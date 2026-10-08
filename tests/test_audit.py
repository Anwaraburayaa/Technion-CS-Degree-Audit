"""Tests for core/audit.py (the calculation engine).

The small functions are tested on tiny made-up rules, so each test shows one behaviour.
run_audit is tested on the real files data/requirements.json and data/courses_data.json.
These tests only look at the five categories that run_audit handles on Day 2, so adding the
Day 3 categories to the result does not break them.

Run from the project folder with:  ./run_tests.sh
"""
import json                                         # to write a fake requirements file
from pathlib import Path                            # to build file paths that work on any system

import pytest                                       # for pytest.raises

from core.audit import check_manual_entries         # refuses negative manual numbers
from core.audit import count_remaining_courses      # how many courses of a rule are still needed
from core.audit import find_missing_course_ids      # which courses of a rule are not done
from core.audit import is_chain_complete            # is one science chain option fully done
from core.audit import load_requirements_from_file  # reads the rules file
from core.audit import run_audit                    # the main function
from core.catalog import CourseCatalog              # the class that loads the 324 courses
from core.models import Category                    # the 14 rule names


# --------------------------------------------------------------------------------------
# Paths, made-up rules and helpers
# --------------------------------------------------------------------------------------

PROJECT_FOLDER = Path(__file__).parent.parent                        # tests/ → project folder
REQUIREMENTS_FILE = PROJECT_FOLDER / "data" / "requirements.json"    # the real rules
COURSES_FILE = PROJECT_FOLDER / "data" / "courses_data.json"         # the real 324 courses

THREE_OF_FOUR_RULE = {                              # a made-up required_courses rule
    "key": "test_rule",                             # any name, these functions do not read it
    "kind": "required_courses",                     # the kind these functions are for
    "label": "Test rule",                           # any text
    "courses": ["00000001", "00000002", "00000003", "00000004"],  # four made-up course numbers
    "needed": 3,                                    # the student must finish 3 of the 4
}

ONE_OF_TWO_RULE = {                                 # a made-up either-or pair
    "key": "test_pair",                             # any name
    "kind": "required_courses",                     # same kind as the real pairs
    "label": "Test pair",                           # any text
    "courses": ["00000011", "00000012"],            # two made-up course numbers
    "needed": 1,                                    # one of the two is enough
}

CHAIN_RULE = {                                      # a made-up one_complete_option rule
    "key": "test_chain",                            # any name
    "kind": "one_complete_option",                  # the kind is_chain_complete is for
    "label": "Test chain",                          # any text
    "options": [                                    # two options
        {"name": "Single", "courses": ["00000021"]},  # an option of one course
        {"name": "Pair", "courses": ["00000022", "00000023"]},  # an option of two courses
    ],
}

ALL_MANDATORY_FIXED_IDS = {                         # the 18 fixed mandatory courses of the real file
    "01040031", "01040166", "02340114", "02340129", "03240033", "01040032",
    "01140071", "02340124", "02340125", "02340141", "00940412", "01040134",
    "02340218", "02340292", "02340118", "02340123", "02340247", "02360343",
}


def load_real_files():
    """Load the real rules and the real catalog.

    Returns:
        A pair (requirements, catalog) ready for run_audit.
    """
    requirements = load_requirements_from_file(str(REQUIREMENTS_FILE))  # the 14 real rules
    catalog = CourseCatalog(str(COURSES_FILE))      # the 324 real courses
    return requirements, catalog                    # both, in the order run_audit takes them


def audit_real(completed_course_ids, manual_entries=None):
    """Run run_audit on the real files for one made-up student.

    Args:
        completed_course_ids: The set of course numbers the student passed.
        manual_entries: The numbers typed by hand; an empty dict when not given.

    Returns:
        The AuditResult of run_audit.
    """
    requirements, catalog = load_real_files()       # the real rules and courses
    if manual_entries is None:                      # no manual numbers given
        manual_entries = {}                         # use an empty dict
    return run_audit(requirements, catalog, completed_course_ids, manual_entries)  # the result


# --------------------------------------------------------------------------------------
# load_requirements_from_file
# --------------------------------------------------------------------------------------

def test_load_returns_the_14_real_rules():
    requirements = load_requirements_from_file(str(REQUIREMENTS_FILE))  # read the real file
    assert len(requirements["rules"]) == 14         # one rule per Category member
    assert requirements["total_min_points"] == 118.5  # the degree total is read too


