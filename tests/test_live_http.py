"""Real HTTP over a real socket: starts the server on a free port and talks to
it with urllib, like Postman or curl would. Slowest test, so just one flow."""
import json
import threading
import urllib.error
import urllib.request

import pytest
from werkzeug.serving import make_server

from app import create_app


@pytest.fixture
def base_url():
    app = create_app({"APP_ENV": "test", "LOG_LEVEL": "WARNING"})
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), json.loads(e.read())


def test_enrollment_flow_over_real_http(base_url):
    status, _, student = call("POST", f"{base_url}/students", {"name": "Rahim", "email": "r@b.co"})
    assert status == 201
    status, _, course = call("POST", f"{base_url}/courses", {"code": "CSE3102L", "title": "Web Lab", "seats": 1})
    assert status == 201

    status, headers, enrollment = call("POST", f"{base_url}/enrollments",
                                       {"studentId": student["id"], "courseId": course["id"]})
    assert status == 201 and headers["Location"] == f"/enrollments/{enrollment['id']}"

    status, headers, problem = call("POST", f"{base_url}/enrollments",
                                    {"studentId": student["id"], "courseId": course["id"]})
    assert status == 409
    assert headers["Content-Type"].startswith("application/problem+json")

    assert call("DELETE", f"{base_url}/enrollments/{enrollment['id']}")[0] == 204
    assert call("GET", f"{base_url}/courses/{course['id']}")[2]["availableSeats"] == 1
