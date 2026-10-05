"""Shared data models used throughout the degree-audit project.

Other modules load course data and degree requirements, then use the types in
this file while checking whether a student's completed courses satisfy those
requirements. Keeping these definitions in one place gives every module the
same representation and avoids duplicated, inconsistent data structures.
"""

from dataclasses import dataclass
from enum import Enum

class Category(Enum):
    """Categories used to classify degree requirements.

    Each member names one rule of the degree. Its value is the "key" of that rule
    in data/requirements.json. The enum prevents typos and inconsistent spelling that could
    occur with plain strings, while each string value remains suitable for
    configuration files and other external data.

    Each enum member identifies one requirement that the student must
    satisfy.  The value of each member is the stable, machine-readable name
    used by configuration files and other parts of the audit system.

    Members:
        MANDATORY_FIXED: The 18 fixed mandatory courses; all are required.
        DIGITAL_SYSTEMS: 00440252 or 02340252; one is required.
        COMPILATION_OR_ARCHITECTURE: 02360360 or 02360267; one is required.
        EXTRA_MATH: Additional mathematics required beyond the core program.
        SCIENCE: At least 8 points from the science course list.
        SCIENCE_CHAIN: One complete science chain (every course of one option).
        LIST_A: At least 18 points from the List A courses.
        LIST_B: Points from the List B courses; no minimum of its own.
        LIST_A_PLUS_B: List A and List B points together; at least 24.5.
        SPORT: A physical-education or sports requirement.
        MALAG: Malag points typed by the student; at least 6.
        FREE_OTHER: Other free-elective points typed by the student; no minimum.
        GENERAL: SPORT + MALAG + FREE_OTHER together; at least 10 points.
        ENGLISH_TAUGHT: A requirement concerning courses taught in English.
    """

    MANDATORY_FIXED = "mandatory_fixed"
    DIGITAL_SYSTEMS = "digital_systems"
    COMPILATION_OR_ARCHITECTURE = "compilation_or_architecture"
    EXTRA_MATH = "extra_math"
    SCIENCE = "science"
    SCIENCE_CHAIN = "science_chain"
    LIST_A = "list_a"
    LIST_B = "list_b"
    LIST_A_PLUS_B = "list_a_plus_b"
    SPORT = "sport"
    MALAG = "malag"
    FREE_OTHER = "free_other"
    GENERAL = "general"
    ENGLISH_TAUGHT = "english_taught"

@dataclass(frozen=True)
class Course:
    """Immutable representation of one course from the course database.

    Course objects are created from the course database and passed to the
    audit logic, which matches them against degree requirements. This class
    stores course information only; the rules for deciding whether a course
    satisfies a requirement belong in the audit logic.

    Attributes:
        id: The course identifier, normally an eight-digit string. It remains
            a string so leading zeroes are preserved.
        name_he: The course name in Hebrew.
        name_en: The course name in English.
        credits: The number of academic credits assigned to the course.

    ``frozen=True`` prevents accidental mutation after a course is loaded,
    allowing instances to be safely shared by the audit logic.
    """

    id: str
    name_he: str
    name_en: str
    credits: float
