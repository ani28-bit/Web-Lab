import pytest

from app import create_app


@pytest.fixture
def app():
    # Fresh app (and fresh in-memory data) for every test.
    return create_app({"APP_ENV": "test", "LOG_LEVEL": "WARNING", "MAX_SEATS": "50"})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_student(client):
    def _make(name="Rahim Uddin", email="rahim@example.com"):
        r = client.post("/students", json={"name": name, "email": email})
        assert r.status_code == 201, r.json
        return r.json
    return _make


@pytest.fixture
def make_course(client):
    def _make(code="CSE3102L", title="Web Technology Lab", seats=2):
        r = client.post("/courses", json={"code": code, "title": title, "seats": seats})
        assert r.status_code == 201, r.json
        return r.json
    return _make


@pytest.fixture
def enroll(client):
    def _enroll(student_id, course_id):
        return client.post("/enrollments", json={"studentId": student_id, "courseId": course_id})
    return _enroll


def assert_problem(response, status, code):
    """Every failure must use the same RFC 9457 shape."""
    assert response.status_code == status
    assert response.mimetype == "application/problem+json"
    body = response.json
    assert body["status"] == status
    assert body["type"] == f"/problems/{code}"
    assert body["requestId"] == response.headers["X-Request-ID"]
    assert body["title"] and body["detail"]
    return body
