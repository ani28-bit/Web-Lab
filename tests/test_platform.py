"""Cross-cutting behaviour: request IDs, logging, error handling, headers."""
import logging

from tests.conftest import assert_problem


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_every_response_has_a_request_id_and_nosniff(client):
    r = client.get("/health")
    assert len(r.headers["X-Request-ID"]) == 12
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_client_supplied_request_id_is_reused(client):
    r = client.get("/students/1", headers={"X-Request-ID": "trace-abc-123"})
    assert r.headers["X-Request-ID"] == "trace-abc-123"
    assert r.json["requestId"] == "trace-abc-123"


import pytest


@pytest.mark.parametrize("unsafe", ["bad id INFO fake log line", "<script>alert(1)</script>", "x" * 65])
def test_unsafe_request_id_is_replaced(client, unsafe):
    r = client.get("/health", headers={"X-Request-ID": unsafe})
    assert r.headers["X-Request-ID"] != unsafe
    assert len(r.headers["X-Request-ID"]) == 12


def test_request_log_line_has_method_path_status_and_id(client, caplog):
    caplog.set_level(logging.INFO, logger="app")
    r = client.get("/students/5")
    line = next(m for m in caplog.messages if m.startswith("GET /students/5"))
    assert line == f"GET /students/5 -> 404 [{r.headers['X-Request-ID']}]"


def test_service_events_are_logged_without_personal_data(client, caplog):
    caplog.set_level(logging.INFO, logger="app")
    client.post("/students", json={"name": "Secret Name", "email": "secret@example.com"})
    text = "\n".join(caplog.messages)
    assert "student created id=1" in text
    assert "Secret Name" not in text and "secret@example.com" not in text


def test_unknown_route_uses_problem_format(client):
    assert_problem(client.get("/nope"), 404, "not-found")


def test_wrong_method_uses_problem_format(client):
    assert_problem(client.patch("/students"), 405, "method-not-allowed")


def test_trailing_slash_is_accepted(client):
    assert client.get("/students/").status_code == 200


def test_oversized_body_is_rejected_with_413():
    from app import create_app
    app = create_app({"APP_ENV": "test", "LOG_LEVEL": "WARNING", "MAX_BODY_BYTES": "100"})
    r = app.test_client().post("/students", json={"name": "x" * 500, "email": "a@b.co"})
    assert_problem(r, 413, "request-entity-too-large")


def test_unexpected_error_is_hidden_from_client_but_logged_in_full(app, client, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("db password=hunter2")
    monkeypatch.setattr(app.extensions["course_service"], "list_courses", boom)

    r = client.get("/courses")
    body = assert_problem(r, 500, "internal-error")
    assert body["detail"] == "Something went wrong"
    assert "hunter2" not in r.get_data(as_text=True)
    assert "Traceback" not in r.get_data(as_text=True)

    record = next(rec for rec in caplog.records if rec.getMessage() == "unhandled error")
    assert record.exc_info and "hunter2" in str(record.exc_info[1])  # full detail kept in the log
