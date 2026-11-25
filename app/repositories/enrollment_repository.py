from app.repositories._memory import MemoryTable


class EnrollmentRepository(MemoryTable):
    def list(self, student_id=None, course_id=None):
        rows = self.all()
        if student_id is not None:
            rows = [e for e in rows if e.student_id == student_id]
        if course_id is not None:
            rows = [e for e in rows if e.course_id == course_id]
        return rows

    def exists(self, student_id, course_id):
        return bool(self.list(student_id, course_id))

    def count_for_student(self, student_id):
        return len(self.list(student_id=student_id))

    def count_for_course(self, course_id):
        return len(self.list(course_id=course_id))
