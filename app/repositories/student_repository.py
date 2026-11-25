from app.repositories._memory import MemoryTable


class StudentRepository(MemoryTable):
    def find_by_email(self, email):
        return next((s for s in self.all() if s.email == email), None)

    def list(self):
        return self.all()
