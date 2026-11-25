"""One place that turns every failure into an RFC 9457 problem response."""
import logging

from flask import g, jsonify
from werkzeug.exceptions import HTTPException

from app.errors import AppError

log = logging.getLogger(__name__)


def problem(status, title, detail, code, errors=None):
    body = {
        "type": "/problems/" + code.replace("_", "-"),
        "title": title,
        "status": status,
        "detail": detail,
        "requestId": getattr(g, "request_id", None),
    }
    if errors:
        body["errors"] = errors
    response = jsonify(body)
    response.status_code = status
    response.mimetype = "application/problem+json"
    return response


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return problem(e.status, e.title, e.detail, e.code, e.errors)

    @app.errorhandler(HTTPException)
    def handle_http_error(e):  # unknown URL, wrong method, body too large...
        return problem(e.code, e.name, e.description, e.name.lower().replace(" ", "_"))

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        log.exception("unhandled error")  # full stack trace goes to the log only
        return problem(500, "Internal server error", "Something went wrong", "internal_error")
