from app.repositories._memory import MemoryTable


class CourseRepository(MemoryTable):
    def find_by_code(self, code):
        return next((c for c in self.all() if c.code == code), None)

    def list(self, only_available=False):
        courses = self.all()
        if only_available:
            courses = [c for c in courses if c.available_seats > 0]
        return courses
