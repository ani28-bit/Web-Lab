from flask import Flask, jsonify

from app.config import Config
from app.error_handlers import register_error_handlers
from app.logging_config import configure_logging
from app.middleware import register_request_hooks
from app.repositories import build_repositories
from app.routes import courses, enrollments, students
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService
from app.services.student_service import StudentService


def create_app(overrides=None):
    """Composition root: the only place that builds and connects objects."""
    config = Config(overrides)
    configure_logging(config.LOG_LEVEL)

    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_BODY_BYTES
    app.json.sort_keys = False
    app.extensions["config"] = config

    student_repo, course_repo, enrollment_repo = build_repositories()
    app.extensions["student_service"] = StudentService(student_repo, enrollment_repo)
    app.extensions["course_service"] = CourseService(course_repo, enrollment_repo, config.MAX_SEATS)
    app.extensions["enrollment_service"] = EnrollmentService(student_repo, course_repo, enrollment_repo)

    register_request_hooks(app)
    register_error_handlers(app)
    for module in (students, courses, enrollments):
        app.register_blueprint(module.bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "env": config.APP_ENV})

    return app
