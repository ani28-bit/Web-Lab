from flask import Blueprint, current_app, jsonify, request

from app.routes.helpers import created, json_body, no_content
from app.schemas import parse_course

bp = Blueprint("courses", __name__, url_prefix="/courses")


def _service():
    return current_app.extensions["course_service"]


def _view(c):
    return {
        "id": c.id, "code": c.code, "title": c.title,
        "seats": c.seats, "enrolled": c.enrolled, "availableSeats": c.available_seats,
    }


@bp.post("")
def create_course():
    data = parse_course(json_body())
    course = _service().create_course(**data)
    return created(_view(course), "courses.get_course", course_id=course.id)


@bp.get("")
def list_courses():
    only_available = request.args.get("available", "").lower() == "true"
    items = [_view(c) for c in _service().list_courses(only_available)]
    return jsonify({"items": items, "count": len(items)})


@bp.get("/<int:course_id>")
def get_course(course_id):
    return jsonify(_view(_service().get_course(course_id)))


@bp.put("/<int:course_id>")
def update_course(course_id):
    data = parse_course(json_body())
    return jsonify(_view(_service().update_course(course_id, **data)))


@bp.delete("/<int:course_id>")
def delete_course(course_id):
    _service().delete_course(course_id)
    return no_content()
