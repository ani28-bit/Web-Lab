import logging

from app.domain.course import Course
from app.errors import Conflict, NotFound, ValidationFailed

log = logging.getLogger(__name__)


class CourseService:
    def __init__(self, courses, enrollments, max_seats):
        self.courses = courses
        self.enrollments = enrollments
        self.max_seats = max_seats

    def create_course(self, code, title, seats):
        self._check_seats(seats)
        self._ensure_code_free(code)
        course = self.courses.add(Course(code=code, title=title, seats=seats))
        log.info("course created id=%s code=%s seats=%s", course.id, code, seats)
        return course

    def get_course(self, course_id):
        course = self.courses.get(course_id)
        if course is None:
            raise NotFound(f"Course {course_id} does not exist")
        return course

    def list_courses(self, only_available=False):
        return self.courses.list(only_available=only_available)

    def update_course(self, course_id, code, title, seats):
        course = self.get_course(course_id)
        self._check_seats(seats)
        self._ensure_code_free(code, ignore_id=course_id)
        course.change_seats(seats)  # domain rule: not below enrolled
        course.code, course.title = code, title
        self.courses.save(course)
        log.info("course updated id=%s seats=%s", course_id, seats)
        return course

    def delete_course(self, course_id):
        self.get_course(course_id)
        if self.enrollments.count_for_course(course_id) > 0:
            raise Conflict("Course has enrolled students; drop them first")
        self.courses.delete(course_id)
        log.info("course deleted id=%s", course_id)

    def _check_seats(self, seats):
        if seats > self.max_seats:
            raise ValidationFailed(
                "One or more fields are invalid",
                [{"field": "seats", "message": f"must be at most {self.max_seats}"}],
            )

    def _ensure_code_free(self, code, ignore_id=None):
        existing = self.courses.find_by_code(code)
        if existing and existing.id != ignore_id:
            raise Conflict(f"A course with code {code} already exists")
