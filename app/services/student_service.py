import logging

from app.domain.student import Student
from app.errors import Conflict, NotFound

log = logging.getLogger(__name__)


class StudentService:
    def __init__(self, students, enrollments):
        self.students = students
        self.enrollments = enrollments

    def create_student(self, name, email):
        self._ensure_email_free(email)
        student = self.students.add(Student(name=name, email=email))
        log.info("student created id=%s", student.id)
        return student

    def get_student(self, student_id):
        student = self.students.get(student_id)
        if student is None:
            raise NotFound(f"Student {student_id} does not exist")
        return student

    def list_students(self):
        return self.students.list()

    def update_student(self, student_id, name, email):
        student = self.get_student(student_id)
        self._ensure_email_free(email, ignore_id=student_id)
        student.name, student.email = name, email
        self.students.save(student)
        log.info("student updated id=%s", student_id)
        return student

    def delete_student(self, student_id):
        self.get_student(student_id)
        if self.enrollments.count_for_student(student_id) > 0:
            raise Conflict("Student has active enrollments; drop them first")
        self.students.delete(student_id)
        log.info("student deleted id=%s", student_id)

    def _ensure_email_free(self, email, ignore_id=None):
        existing = self.students.find_by_email(email)
        if existing and existing.id != ignore_id:
            raise Conflict(f"A student with email {email} already exists")
