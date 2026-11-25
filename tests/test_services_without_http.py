"""Use cases and rules run with no web server and no HTTP client.
This is the 'separated layers' check from the lab."""
import logging

import pytest

from app.domain.course import Course
from app.errors import Conflict, NotFound, ValidationFailed
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.student_repository import StudentRepository
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService
from app.services.student_service import StudentService


@pytest.fixture
def world():
    students, courses, enrollments = StudentRepository(), CourseRepository(), EnrollmentRepository()
    return {
        "students": StudentService(students, enrollments),
        "courses": CourseService(courses, enrollments, max_seats=10),
        "enrollments": EnrollmentService(students, courses, enrollments),
        "repos": (students, courses, enrollments),
    }


# ---- domain rules -------------------------------------------------------
def test_course_reserve_and_release():
    c = Course(code="CSE1101", title="T", seats=1)
    c.reserve_seat()
    assert (c.enrolled, c.available_seats) == (1, 0)
    with pytest.raises(Conflict):
        c.reserve_seat()
    c.release_seat()
    assert c.available_seats == 1


def test_release_never_goes_negative():
    c = Course(code="CSE1101", title="T", seats=1)
    c.release_seat()
    assert c.enrolled == 0


def test_change_seats_rule():
    c = Course(code="CSE1101", title="T", seats=5, enrolled=3)
    with pytest.raises(Conflict):
        c.change_seats(2)
    c.change_seats(3)
    assert c.seats == 3


# ---- services -----------------------------------------------------------
def test_enroll_use_case_end_to_end(world):
    s = world["students"].create_student("A", "a@b.co")
    c = world["courses"].create_course("CSE1101", "T", 1)
    world["enrollments"].enroll(s.id, c.id)

    assert world["courses"].get_course(c.id).available_seats == 0
    other = world["students"].create_student("B", "b@b.co")
    with pytest.raises(Conflict, match="No seats left"):
        world["enrollments"].enroll(other.id, c.id)


def test_enroll_checks_existence_first(world):
    with pytest.raises(NotFound):
        world["enrollments"].enroll(1, 1)


def test_failed_enrollment_does_not_change_state(world):
    s = world["students"].create_student("A", "a@b.co")
    c = world["courses"].create_course("CSE1101", "T", 1)
    world["enrollments"].enroll(s.id, c.id)
    with pytest.raises(Conflict):
        world["enrollments"].enroll(s.id, c.id)  # duplicate
    assert world["courses"].get_course(c.id).enrolled == 1
    assert len(world["enrollments"].list_enrollments()) == 1


def test_max_seats_is_injected_configuration(world):
    with pytest.raises(ValidationFailed) as err:
        world["courses"].create_course("CSE1101", "T", 11)
    assert err.value.errors == [{"field": "seats", "message": "must be at most 10"}]


def test_drop_releases_seat(world):
    s = world["students"].create_student("A", "a@b.co")
    c = world["courses"].create_course("CSE1101", "T", 1)
    e = world["enrollments"].enroll(s.id, c.id)
    world["enrollments"].drop(e.id)
    assert world["courses"].get_course(c.id).available_seats == 1
    with pytest.raises(NotFound):
        world["enrollments"].get_enrollment(e.id)


def test_services_log_events(world, caplog):
    caplog.set_level(logging.INFO, logger="app")
    s = world["students"].create_student("A", "a@b.co")
    c = world["courses"].create_course("CSE1101", "T", 2)
    world["enrollments"].enroll(s.id, c.id)
    assert any("student enrolled" in m and "remaining=1" in m for m in caplog.messages)


# ---- repositories (the only storage code) -------------------------------
def test_repository_returns_copies_so_changes_need_save():
    repo = CourseRepository()
    course = repo.add(Course(code="CSE1101", title="T", seats=5))
    fetched = repo.get(course.id)
    fetched.title = "Changed but not saved"
    assert repo.get(course.id).title == "T"
    repo.save(fetched)
    assert repo.get(course.id).title == "Changed but not saved"


def test_services_work_with_a_fake_repository():
    """Dependency injection: the service never creates its own repository."""
    class FakeEnrollments:
        def count_for_student(self, student_id):
            return 1  # pretend the student has enrollments

    students = StudentRepository()
    service = StudentService(students, FakeEnrollments())
    s = service.create_student("A", "a@b.co")
    with pytest.raises(Conflict):
        service.delete_student(s.id)
