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
from core.catalog import CourseCatalog              # the class that loads the 323 courses
from core.models import Category                    # the 13 rule names


# --------------------------------------------------------------------------------------
# Paths, made-up rules and helpers
# --------------------------------------------------------------------------------------

PROJECT_FOLDER = Path(__file__).parent.parent                        # tests/ → project folder
REQUIREMENTS_FILE = PROJECT_FOLDER / "data" / "requirements.json"    # the real rules
COURSES_FILE = PROJECT_FOLDER / "data" / "courses_data.json"         # the real 323 courses

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

ALL_MANDATORY_FIXED_IDS = {                         # the 19 fixed mandatory courses of the real file
    "01040031", "01040166", "02340114", "02340129", "03240033", "01040032",
    "01140071", "02340124", "02340125", "02340141", "00940412", "01040134",
    "02340218", "02340292", "02340118", "02340123", "02340247", "02360343",
    "00440252",
}


def load_real_files():
    """Load the real rules and the real catalog.

    Returns:
        A pair (requirements, catalog) ready for run_audit.
    """
    requirements = load_requirements_from_file(str(REQUIREMENTS_FILE))  # the 13 real rules
    catalog = CourseCatalog(str(COURSES_FILE))      # the 323 real courses
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

def test_load_returns_the_13_real_rules():
    requirements = load_requirements_from_file(str(REQUIREMENTS_FILE))  # read the real file
    assert len(requirements["rules"]) == 13         # one rule per Category member
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
    assert remaining[Category.MANDATORY_FIXED] == 19  # all 19 fixed courses are left
    assert remaining[Category.COMPILATION_OR_ARCHITECTURE] == 1  # one course of the pair is left
    assert remaining[Category.EXTRA_MATH] == 1      # one extra math course is left
    assert remaining[Category.SCIENCE_CHAIN] == 1   # the chain is not done


def test_run_audit_with_no_courses_missing_lists():
    result = audit_real(set())                      # a student with no courses
    missing = result.missing_courses_by_category    # the dict Category → list of Course
    assert len(missing[Category.MANDATORY_FIXED]) == 19  # all 19 are listed
    assert len(missing[Category.COMPILATION_OR_ARCHITECTURE]) == 2  # both courses of the pair are options
    assert len(missing[Category.EXTRA_MATH]) == 7   # all 7 extra math courses are options


def test_run_audit_lists_the_one_missing_mandatory_course_as_a_course_object():
    requirements, catalog = load_real_files()       # the real rules and courses
    done = ALL_MANDATORY_FIXED_IDS - {"02340114"}   # every fixed course except one
    result = run_audit(requirements, catalog, done, {})  # run the audit
    assert result.remaining_by_category[Category.MANDATORY_FIXED] == 1  # one course left
    assert result.missing_courses_by_category[Category.MANDATORY_FIXED] == [catalog.get_course_by_id("02340114")]  # the Course object, not the number


