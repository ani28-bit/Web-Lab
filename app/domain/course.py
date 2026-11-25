from dataclasses import dataclass

from app.errors import Conflict


@dataclass
class Course:
    code: str
    title: str
    seats: int
    enrolled: int = 0
    id: int | None = None

    @property
    def available_seats(self) -> int:
        return self.seats - self.enrolled

    def reserve_seat(self) -> None:
        """Business rule: a full course cannot take another student."""
        if self.enrolled >= self.seats:
            raise Conflict(f"No seats left in course {self.code}")
        self.enrolled += 1

    def release_seat(self) -> None:
        if self.enrolled > 0:
            self.enrolled -= 1

    def change_seats(self, new_seats: int) -> None:
        """Business rule: capacity cannot drop below students already enrolled."""
        if new_seats < self.enrolled:
            raise Conflict(
                f"Cannot set seats to {new_seats}: {self.enrolled} students are already enrolled"
            )
        self.seats = new_seats
