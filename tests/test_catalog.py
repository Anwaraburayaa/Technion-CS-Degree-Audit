"""Tests for core/catalog.py (CourseCatalog).

Most tests build a small fake catalog in a temporary folder, so they check the CODE and do not
break when the real course data changes. One test (the last section) loads the real data file.

Run from the project folder with:  pytest -v
"""
import json                                         # to write the fake course file
from pathlib import Path                            # to build file paths that work on any system

import pytest                                       # the test framework (pytest.raises)

from core.catalog import CourseCatalog              # the class under test


# --------------------------------------------------------------------------------------
# Fake data and helper
# --------------------------------------------------------------------------------------

FAKE_COURSES = [                                    # three made-up courses that cover the special cases
    {                                               # course 1: Hebrew name with a keyboard apostrophe '
        "id": "00000001",                           # 8-digit ID as text
        "name_he": "אלגברה אמ'",                    # contains ' (the Hebrew keyboard may type ׳ instead)
        "name_en": "Algebra AM",                    # has an English name (with capital letters)
        "credits": 5.5,                             # half point, to make sure floats are kept
    },
    {                                               # course 2: Hebrew name with a keyboard double quote "
        "id": "00000002",
        "name_he": 'לוגיקה למדמ"ח',                 # contains " (the Hebrew keyboard may type ״ instead)
        "name_en": "Logic for CS",
        "credits": 3.0,
    },
    {                                               # course 3: no English name
        "id": "00000003",
        "name_he": "מבני נתונים",                   # plain Hebrew name
        "name_en": "",                              # empty English name, like 201 real courses
        "credits": 3.0,
    },
]


def create_catalog_from_fake_courses(tmp_path, courses):
    """Write `courses` into a temporary JSON file and return a CourseCatalog loaded from it.

    Args:
        tmp_path: The temporary folder pytest gives each test (deleted afterwards).
        courses: List of course dicts in the same shape as data/courses_data.json.

    Returns:
        A CourseCatalog built from the fake file.
    """
    fake_file = tmp_path / "courses.json"           # path of the fake file inside the temp folder
    fake_data = {                                   # same top-level shape as the real data file
        "catalog_year": "TEST-YEAR",                # a value we can check in a test
        "source": "TEST-SOURCE",                    # a value we can check in a test
        "courses": courses,                         # the courses given by the test
    }
    with open(fake_file, "w", encoding="utf-8") as f:   # utf-8 so Hebrew is written correctly
        json.dump(fake_data, f, ensure_ascii=False)     # ensure_ascii=False keeps Hebrew letters as letters
    return CourseCatalog(str(fake_file))            # load it with the real class (str() turns the Path into text)


# --------------------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------------------