def test_load_raises_for_an_unknown_rule_key(tmp_path):
    fake_file = tmp_path / "requirements.json"      # a fake file inside the temp folder
    fake_data = {"rules": [{"key": "no_such_rule", "kind": "required_courses", "label": "X"}]}  # a key Category does not know
    with open(fake_file, "w", encoding="utf-8") as f:  # write the fake file
        json.dump(fake_data, f)                     # as JSON
    with pytest.raises(ValueError):                 # Category("no_such_rule") must fail
        load_requirements_from_file(str(fake_file))  # load the fake file


# --------------------------------------------------------------------------------------
# find_missing_course_ids
# --------------------------------------------------------------------------------------

def test_missing_ids_when_nothing_is_done():
    missing = find_missing_course_ids(THREE_OF_FOUR_RULE, set())  # an empty set: nothing done
    assert missing == ["00000001", "00000002", "00000003", "00000004"]  # every course, in the rule's order


def test_missing_ids_when_some_are_done_but_not_enough():
    missing = find_missing_course_ids(THREE_OF_FOUR_RULE, {"00000002"})  # 1 of the 3 needed
    assert missing == ["00000001", "00000003", "00000004"]  # the courses not done, in the rule's order


def test_missing_ids_is_empty_when_enough_are_done():
    done = {"00000001", "00000002", "00000004"}     # 3 of 4: exactly what is needed
    assert find_missing_course_ids(THREE_OF_FOUR_RULE, done) == []  # the rule is done, nothing missing


def test_missing_ids_is_empty_when_one_of_a_pair_is_done():
    assert find_missing_course_ids(ONE_OF_TWO_RULE, {"00000012"}) == []  # one of two is enough


def test_missing_ids_ignores_courses_outside_the_rule():
    done = {"99999999", "88888888", "77777777"}     # three courses that are not in the rule
    missing = find_missing_course_ids(THREE_OF_FOUR_RULE, done)  # they must not count
    assert len(missing) == 4                        # all four courses of the rule are still missing


# --------------------------------------------------------------------------------------
# count_remaining_courses
# --------------------------------------------------------------------------------------

def test_remaining_count_when_nothing_is_done():
    assert count_remaining_courses(THREE_OF_FOUR_RULE, set()) == 3  # all 3 needed are left


def test_remaining_count_when_some_are_done():
    assert count_remaining_courses(THREE_OF_FOUR_RULE, {"00000001"}) == 2  # 3 needed − 1 done


def test_remaining_count_is_zero_when_enough_are_done():
    done = {"00000001", "00000002", "00000003"}     # exactly 3 of 4
    assert count_remaining_courses(THREE_OF_FOUR_RULE, done) == 0  # nothing left


def test_remaining_count_never_goes_below_zero():
    done = {"00000001", "00000002", "00000003", "00000004"}  # 4 done, only 3 needed
    assert count_remaining_courses(THREE_OF_FOUR_RULE, done) == 0  # 0, not −1


# --------------------------------------------------------------------------------------
# is_chain_complete
# --------------------------------------------------------------------------------------

def test_chain_is_not_complete_when_nothing_is_done():
    assert is_chain_complete(CHAIN_RULE, set()) is False  # no option is done


def test_chain_is_complete_with_a_one_course_option():
    assert is_chain_complete(CHAIN_RULE, {"00000021"}) is True  # the "Single" option is done


def test_chain_is_not_complete_with_half_of_a_two_course_option():
    assert is_chain_complete(CHAIN_RULE, {"00000022"}) is False  # the "Pair" option needs both


def test_chain_is_complete_with_both_courses_of_a_two_course_option():
    assert is_chain_complete(CHAIN_RULE, {"00000022", "00000023"}) is True  # the "Pair" option is done


# --------------------------------------------------------------------------------------
# check_manual_entries
# --------------------------------------------------------------------------------------

def test_manual_entries_empty_dict_is_accepted():
    assert check_manual_entries({}) is None         # no numbers typed: no error, returns None


def test_manual_entries_zero_and_positive_are_accepted():
    entries = {Category.SPORT: 0.0, Category.MALAG: 4.5}  # zero and a positive number
    assert check_manual_entries(entries) is None    # no error


def test_manual_entries_negative_raises_and_names_the_category():
    with pytest.raises(ValueError, match="sport"):  # the message must say which category
        check_manual_entries({Category.SPORT: -1.0})  # a negative number


# --------------------------------------------------------------------------------------
# run_audit on the real files
# --------------------------------------------------------------------------------------

