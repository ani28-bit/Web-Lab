import pytest

from tests.conftest import assert_problem


def test_create_course_returns_201_location_and_body(client):
    r = client.post("/courses", json={"code": "CSE3102L", "title": "Web Lab", "seats": 30})
    assert r.status_code == 201
    assert r.headers["Location"] == "/courses/1"
    assert r.json == {"id": 1, "code": "CSE3102L", "title": "Web Lab",
                      "seats": 30, "enrolled": 0, "availableSeats": 30}


def test_course_code_is_uppercased(client):
    r = client.post("/courses", json={"code": "cse3102l", "title": "Web Lab", "seats": 5})
    assert r.json["code"] == "CSE3102L"


@pytest.mark.parametrize("payload, bad_field", [
    ({"code": "CSE3102", "title": "T", "seats": 0}, "seats"),
    ({"code": "CSE3102", "title": "T", "seats": -3}, "seats"),
    ({"code": "CSE3102", "title": "T", "seats": "5"}, "seats"),
    ({"code": "CSE3102", "title": "T", "seats": True}, "seats"),
    ({"code": "CSE3102", "title": "T", "seats": 5.5}, "seats"),
    ({"code": "CSE3102", "title": "T"}, "seats"),
    ({"code": "3102CSE", "title": "T", "seats": 5}, "code"),
    ({"code": "", "title": "T", "seats": 5}, "code"),
    ({"code": "CSE3102", "title": " ", "seats": 5}, "title"),
    ({"code": "CSE3102", "title": "T" * 121, "seats": 5}, "title"),
])
def test_invalid_course_payloads_name_the_bad_field(client, payload, bad_field):
    body = assert_problem(client.post("/courses", json=payload), 422, "validation-failed")
    assert bad_field in {e["field"] for e in body["errors"]}


def test_seats_above_configured_maximum_is_rejected(client):
    r = client.post("/courses", json={"code": "CSE3102", "title": "T", "seats": 51})  # MAX_SEATS=50
    body = assert_problem(r, 422, "validation-failed")
    assert body["errors"] == [{"field": "seats", "message": "must be at most 50"}]


def test_duplicate_course_code_conflicts(client, make_course):
    make_course(code="CSE3102L")
    r = client.post("/courses", json={"code": "cse3102l", "title": "Again", "seats": 5})
    assert_problem(r, 409, "conflict")


def test_get_and_list_courses(client, make_course):
    c = make_course()
    assert client.get(f"/courses/{c['id']}").json == c
    assert client.get("/courses").json == {"items": [c], "count": 1}
    assert_problem(client.get("/courses/99"), 404, "not-found")


def test_list_only_available_courses(client, make_course, make_student, enroll):
    full = make_course(code="CSE1101", seats=1)
    open_ = make_course(code="CSE1102", seats=1)
    s = make_student()
    enroll(s["id"], full["id"])
    codes = [c["code"] for c in client.get("/courses?available=true").json["items"]]
    assert codes == [open_["code"]]
    assert client.get("/courses").json["count"] == 2


def test_update_course(client, make_course):
    c = make_course(seats=2)
    r = client.put(f"/courses/{c['id']}", json={"code": "CSE3103", "title": "Renamed", "seats": 10})
    assert r.status_code == 200
    assert (r.json["code"], r.json["title"], r.json["seats"], r.json["availableSeats"]) == ("CSE3103", "Renamed", 10, 10)


def test_cannot_shrink_seats_below_enrolled(client, make_course, make_student, enroll):
    c = make_course(seats=3)
    for i in range(2):
        enroll(make_student(email=f"s{i}@b.co")["id"], c["id"])
    r = client.put(f"/courses/{c['id']}", json={"code": c["code"], "title": c["title"], "seats": 1})
    assert_problem(r, 409, "conflict")
    assert client.get(f"/courses/{c['id']}").json["seats"] == 3  # unchanged


def test_update_to_another_courses_code_conflicts(client, make_course):
    make_course(code="CSE1101")
    b = make_course(code="CSE1102")
    r = client.put(f"/courses/{b['id']}", json={"code": "CSE1101", "title": "T", "seats": 5})
    assert_problem(r, 409, "conflict")


def test_update_unknown_course_is_404(client):
    assert_problem(client.put("/courses/9", json={"code": "CSE1101", "title": "T", "seats": 5}), 404, "not-found")


def test_delete_course(client, make_course):
    c = make_course()
    assert client.delete(f"/courses/{c['id']}").status_code == 204
    assert_problem(client.get(f"/courses/{c['id']}"), 404, "not-found")
    assert_problem(client.delete(f"/courses/{c['id']}"), 404, "not-found")


def test_cannot_delete_course_with_students(client, make_course, make_student, enroll):
    c, s = make_course(), make_student()
    enroll(s["id"], c["id"])
    assert_problem(client.delete(f"/courses/{c['id']}"), 409, "conflict")