def test_count_courses_returns_number_of_courses_in_file(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.count_courses() == 3             # three fake courses → 3


def test_catalog_year_and_source_are_read_from_file(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.catalog_year == "TEST-YEAR"      # the year comes from the file
    assert catalog.source == "TEST-SOURCE"          # the source comes from the file


def test_credits_keep_half_points(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.get_course_by_id("00000001").credits == 5.5  # 5.5 must not become 5


# --------------------------------------------------------------------------------------
# get_course_by_id
# --------------------------------------------------------------------------------------

def test_get_course_by_id_returns_matching_course(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    course = catalog.get_course_by_id("00000002")   # look up course 2 by its ID
    assert course is not None                       # it must be found
    assert course.name_en == "Logic for CS"         # and it must be the right course


def test_get_course_by_id_returns_none_for_unknown_id(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.get_course_by_id("99999999") is None  # unknown ID → None, not a crash


# --------------------------------------------------------------------------------------
# find_course_by_name_or_id
# --------------------------------------------------------------------------------------

def test_find_course_by_name_or_id_accepts_id(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("00000003").id == "00000003"  # search with a course number


def test_find_course_by_name_or_id_accepts_hebrew_name(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("מבני נתונים").id == "00000003"  # exact Hebrew name


def test_find_course_by_name_or_id_accepts_english_name_in_any_case(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("logic for cs").id == "00000002"  # all lowercase
    assert catalog.find_course_by_name_or_id("LOGIC FOR CS").id == "00000002"  # all uppercase


def test_id_hebrew_and_english_return_the_same_object(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    by_id = catalog.find_course_by_name_or_id("00000002")        # search by ID
    by_hebrew = catalog.find_course_by_name_or_id('לוגיקה למדמ"ח')  # search by Hebrew name
    by_english = catalog.find_course_by_name_or_id("Logic for CS")  # search by English name
    assert by_id is by_hebrew is by_english         # "is" = the very same object in memory, not just equal


def test_find_course_by_name_or_id_ignores_extra_spaces(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("  מבני   נתונים  ").id == "00000003"  # spaces at ends and doubled inside
    assert catalog.find_course_by_name_or_id(" 00000001 ").id == "00000001"          # an ID with spaces around it


def test_find_course_by_name_or_id_accepts_hebrew_geresh(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("אלגברה אמ׳").id == "00000001"  # typed with ׳, stored with '


def test_find_course_by_name_or_id_accepts_hebrew_gershayim(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("לוגיקה למדמ״ח").id == "00000002"  # typed with ״, stored with "


def test_find_course_by_name_or_id_returns_none_when_nothing_matches(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("no such course") is None  # nothing matches → None


def test_empty_search_text_returns_none(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.find_course_by_name_or_id("") is None     # empty text must not "find" the course with no English name
    assert catalog.find_course_by_name_or_id("   ") is None  # only spaces → also empty after normalizing


# --------------------------------------------------------------------------------------
# Duplicates
# --------------------------------------------------------------------------------------

def test_duplicate_course_id_raises_value_error(tmp_path):
    duplicated = FAKE_COURSES + [dict(FAKE_COURSES[0])]  # add a copy of course 1 → its ID appears twice
    with pytest.raises(ValueError):                 # the test passes only if ValueError is raised inside this block
        create_catalog_from_fake_courses(tmp_path, duplicated)  # loading must fail


def test_duplicate_hebrew_name_keeps_first_course(tmp_path):
    same_name_twice = [                             # two different IDs with the same Hebrew name (two different course numbers)
        {"id": "00000010", "name_he": "שם זהה", "name_en": "", "credits": 5.0},  # first in the file
        {"id": "00000020", "name_he": "שם זהה", "name_en": "", "credits": 5.0},  # second in the file
    ]
    catalog = create_catalog_from_fake_courses(tmp_path, same_name_twice)  # must load without an error
    assert catalog.count_courses() == 2             # both courses exist by ID
    assert catalog.find_course_by_name_or_id("שם זהה").id == "00000010"  # the name finds the FIRST one


# --------------------------------------------------------------------------------------
# is_course_id_in_catalog, get_all_courses_sorted_by_id, normalize
# --------------------------------------------------------------------------------------

def test_is_course_id_in_catalog(tmp_path):
    catalog = create_catalog_from_fake_courses(tmp_path, FAKE_COURSES)  # build the fake catalog
    assert catalog.is_course_id_in_catalog("00000001") is True   # known ID
    assert catalog.is_course_id_in_catalog("99999999") is False  # unknown ID


def test_get_all_courses_sorted_by_id_returns_all_in_order(tmp_path):
    shuffled = [FAKE_COURSES[2], FAKE_COURSES[0], FAKE_COURSES[1]]  # same courses, file order 3, 1, 2
    catalog = create_catalog_from_fake_courses(tmp_path, shuffled)  # build the catalog from the shuffled file
    ids = [course.id for course in catalog.get_all_courses_sorted_by_id()]  # take only the IDs, in returned order
    assert ids == ["00000001", "00000002", "00000003"]  # all three, sorted by ID


def test_normalize_examples():
    assert CourseCatalog.normalize("  Data   Structures 1 ") == "data structures 1"  # spaces + lowercase
    assert CourseCatalog.normalize("אלגברה אמ׳") == CourseCatalog.normalize("אלגברה אמ'")  # ׳ and ' match
    assert CourseCatalog.normalize("לוגיקה למדמ״ח") == CourseCatalog.normalize('לוגיקה למדמ"ח')  # ״ and " match
    assert CourseCatalog.normalize("") == ""        # empty stays empty


# --------------------------------------------------------------------------------------
# Real data file
# --------------------------------------------------------------------------------------

REAL_DATA_FILE = Path(__file__).parent.parent / "data" / "courses_data.json"  # tests/ → project folder → data/


def test_real_course_data_file_loads_323_courses():
    catalog = CourseCatalog(str(REAL_DATA_FILE))    # load the real file; fails if it is broken or has duplicate IDs
    assert catalog.count_courses() == 323           # all courses from the 2024/2025 catalog
    assert catalog.find_course_by_name_or_id("02340114").name_en == "Introduction to Computer Science"  # spot check
