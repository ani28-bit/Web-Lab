from dataclasses import dataclass


@dataclass
class Student:
    name: str
    email: str
    id: int | None = None
