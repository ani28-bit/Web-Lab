import pytest

from tests.conftest import assert_problem


def test_create_student_returns_201_location_and_body(client):
    r = client.post("/students", json={"name": "Rahim", "email": "rahim@example.com"})
    assert r.status_code == 201
    assert r.headers["Location"] == "/students/1"
    assert r.json == {"id": 1, "name": "Rahim", "email": "rahim@example.com"}


def test_email_is_normalised_to_lowercase(client):
    r = client.post("/students", json={"name": "Rahim", "email": "  Rahim@Example.COM "})
    assert r.json["email"] == "rahim@example.com"


def test_extra_fields_are_ignored_not_mass_assigned(client):
    r = client.post("/students", json={"id": 99, "isAdmin": True, "name": "X", "email": "x@x.io"})
    assert r.status_code == 201
    assert r.json == {"id": 1, "name": "X", "email": "x@x.io"}


def test_validation_errors_are_reported_per_field(client):
    r = client.post("/students", json={"name": "  ", "email": "not-an-email"})
    body = assert_problem(r, 422, "validation-failed")
    fields = {e["field"]: e["message"] for e in body["errors"]}
    assert fields == {"name": "must not be empty", "email": "must be a valid email address"}


@pytest.mark.parametrize("payload", [
    {}, {"name": "A"}, {"email": "a@b.co"}, {"name": 5, "email": "a@b.co"},
    {"name": "A", "email": ["a@b.co"]}, {"name": "A" * 101, "email": "a@b.co"},
])
def test_invalid_student_payloads_are_rejected(client, payload):
    assert_problem(client.post("/students", json=payload), 422, "validation-failed")


@pytest.mark.parametrize("body", [[1, 2], "text", 5, None])
def test_body_must_be_a_json_object(client, body):
    assert_problem(client.post("/students", json=body), 422, "validation-failed")


def test_non_json_content_type_is_rejected(client):
    r = client.post("/students", data="name=A", content_type="application/x-www-form-urlencoded")
    assert_problem(r, 422, "validation-failed")


def test_malformed_json_is_rejected(client):
    r = client.post("/students", data="{broken", content_type="application/json")
    assert_problem(r, 422, "validation-failed")


def test_duplicate_email_conflicts(client, make_student):
    make_student(email="a@b.co")
    r = client.post("/students", json={"name": "Other", "email": "A@B.co"})
    assert_problem(r, 409, "conflict")


def test_get_student(client, make_student):
    s = make_student()
    r = client.get(f"/students/{s['id']}")
    assert r.status_code == 200 and r.json == s


def test_get_unknown_student_is_404(client):
    assert_problem(client.get("/students/42"), 404, "not-found")


def test_non_numeric_id_is_404(client):
    assert_problem(client.get("/students/abc"), 404, "not-found")


def test_list_students(client, make_student):
    assert client.get("/students").json == {"items": [], "count": 0}
    make_student(email="a@b.co")
    make_student(name="Karim", email="k@b.co")
    body = client.get("/students").json
    assert body["count"] == 2
    assert [s["id"] for s in body["items"]] == [1, 2]


def test_update_student(client, make_student):
    s = make_student()
    r = client.put(f"/students/{s['id']}", json={"name": "New Name", "email": "new@b.co"})
    assert r.status_code == 200
    assert r.json == {"id": s["id"], "name": "New Name", "email": "new@b.co"}
    assert client.get(f"/students/{s['id']}").json["name"] == "New Name"


def test_update_may_keep_own_email(client, make_student):
    s = make_student(email="keep@b.co")
    r = client.put(f"/students/{s['id']}", json={"name": "Renamed", "email": "keep@b.co"})
    assert r.status_code == 200


def test_update_to_someone_elses_email_conflicts(client, make_student):
    make_student(email="a@b.co")
    other = make_student(name="B", email="b@b.co")
    r = client.put(f"/students/{other['id']}", json={"name": "B", "email": "a@b.co"})
    assert_problem(r, 409, "conflict")


def test_update_validates_and_checks_existence(client, make_student):
    s = make_student()
    assert_problem(client.put(f"/students/{s['id']}", json={"name": ""}), 422, "validation-failed")
    assert_problem(client.put("/students/99", json={"name": "A", "email": "a@b.co"}), 404, "not-found")


def test_delete_student(client, make_student):
    s = make_student()
    r = client.delete(f"/students/{s['id']}")
    assert r.status_code == 204 and r.data == b""
    assert_problem(client.get(f"/students/{s['id']}"), 404, "not-found")


def test_delete_unknown_student_is_404(client):
    assert_problem(client.delete("/students/7"), 404, "not-found")


def test_cannot_delete_student_with_enrollments(client, make_student, make_course, enroll):
    s, c = make_student(), make_course()
    enroll(s["id"], c["id"])
    assert_problem(client.delete(f"/students/{s['id']}"), 409, "conflict")
