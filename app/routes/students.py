from flask import Blueprint, current_app, jsonify

from app.routes.helpers import created, json_body, no_content
from app.schemas import parse_student

bp = Blueprint("students", __name__, url_prefix="/students")


def _service():
    return current_app.extensions["student_service"]


def _view(s):
    return {"id": s.id, "name": s.name, "email": s.email}


@bp.post("")
def create_student():
    data = parse_student(json_body())
    student = _service().create_student(**data)
    return created(_view(student), "students.get_student", student_id=student.id)


@bp.get("")
def list_students():
    items = [_view(s) for s in _service().list_students()]
    return jsonify({"items": items, "count": len(items)})


@bp.get("/<int:student_id>")
def get_student(student_id):
    return jsonify(_view(_service().get_student(student_id)))


@bp.put("/<int:student_id>")
def update_student(student_id):
    data = parse_student(json_body())
    return jsonify(_view(_service().update_student(student_id, **data)))


@bp.delete("/<int:student_id>")
def delete_student(student_id):
    _service().delete_student(student_id)
    return no_content()
