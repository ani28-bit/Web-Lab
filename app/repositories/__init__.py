from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.student_repository import StudentRepository


def build_repositories():
    """The one place that chooses the storage implementation.
    To move to a database, edit files in this package only."""
    return StudentRepository(), CourseRepository(), EnrollmentRepository()