def test_run_audit_digital_systems_is_a_mandatory_course():
    result = audit_real({"00440252"})               # only Digital Systems and Computer Structure
    assert result.remaining_by_category[Category.MANDATORY_FIXED] == 18  # 19 mandatory courses minus this one
    missing_ids = [course.id for course in result.missing_courses_by_category[Category.MANDATORY_FIXED]]  # the numbers still missing
    assert "00440252" not in missing_ids            # it is not listed as missing


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
    done = ALL_MANDATORY_FIXED_IDS | {"00440252", "02360360", "01040295", "01140075"}  # 19 fixed + the pair + extra math (01040295 has no condition) + a chain
    result = audit_real(done)                       # run the audit
    day_2_categories = [                            # the four course categories run_audit handles on Day 2
        Category.MANDATORY_FIXED,                   # the 19 fixed courses
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

# ======================================================================================
# Day 3: the points audit
# ======================================================================================

from core.audit import collect_excluded_course_ids  # rule names in exclude_rules -> course ids
from core.audit import count_remaining_points       # minimum minus have, never below 0
from core.audit import filter_conditional_courses   # drops a course whose condition is not met
from core.audit import sum_completed_points         # points of the completed courses of one rule
from core.audit import sum_total_points             # the degree total
from core.models import AuditResult                 # the result object, to test its property

ODE_CONDITION_RULE = {                              # a made-up rule with the same condition as extra_math
    "conditional_courses": {"01040135": ["01140073", "01150203", "01240400", "01140101"]},  # ODE counts only with one of these
}


def rules_by_key():
    """Return the real rules as a dict: key -> rule.

    Returns:
        A dict from rule key to rule dict, read from the real file.
    """
    requirements = load_requirements_from_file(str(REQUIREMENTS_FILE))  # the 13 real rules
    return {rule["key"]: rule for rule in requirements["rules"]}  # one entry per rule


# --------------------------------------------------------------------------------------
# sum_completed_points
# --------------------------------------------------------------------------------------

def test_sum_points_counts_only_the_completed_courses_of_the_rule():
    _, catalog = load_real_files()                  # the real catalog, for the points
    rule = {"courses": ["01140052", "01140054", "01240120"]}  # physics 2, physics 3, chemistry
    done = {"01140052", "01240120", "02340114"}     # 02340114 is not in the rule
    assert sum_completed_points(rule, done, set(), catalog) == pytest.approx(8.5)  # 3.5 + 5.0


def test_sum_points_skips_excluded_courses():
    _, catalog = load_real_files()                  # the real catalog
    rule = {"courses": ["01140052", "01240120"]}    # physics 2 and chemistry
    done = {"01140052", "01240120"}                 # both completed
    assert sum_completed_points(rule, done, {"01240120"}, catalog) == pytest.approx(3.5)  # chemistry is excluded


def test_sum_points_keeps_half_points():
    _, catalog = load_real_files()                  # the real catalog
    rule = {"courses": ["01140052", "01140054"]}    # two courses of 3.5 points
    assert sum_completed_points(rule, {"01140052", "01140054"}, set(), catalog) == pytest.approx(7.0)  # not 6 or 8


def test_sum_points_is_zero_when_nothing_is_completed():
    _, catalog = load_real_files()                  # the real catalog
    assert sum_completed_points({"courses": ["01140052"]}, set(), set(), catalog) == 0.0  # nothing done


# --------------------------------------------------------------------------------------
# collect_excluded_course_ids
# --------------------------------------------------------------------------------------

def test_list_a_excludes_the_courses_of_the_four_course_rules():
    requirements, _ = load_real_files()             # the real rules
    excluded = collect_excluded_course_ids(rules_by_key()["list_a"], requirements)  # list_a's exclusions
    assert len(excluded) == 28                      # 19 + 2 + 7
    assert "02360360" in excluded                   # compilation is mandatory, so not in list a


def test_list_b_also_excludes_the_science_courses():
    requirements, _ = load_real_files()             # the real rules
    excluded = collect_excluded_course_ids(rules_by_key()["list_b"], requirements)  # list_b's exclusions
    assert len(excluded) == 40                      # the same 28 + 12 science courses
    assert "01240120" in excluded                   # a science course printed in list b
    assert "01040174" in excluded                   # an extra math course printed in list b


def test_a_rule_without_exclude_rules_excludes_nothing():
    requirements, _ = load_real_files()             # the real rules
    assert collect_excluded_course_ids(rules_by_key()["science"], requirements) == set()  # science has no exclude_rules


# --------------------------------------------------------------------------------------
# count_remaining_points
# --------------------------------------------------------------------------------------

def test_remaining_points_is_the_minimum_minus_what_the_student_has():
    assert count_remaining_points(8.0, 3.5) == pytest.approx(4.5)  # 8 - 3.5


def test_remaining_points_never_goes_below_zero_and_is_a_float():
    result = count_remaining_points(8.0, 12.0)      # more than enough
    assert result == 0.0                            # 0, not -4
    assert isinstance(result, float)                # 0.0, not the int 0


# --------------------------------------------------------------------------------------
# filter_conditional_courses
# --------------------------------------------------------------------------------------

def test_ode_is_removed_without_its_condition_course():
    result = filter_conditional_courses(ODE_CONDITION_RULE, {"01040135", "02340114"})  # no condition course
    assert result == {"02340114"}                   # ode does not count


def test_ode_stays_with_one_condition_course():
    done = {"01040135", "01140101"}                 # ode + analytical mechanics
    assert filter_conditional_courses(ODE_CONDITION_RULE, done) == done  # the condition is met


def test_filter_does_not_change_the_students_own_set():
    done = {"01040135", "02340114"}                 # the student's set
    filter_conditional_courses(ODE_CONDITION_RULE, done)  # run the filter
    assert done == {"01040135", "02340114"}         # still both courses


def test_filter_returns_a_copy_for_a_rule_without_conditions():
    done = {"01040135"}                             # any set
    result = filter_conditional_courses({}, done)   # a rule with no conditional_courses
    assert result == done                           # same courses
    assert result is not done                       # but a new set


# --------------------------------------------------------------------------------------
# sum_total_points
# --------------------------------------------------------------------------------------

def test_total_counts_every_known_course_once_and_skips_unknown_ones():
    _, catalog = load_real_files()                  # the real catalog
    done = {"01140052", "02340114", "99999999"}     # 3.5 + 4.0 + an unknown number
    assert sum_total_points(done, {}, catalog, {}, {}) == pytest.approx(7.5)  # the unknown one adds nothing


def test_total_uses_the_real_points_of_a_replacement():
    _, catalog = load_real_files()                  # the real catalog
    total = sum_total_points({"01040166"}, {}, catalog, {"01040166": 5.0}, {})  # algebra am (5.5) replaced by a 5.0 course
    assert total == pytest.approx(5.0)              # the points of the course really taken


def test_total_adds_typed_sport_malag_free_but_not_typed_list_points():
    _, catalog = load_real_files()                  # the real catalog
    typed = {Category.SPORT: 2.0, Category.MALAG: 6.0, Category.FREE_OTHER: 2.0, Category.LIST_A: 3.0, Category.SCIENCE: 4.0}  # typed numbers
    assert sum_total_points(set(), typed, catalog, {}, {}) == pytest.approx(10.0)  # list a and science are moved surplus


def test_total_adds_the_assigned_points():
    _, catalog = load_real_files()                  # the real catalog
    assigned = {Category.LIST_A: 5.0, Category.SPORT: 1.0}  # grade sheet courses the student assigned
    assert sum_total_points(set(), {}, catalog, {}, assigned) == pytest.approx(6.0)  # all of them count


# --------------------------------------------------------------------------------------
# AuditResult.is_eligible_to_graduate
# --------------------------------------------------------------------------------------

def test_eligible_when_every_rule_and_the_total_are_done():
    result = AuditResult({}, {Category.SPORT: 0, Category.MALAG: 0.0}, 0.0)  # everything 0
    assert result.is_eligible_to_graduate is True   # can graduate


def test_not_eligible_when_one_rule_is_not_done():
    result = AuditResult({}, {Category.SPORT: 0, Category.MALAG: 2.0}, 0.0)  # malag has 2 left
    assert result.is_eligible_to_graduate is False  # cannot graduate


def test_not_eligible_when_the_total_is_not_done():
    result = AuditResult({}, {Category.SPORT: 0}, 4.5)  # 4.5 points left to 118.5
    assert result.is_eligible_to_graduate is False  # cannot graduate


# --------------------------------------------------------------------------------------
# The rules file order that run_audit depends on
# --------------------------------------------------------------------------------------

def test_the_parts_of_a_sum_rule_come_before_it_in_the_file():
    requirements, _ = load_real_files()             # the real rules
    keys_in_order = [rule["key"] for rule in requirements["rules"]]  # the rule keys in file order
    for rule in requirements["rules"]:              # go over the rules
        for part_key in rule.get("rules", []):      # only list_a_plus_b and general have parts
            assert keys_in_order.index(part_key) < keys_in_order.index(rule["key"]), part_key  # the part is computed first


# --------------------------------------------------------------------------------------
# run_audit: the Day 3 rules on the real files
# --------------------------------------------------------------------------------------

def test_run_audit_mandatory_course_does_not_count_in_list_a():
    result = audit_real({"02360360"})               # compilation, which is printed in list a
    assert result.remaining_by_category[Category.LIST_A] == pytest.approx(18.0)  # list a still needs all 18


def test_run_audit_science_course_does_not_count_in_list_b():
    result = audit_real({"01240120"})               # chemistry, which is printed in list b
    assert result.remaining_by_category[Category.SCIENCE] == pytest.approx(3.0)  # it counts in science: 8 - 5
    assert result.remaining_by_category[Category.LIST_A_PLUS_B] == pytest.approx(24.5)  # but not in list a + b


def test_run_audit_list_a_and_list_b_add_up_in_the_combined_rule():
    result = audit_real({"02360766", "00440105"})   # intro to ml (list a, 3.5) + circuits (list b, 4.0)
    assert result.remaining_by_category[Category.LIST_A] == pytest.approx(14.5)  # 18 - 3.5
    assert result.remaining_by_category[Category.LIST_A_PLUS_B] == pytest.approx(17.0)  # 24.5 - 7.5


def test_run_audit_manual_entries_only():
    typed = {Category.SPORT: 2.0, Category.MALAG: 6.0, Category.FREE_OTHER: 2.0, Category.ENGLISH_TAUGHT: 2}  # typed by hand
    result = audit_real(set(), typed)               # no courses at all
    for category in [Category.SPORT, Category.MALAG, Category.FREE_OTHER, Category.GENERAL, Category.ENGLISH_TAUGHT]:  # the typed categories
        assert result.remaining_by_category[category] == 0, category  # all done
    assert result.remaining_total_points == pytest.approx(108.5)  # 118.5 - 10


def test_run_audit_ode_counts_as_extra_math_only_with_its_condition():
    without = audit_real({"01040135"})              # ode alone
    with_condition = audit_real({"01040135", "01140101"})  # ode + analytical mechanics
    assert without.remaining_by_category[Category.EXTRA_MATH] == 1  # not done
    assert with_condition.remaining_by_category[Category.EXTRA_MATH] == 0  # done


def test_run_audit_assigned_points_count_in_their_category_and_the_total():
    requirements, catalog = load_real_files()       # the real rules and courses
    assigned = {Category.LIST_A: 5.0}               # a grade sheet course assigned to list a
    result = run_audit(requirements, catalog, set(), {}, {}, assigned)  # run the audit
    assert result.remaining_by_category[Category.LIST_A] == pytest.approx(13.0)  # 18 - 5
    assert result.remaining_by_category[Category.LIST_A_PLUS_B] == pytest.approx(19.5)  # 24.5 - 5
    assert result.remaining_total_points == pytest.approx(113.5)  # 118.5 - 5


def test_run_audit_full_sample_student():
    requirements, catalog = load_real_files()       # the real rules and courses
    done = ALL_MANDATORY_FIXED_IDS | {"00440252", "02360360", "01040135",  # both pairs + ode without its condition
                                      "01140052", "01140054", "01240120", "01340058",  # physics 2 + 3, chemistry, biology 1
                                      "00440105", "02360766"}  # one list b course, one list a course
    typed = {Category.SPORT: 2.0, Category.MALAG: 4.0, Category.ENGLISH_TAUGHT: 1, Category.LIST_A: 3.0}  # typed by hand
    assigned = {Category.LIST_A: 5.0, Category.MALAG: 2.0}  # grade sheet courses the student assigned
    result = run_audit(requirements, catalog, done, typed, {}, assigned)  # run the audit
    remaining = result.remaining_by_category        # what is left per rule
    assert remaining[Category.EXTRA_MATH] == 1      # ode without its condition
    assert remaining[Category.SCIENCE] == 0         # 15 science points
    assert remaining[Category.SCIENCE_CHAIN] == 0   # physics 2 + 3
    assert remaining[Category.LIST_A] == pytest.approx(6.5)  # 18 - (3.5 + 3 typed + 5 assigned)
    assert remaining[Category.LIST_A_PLUS_B] == pytest.approx(9.0)  # 24.5 - (11.5 + 4)
    assert remaining[Category.GENERAL] == pytest.approx(2.0)  # 10 - (2 + 6)
    assert remaining[Category.ENGLISH_TAUGHT] == 1  # 2 - 1
    assert result.remaining_total_points == pytest.approx(7.0)  # 118.5 - 111.5
    assert result.is_eligible_to_graduate is False  # extra math, list a, and more are missing


def test_run_audit_a_finished_student_is_eligible():
    requirements, catalog = load_real_files()       # the real rules and courses
    done = ALL_MANDATORY_FIXED_IDS | {"00440252", "02360360", "01040295",  # both pairs + extra math without a condition
                                      "01140075", "01140052"}  # physics 2mm (a chain) + physics 2: 8.5 science points
    typed = {Category.SPORT: 2.0, Category.MALAG: 6.0, Category.FREE_OTHER: 2.0, Category.ENGLISH_TAUGHT: 2}  # general and english
    assigned = {Category.LIST_A: 18.0, Category.LIST_B: 6.5}  # faculty electives from the grade sheet
    result = run_audit(requirements, catalog, done, typed, {}, assigned)  # run the audit
    assert all(left == 0 for left in result.remaining_by_category.values())  # every rule is done
    assert result.remaining_total_points == 0.0     # the total is done
    assert result.is_eligible_to_graduate is True   # can graduate
