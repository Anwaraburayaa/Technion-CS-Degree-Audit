from dataclasses import dataclass
from enum import Enum


class Category(Enum):
    pass


@dataclass(frozen=True)
class Course:
    id: str
    name: str
    credits: float
