"""One scripted run through the whole API, the same steps you would click
through in a Postman collection, but checked automatically."""
from tests.conftest import assert_problem


def test_full_lifecycle_of_every_resource(client):
    # 1. create a student and a course (2 seats)
    s1 = client.post("/students", json={"name": "Rahim", "email": "rahim@example.com"})
    s2 = client.post("/students", json={"name": "Karim", "email": "karim@example.com"})
    s3 = client.post("/students", json={"name": "Salma", "email": "salma@example.com"})
    course = client.post("/courses", json={"code": "CSE3102L", "title": "Web Lab", "seats": 2})
    assert [r.status_code for r in (s1, s2, s3, course)] == [201, 201, 201, 201]
    sid1, sid2, sid3, cid = s1.json["id"], s2.json["id"], s3.json["id"], course.json["id"]

    # 2. read and list
    assert client.get(f"/students/{sid1}").json["email"] == "rahim@example.com"
    assert client.get("/students").json["count"] == 3
    assert client.get("/courses").json["count"] == 1

    # 3. update
    r = client.put(f"/students/{sid1}", json={"name": "Rahim Uddin", "email": "rahim@example.com"})
    assert r.json["name"] == "Rahim Uddin"

    # 4. enroll until the course is full, then hit the failing rule
    e1 = client.post("/enrollments", json={"studentId": sid1, "courseId": cid})
    e2 = client.post("/enrollments", json={"studentId": sid2, "courseId": cid})
    assert (e1.status_code, e2.status_code) == (201, 201)
    assert client.get(f"/courses/{cid}").json["availableSeats"] == 0
    assert_problem(client.post("/enrollments", json={"studentId": sid3, "courseId": cid}), 409, "conflict")
    assert client.get("/courses?available=true").json["count"] == 0

    # 5. protected deletes while enrollments exist
    assert_problem(client.delete(f"/students/{sid1}"), 409, "conflict")
    assert_problem(client.delete(f"/courses/{cid}"), 409, "conflict")

    # 6. drop one enrollment, the waiting student gets the seat
    assert client.delete(f"/enrollments/{e1.json['id']}").status_code == 204
    assert client.post("/enrollments", json={"studentId": sid3, "courseId": cid}).status_code == 201

    # 7. clean everything up in a legal order
    for e in client.get("/enrollments").json["items"]:
        assert client.delete(f"/enrollments/{e['id']}").status_code == 204
    for sid in (sid1, sid2, sid3):
        assert client.delete(f"/students/{sid}").status_code == 204
    assert client.delete(f"/courses/{cid}").status_code == 204

    # 8. nothing is left
    assert client.get("/students").json["count"] == 0
    assert client.get("/courses").json["count"] == 0
    assert client.get("/enrollments").json["count"] == 0
