"""Request ID, access log and basic response headers."""
import logging
import re
import uuid

from flask import g, request

_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
http_log = logging.getLogger("app.http")


def register_request_hooks(app):
    @app.before_request
    def assign_request_id():
        supplied = request.headers.get("X-Request-ID", "")
        # Only accept simple IDs: stops log injection through this header.
        g.request_id = supplied if _SAFE_REQUEST_ID.match(supplied) else uuid.uuid4().hex[:12]

    @app.after_request
    def finish_request(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        http_log.info("%s %s -> %s [%s]", request.method, request.path,
                      response.status_code, g.request_id)
        return response
