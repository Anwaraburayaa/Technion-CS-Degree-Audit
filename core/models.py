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

    Requirement data uses these members to identify what kind of rule applies
    to a course. The enum prevents typos and inconsistent spelling that could
    occur with plain strings, while each string value remains suitable for
    configuration files and other external data.

    Each enum member identifies the type of requirement that a course may
    satisfy.  The value of each member is the stable, machine-readable name
    used by configuration files and other parts of the audit system.

    Members:
        MANDATORY_FIXED: A specific compulsory course that must be completed.
        DIGITAL_SYSTEMS: A requirement covering digital-systems coursework.
        COMPILATION_OR_ARCHITECTURE: A requirement satisfied by compilation or
            computer-architecture coursework.
        EXTRA_MATH: Additional mathematics required beyond the core program.
        SCIENCE: A general science requirement.
        SCIENCE_CHAIN: A science requirement in which courses form a defined
            sequence or prerequisite chain.
        LIST_A: A course selected from the approved List A alternatives.
        LIST_B: A course selected from the approved List B alternatives.
        LIST_A_PLUS_B: A requirement that may be fulfilled using courses from
            the combined List A and List B alternatives.
        SPORT: A physical-education or sports requirement.
        MALAG: A requirement associated with the MALAG category or rules.
        FREE_OTHER: Free-choice coursework that does not belong to another
            specific requirement category.
        GENERAL: General coursework or requirements not otherwise classified.
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