def test_run_audit_with_no_courses_remaining_numbers():
    result = audit_real(set())                      # a student with no courses
    remaining = result.remaining_by_category        # the dict Category → what is left
    assert remaining[Category.MANDATORY_FIXED] == 18  # all 18 fixed courses are left
    assert remaining[Category.DIGITAL_SYSTEMS] == 1  # one course of the pair is left
    assert remaining[Category.COMPILATION_OR_ARCHITECTURE] == 1  # one course of the pair is left
    assert remaining[Category.EXTRA_MATH] == 1      # one extra math course is left
    assert remaining[Category.SCIENCE_CHAIN] == 1   # the chain is not done


def test_run_audit_with_no_courses_missing_lists():
    result = audit_real(set())                      # a student with no courses
    missing = result.missing_courses_by_category    # the dict Category → list of Course
    assert len(missing[Category.MANDATORY_FIXED]) == 18  # all 18 are listed
    assert len(missing[Category.DIGITAL_SYSTEMS]) == 2  # both courses of the pair are options
    assert len(missing[Category.COMPILATION_OR_ARCHITECTURE]) == 2  # both courses of the pair are options
    assert len(missing[Category.EXTRA_MATH]) == 7   # all 7 extra math courses are options


def test_run_audit_lists_the_one_missing_mandatory_course_as_a_course_object():
    requirements, catalog = load_real_files()       # the real rules and courses
    done = ALL_MANDATORY_FIXED_IDS - {"02340114"}   # every fixed course except one
    result = run_audit(requirements, catalog, done, {})  # run the audit
    assert result.remaining_by_category[Category.MANDATORY_FIXED] == 1  # one course left
    assert result.missing_courses_by_category[Category.MANDATORY_FIXED] == [catalog.get_course_by_id("02340114")]  # the Course object, not the number


def test_run_audit_one_course_of_digital_systems_is_enough():
    result = audit_real({"02340252"})               # one of the two numbers of the same course
    assert result.remaining_by_category[Category.DIGITAL_SYSTEMS] == 0  # done
    assert result.missing_courses_by_category[Category.DIGITAL_SYSTEMS] == []  # nothing listed


def test_run_audit_both_courses_of_a_pair_still_give_zero():
    result = audit_real({"02360360", "02360267"})   # Compilation and Computer Architecture
    assert result.remaining_by_category[Category.COMPILATION_OR_ARCHITECTURE] == 0  # 0, not −1


def test_run_audit_computer_architecture_alone_is_enough():
    result = audit_real({"02360267"})               # only Computer Architecture
    assert result.remaining_by_category[Category.COMPILATION_OR_ARCHITECTURE] == 0  # the pair is done


def test_run_audit_one_extra_math_course_is_enough():
    result = audit_real({"01040295"})               # one course from the list of 7
    assert result.remaining_by_category[Category.EXTRA_MATH] == 0  # done
    assert result.missing_courses_by_category[Category.EXTRA_MATH] == []  # nothing listed


def test_run_audit_physics_2_alone_does_not_complete_the_chain():
    result = audit_real({"01140052"})               # Physics 2 without Physics 3
    assert result.remaining_by_category[Category.SCIENCE_CHAIN] == 1  # not done


def test_run_audit_physics_2_and_3_complete_the_chain():
    result = audit_real({"01140052", "01140054"})   # the option Physics (2 + 3)
    assert result.remaining_by_category[Category.SCIENCE_CHAIN] == 0  # done


def test_run_audit_physics_2mm_alone_completes_the_chain():
    result = audit_real({"01140075"})               # the option Physics (2MM), one course
    assert result.remaining_by_category[Category.SCIENCE_CHAIN] == 0  # done


def test_run_audit_everything_done_gives_zero_everywhere():
    done = ALL_MANDATORY_FIXED_IDS | {"00440252", "02360360", "01040135", "01140075"}  # 18 fixed + both pairs + extra math + a chain
    result = audit_real(done)                       # run the audit
    day_2_categories = [                            # the five categories run_audit handles on Day 2
        Category.MANDATORY_FIXED,                   # the 18 fixed courses
        Category.DIGITAL_SYSTEMS,                   # the first pair
        Category.COMPILATION_OR_ARCHITECTURE,       # the second pair
        Category.EXTRA_MATH,                        # one extra math course
        Category.SCIENCE_CHAIN,                     # one complete chain
    ]
    for category in day_2_categories:               # check them one by one
        assert result.remaining_by_category[category] == 0, category  # done; the category is shown if it fails
    for course_list in result.missing_courses_by_category.values():  # every list of missing courses
        assert course_list == []                    # is empty


def test_run_audit_refuses_a_negative_manual_entry():
    with pytest.raises(ValueError):                 # run_audit must stop at its first step
        audit_real(set(), {Category.MALAG: -2.0})   # a negative manual number