import logging

from app.domain.enrollment import Enrollment
from app.errors import Conflict, NotFound

log = logging.getLogger(__name__)


class EnrollmentService:
    def __init__(self, students, courses, enrollments):
        self.students = students
        self.courses = courses
        self.enrollments = enrollments

    def enroll(self, student_id, course_id):
        """The use case with rules that can fail: unknown ids, duplicates, full course."""
        if self.students.get(student_id) is None:
            raise NotFound(f"Student {student_id} does not exist")
        course = self.courses.get(course_id)
        if course is None:
            raise NotFound(f"Course {course_id} does not exist")
        if self.enrollments.exists(student_id, course_id):
            raise Conflict("Student is already enrolled in this course")

        course.reserve_seat()  # raises Conflict when full
        self.courses.save(course)
        enrollment = self.enrollments.add(Enrollment(student_id, course_id))
        log.info(
            "student enrolled enrollment=%s student=%s course=%s remaining=%s",
            enrollment.id, student_id, course_id, course.available_seats,
        )
        return enrollment

    def drop(self, enrollment_id):
        enrollment = self.get_enrollment(enrollment_id)
        course = self.courses.get(enrollment.course_id)
        if course is not None:
            course.release_seat()
            self.courses.save(course)
        self.enrollments.delete(enrollment_id)
        log.info("enrollment dropped id=%s", enrollment_id)

    def get_enrollment(self, enrollment_id):
        enrollment = self.enrollments.get(enrollment_id)
        if enrollment is None:
            raise NotFound(f"Enrollment {enrollment_id} does not exist")
        return enrollment

    def list_enrollments(self, student_id=None, course_id=None):
        return self.enrollments.list(student_id=student_id, course_id=course_id)
