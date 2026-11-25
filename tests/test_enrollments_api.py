import pytest

from tests.conftest import assert_problem


def test_enroll_returns_201_and_takes_a_seat(client, make_student, make_course, enroll):
    s, c = make_student(), make_course(seats=2)
    r = enroll(s["id"], c["id"])
    assert r.status_code == 201
    assert r.headers["Location"] == "/enrollments/1"
    assert r.json == {"id": 1, "studentId": s["id"], "courseId": c["id"]}
    course = client.get(f"/courses/{c['id']}").json
    assert (course["enrolled"], course["availableSeats"]) == (1, 1)


def test_full_course_rejects_enrollment_with_409(client, make_student, make_course, enroll):
    c = make_course(seats=1)
    first = make_student(email="a@b.co")
    second = make_student(name="Karim", email="k@b.co")
    assert enroll(first["id"], c["id"]).status_code == 201
    body = assert_problem(enroll(second["id"], c["id"]), 409, "conflict")
    assert "No seats left" in body["detail"]
    assert client.get(f"/courses/{c['id']}").json["enrolled"] == 1  # nothing changed


def test_duplicate_enrollment_conflicts(make_student, make_course, enroll):
    s, c = make_student(), make_course(seats=5)
    enroll(s["id"], c["id"])
    assert_problem(enroll(s["id"], c["id"]), 409, "conflict")


def test_unknown_student_or_course_is_404(make_student, make_course, enroll):
    s, c = make_student(), make_course()
    assert_problem(enroll(999, c["id"]), 404, "not-found")
    assert_problem(enroll(s["id"], 999), 404, "not-found")


@pytest.mark.parametrize("payload, bad_field", [
    ({}, "studentId"),
    ({"studentId": 1}, "courseId"),
    ({"studentId": "1", "courseId": 1}, "studentId"),
    ({"studentId": 1, "courseId": 0}, "courseId"),
    ({"studentId": True, "courseId": 1}, "studentId"),
    ({"studentId": 1.5, "courseId": 1}, "studentId"),
])
def test_invalid_enrollment_payloads(client, payload, bad_field):
    body = assert_problem(client.post("/enrollments", json=payload), 422, "validation-failed")
    assert bad_field in {e["field"] for e in body["errors"]}


def test_get_enrollment(client, make_student, make_course, enroll):
    s, c = make_student(), make_course()
    e = enroll(s["id"], c["id"]).json
    assert client.get(f"/enrollments/{e['id']}").json == e
    assert_problem(client.get("/enrollments/77"), 404, "not-found")


def test_drop_enrollment_frees_the_seat(client, make_student, make_course, enroll):
    c = make_course(seats=1)
    a = make_student(email="a@b.co")
    b = make_student(name="Karim", email="k@b.co")
    e = enroll(a["id"], c["id"]).json
    assert enroll(b["id"], c["id"]).status_code == 409

    assert client.delete(f"/enrollments/{e['id']}").status_code == 204
    assert client.get(f"/courses/{c['id']}").json["availableSeats"] == 1
    assert enroll(b["id"], c["id"]).status_code == 201  # seat is reusable


def test_drop_unknown_enrollment_is_404(client):
    assert_problem(client.delete("/enrollments/5"), 404, "not-found")


def test_list_and_filter_enrollments(client, make_student, make_course, enroll):
    s1, s2 = make_student(email="a@b.co"), make_student(name="K", email="k@b.co")
    c1, c2 = make_course(code="CSE1101", seats=5), make_course(code="CSE1102", seats=5)
    enroll(s1["id"], c1["id"]); enroll(s1["id"], c2["id"]); enroll(s2["id"], c1["id"])

    assert client.get("/enrollments").json["count"] == 3
    assert client.get(f"/enrollments?studentId={s1['id']}").json["count"] == 2
    assert client.get(f"/enrollments?courseId={c1['id']}").json["count"] == 2
    assert client.get(f"/enrollments?studentId={s2['id']}&courseId={c1['id']}").json["count"] == 1
    assert client.get("/enrollments?studentId=999").json == {"items": [], "count": 0}


@pytest.mark.parametrize("query", ["studentId=abc", "courseId=-1", "studentId=0", "courseId=1.5"])
def test_invalid_filters_are_rejected(client, query):
    body = assert_problem(client.get(f"/enrollments?{query}"), 422, "validation-failed")
    assert body["errors"][0]["field"] in {"studentId", "courseId"}
