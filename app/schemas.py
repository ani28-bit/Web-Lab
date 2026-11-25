"""Turns untrusted request data into clean values, or raises ValidationFailed
with field-level messages. Only listed fields are read, so extra fields such
as "id" or "isAdmin" are ignored (protection against mass assignment)."""
import re

from app.errors import ValidationFailed

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_COURSE_CODE = re.compile(r"^[A-Z]{2,5}\d{3,4}[A-Z]?$")


class _Fields:
    def __init__(self, payload):
        if not isinstance(payload, dict):
            raise ValidationFailed(
                "Request body must be a JSON object",
                [{"field": "body", "message": "must be a JSON object (send Content-Type: application/json)"}],
            )
        self.payload = payload
        self.clean = {}
        self.errors = []

    def _fail(self, field, message):
        self.errors.append({"field": field, "message": message})

    def text(self, field, max_len, pattern=None, pattern_message=None, transform=None):
        value = self.payload.get(field)
        if value is None:
            return self._fail(field, "is required")
        if not isinstance(value, str):
            return self._fail(field, "must be a string")
        value = value.strip()
        if transform:
            value = transform(value)
        if not value:
            return self._fail(field, "must not be empty")
        if len(value) > max_len:
            return self._fail(field, f"must be at most {max_len} characters")
        if pattern and not pattern.match(value):
            return self._fail(field, pattern_message)
        self.clean[field] = value

    def integer(self, field, minimum, source=None):
        source = self.payload if source is None else source
        value = source.get(field)
        if value is None:
            return self._fail(field, "is required")
        if isinstance(value, bool) or not isinstance(value, int):
            return self._fail(field, "must be an integer")
        if value < minimum:
            return self._fail(field, f"must be at least {minimum}")
        self.clean[field] = value

    def done(self):
        if self.errors:
            raise ValidationFailed("One or more fields are invalid", self.errors)
        return self.clean


def parse_student(payload):
    f = _Fields(payload)
    f.text("name", 100)
    f.text("email", 254, _EMAIL, "must be a valid email address", transform=str.lower)
    return f.done()


def parse_course(payload):
    f = _Fields(payload)
    f.text("code", 10, _COURSE_CODE, "must look like CSE3102 or CSE3102L", transform=str.upper)
    f.text("title", 120)
    f.integer("seats", 1)
    return f.done()


def parse_enrollment(payload):
    f = _Fields(payload)
    f.integer("student_id", 1, {"student_id": _get(payload, "studentId")})
    f.integer("course_id", 1, {"course_id": _get(payload, "courseId")})
    # report errors under the names the client actually sent
    for e in f.errors:
        e["field"] = {"student_id": "studentId", "course_id": "courseId"}.get(e["field"], e["field"])
    return f.done()


def _get(payload, key):
    return payload.get(key) if isinstance(payload, dict) else None


def parse_enrollment_filters(args):
    """Optional ?studentId= and ?courseId= query parameters."""
    errors, clean = [], {}
    for query_name, key in (("studentId", "student_id"), ("courseId", "course_id")):
        raw = args.get(query_name)
        if raw is None:
            continue
        if not raw.isdigit() or int(raw) < 1:
            errors.append({"field": query_name, "message": "must be a positive integer"})
        else:
            clean[key] = int(raw)
    if errors:
        raise ValidationFailed("One or more query parameters are invalid", errors)
    return clean
