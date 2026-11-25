from flask import Blueprint, current_app, jsonify, request

from app.routes.helpers import created, json_body, no_content
from app.schemas import parse_enrollment, parse_enrollment_filters

bp = Blueprint("enrollments", __name__, url_prefix="/enrollments")


def _service():
    return current_app.extensions["enrollment_service"]


def _view(e):
    return {"id": e.id, "studentId": e.student_id, "courseId": e.course_id}


@bp.post("")
def enroll():
    data = parse_enrollment(json_body())
    enrollment = _service().enroll(data["student_id"], data["course_id"])
    return created(_view(enrollment), "enrollments.get_enrollment", enrollment_id=enrollment.id)


@bp.get("")
def list_enrollments():
    filters = parse_enrollment_filters(request.args)
    items = [_view(e) for e in _service().list_enrollments(**filters)]
    return jsonify({"items": items, "count": len(items)})


@bp.get("/<int:enrollment_id>")
def get_enrollment(enrollment_id):
    return jsonify(_view(_service().get_enrollment(enrollment_id)))


@bp.delete("/<int:enrollment_id>")
def drop_enrollment(enrollment_id):
    _service().drop(enrollment_id)
    return no_content()
