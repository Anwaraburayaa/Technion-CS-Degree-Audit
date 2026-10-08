"""Tests for the DATA file data/requirements.json (not for any Python class).

These tests catch mistakes made while editing the JSON by hand: a mistyped course ID,
a rule key written twice, a kind the code does not know, or a rule that points to a
rule that does not exist.

Run from the project folder with:  pytest -v
"""
import json                                         # to read the requirements file
from pathlib import Path                            # to build file paths that work on any system

from core.catalog import CourseCatalog              # the class that loads the 324 courses


# --------------------------------------------------------------------------------------
# Paths, constants and helper
# --------------------------------------------------------------------------------------

PROJECT_FOLDER = Path(__file__).parent.parent                        # tests/ → project folder
REQUIREMENTS_FILE = PROJECT_FOLDER / "data" / "requirements.json"    # the file under test
COURSES_FILE = PROJECT_FOLDER / "data" / "courses_data.json"         # the 324 real courses

KNOWN_KINDS = {                                     # every kind the audit engine will know how to check
    "required_courses",                             # "complete `needed` courses out of `courses`"
    "points_from_courses",                          # "collect `min_points` from the courses in `courses`"
    "points_from_rules",                            # "collect `min_points` from the rules named in `rules`"
    "manual_points",                                # "the student types points; needs `min_points`"
    "manual_count",                                 # "the student types a number of courses; needs `min_count`"
    "one_complete_option",                          # "complete EVERY course of at least one entry in `options`"
}

FIELDS_REQUIRED_BY_KIND = {                         # which extra fields each kind must have
    "required_courses": ["courses", "needed"],      # a list of IDs and how many of them are needed
    "points_from_courses": ["courses", "min_points"],  # a list of IDs and a points minimum
    "points_from_rules": ["rules", "min_points"],   # a list of rule keys and a points minimum
    "manual_points": ["min_points"],                # only a points minimum
    "manual_count": ["min_count"],                  # only a count minimum
    "one_complete_option": ["options"],             # a list of options, each with a name and a course list
}


def load_requirements_file():
    """Read data/requirements.json and return its content as a Python dict.

    Returns:
        The whole file as a dict with the keys catalog_year, track, source,
        total_min_points and rules.
    """
    with open(REQUIREMENTS_FILE, encoding="utf-8") as f:  # utf-8 so the Hebrew catalog year is read correctly
        return json.load(f)                         # turn the JSON text into dicts and lists


def collect_all_course_ids_of_rule(rule):
    """Return every course ID written anywhere inside one rule, as a list.

    A rule can hold IDs in two places: directly in `courses`, or inside each entry
    of `options` (the science chain). This helper reads both places.

    Args:
        rule: One rule dict from data/requirements.json.

    Returns:
        A list of course ID strings (empty for rules that have no courses).
    """
    course_ids = list(rule.get("courses", []))      # the direct course list, or an empty list; list() makes a copy
    for option in rule.get("options", []):          # rules without options give an empty list
        course_ids.extend(option["courses"])        # add the courses of this option to the result
    return course_ids                               # all IDs of the rule, repeats included


# --------------------------------------------------------------------------------------
# Top level of the file
# --------------------------------------------------------------------------------------

def test_requirements_file_has_all_top_level_fields():
    requirements = load_requirements_file()         # read the file
    for field in ["catalog_year", "track", "source", "total_min_points", "rules"]:  # every field the app reads
        assert field in requirements                # a missing field fails here, with the field name in the report


def test_total_min_points_is_118_5():
    requirements = load_requirements_file()         # read the file
    assert requirements["total_min_points"] == 118.5  # the degree total of the 3-year track


def test_requirements_and_courses_use_the_same_catalog_year():
    requirements = load_requirements_file()         # read the requirements file
    catalog = CourseCatalog(str(COURSES_FILE))      # load the real courses
    assert requirements["catalog_year"] == catalog.catalog_year  # rules and courses must come from the same catalog


# --------------------------------------------------------------------------------------
# Shape of every rule
# --------------------------------------------------------------------------------------

def test_every_rule_has_key_kind_and_label():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        assert "key" in rule                        # the unique name of the rule
        assert "kind" in rule                       # which check the code must run
        assert "label" in rule                      # the name shown to the student


def test_rule_keys_are_unique():
    requirements = load_requirements_file()         # read the file
    keys = [rule["key"] for rule in requirements["rules"]]  # take only the keys, in file order
    assert len(keys) == len(set(keys))              # a set drops repeats, so equal lengths means no key is repeated


def test_every_rule_kind_is_known():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        assert rule["kind"] in KNOWN_KINDS, rule["key"]  # the text after the comma is shown if the check fails


def test_every_rule_has_the_fields_its_kind_needs():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        for field in FIELDS_REQUIRED_BY_KIND[rule["kind"]]:  # the fields this kind must have
            assert field in rule, f"{rule['key']} is missing {field}"  # report which rule and which field


def test_minimums_are_not_negative():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        minimum = rule.get("min_points", rule.get("min_count", 0))  # the rule's minimum, or 0 if it has none
        assert minimum >= 0, rule["key"]            # a negative minimum is always a typing mistake


# --------------------------------------------------------------------------------------
# Course IDs inside the rules
# --------------------------------------------------------------------------------------

def test_every_course_id_in_requirements_exists_in_courses_data():
    requirements = load_requirements_file()         # read the requirements file
    catalog = CourseCatalog(str(COURSES_FILE))      # load the real courses
    unknown_ids = []                                # collect every bad ID so one run shows all of them
    for rule in requirements["rules"]:              # go over the rules one by one
        for course_id in collect_all_course_ids_of_rule(rule):  # IDs from `courses` and from `options`
            if not catalog.is_course_id_in_catalog(course_id):  # the ID is not one of the 324 courses
                unknown_ids.append((rule["key"], course_id))    # remember the rule and the bad ID
    assert unknown_ids == []                        # passes only if no bad ID was found


def test_no_course_id_is_repeated_inside_one_rule():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        course_ids = rule.get("courses", [])        # the rule's course list, or an empty list
        assert len(course_ids) == len(set(course_ids)), rule["key"]  # equal lengths means no ID appears twice


def test_needed_is_between_one_and_the_number_of_courses():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        if rule["kind"] == "required_courses":      # only this kind has the field `needed`
            assert 1 <= rule["needed"] <= len(rule["courses"]), rule["key"]  # cannot need 0 courses or more than exist


def test_every_course_in_courses_data_belongs_to_at_least_one_rule():
    requirements = load_requirements_file()         # read the requirements file
    catalog = CourseCatalog(str(COURSES_FILE))      # load the real courses
    ids_used_in_rules = set()                       # every ID that appears in any rule
    for rule in requirements["rules"]:              # go over the rules one by one
        ids_used_in_rules.update(collect_all_course_ids_of_rule(rule))  # add this rule's IDs to the set
    all_course_ids = {course.id for course in catalog.get_all_courses_sorted_by_id()}  # the 324 IDs as a set
    assert all_course_ids - ids_used_in_rules == set()  # set difference: courses that no rule mentions; must be empty


# --------------------------------------------------------------------------------------
# Science chain (kind one_complete_option)
# --------------------------------------------------------------------------------------

def test_every_option_has_a_name_and_at_least_one_course():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        for option in rule.get("options", []):      # only one_complete_option has this field
            assert option["name"] != "", rule["key"]        # the name is shown to the student
            assert len(option["courses"]) >= 1, rule["key"]  # an empty option would count as completed by everyone


def test_no_course_id_is_repeated_inside_one_option():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        for option in rule.get("options", []):      # only one_complete_option has this field
            assert len(option["courses"]) == len(set(option["courses"])), option["name"]  # no ID twice in an option


def test_every_science_chain_course_is_in_the_science_list():
    requirements = load_requirements_file()         # read the file
    rules_by_key = {rule["key"]: rule for rule in requirements["rules"]}  # dict: key → rule, to find two rules by name
    science_ids = set(rules_by_key["science"]["courses"])  # the 12 science courses as a set
    for option in rules_by_key["science_chain"]["options"]:  # go over the chain options
        assert set(option["courses"]) <= science_ids, option["name"]  # <= on sets means "is a subset of"


# --------------------------------------------------------------------------------------
# Rules that point to other rules (List A + List B, general electives)
# --------------------------------------------------------------------------------------

def test_rules_that_sum_other_rules_point_to_existing_keys():
    requirements = load_requirements_file()         # read the file
    all_keys = {rule["key"] for rule in requirements["rules"]}  # every rule key as a set
    for rule in requirements["rules"]:              # go over the rules one by one
        for referenced_key in rule.get("rules", []):  # only points_from_rules has this field
            assert referenced_key in all_keys, f"{rule['key']} points to unknown rule {referenced_key}"  # mistyped key


def test_a_rule_never_points_to_itself():
    requirements = load_requirements_file()         # read the file
    for rule in requirements["rules"]:              # go over the rules one by one
        assert rule["key"] not in rule.get("rules", []), rule["key"]  # a rule summing itself would never finish


# --------------------------------------------------------------------------------------
# Exclusions (exclude_rules on list_a and list_b)
# --------------------------------------------------------------------------------------

def test_exclude_rules_point_to_existing_rules_that_list_courses():
    requirements = load_requirements_file()         # read the file
    rules_by_key = {rule["key"]: rule for rule in requirements["rules"]}  # dict: key → rule
    for rule in requirements["rules"]:              # go over the rules one by one
        for excluded_key in rule.get("exclude_rules", []):  # only list_a and list_b have this field
            assert excluded_key in rules_by_key, f"{rule['key']} excludes unknown rule {excluded_key}"  # mistyped key
            assert excluded_key != rule["key"], rule["key"]  # a rule must not exclude itself
            assert "courses" in rules_by_key[excluded_key], excluded_key  # only a rule with a course list can be excluded


def test_list_a_and_list_b_exclude_the_agreed_rules():
    requirements = load_requirements_file()         # read the file
    rules_by_key = {rule["key"]: rule for rule in requirements["rules"]}  # dict: key → rule
    four_course_rules = {"mandatory_fixed", "digital_systems", "compilation_or_architecture", "extra_math"}  # mandatory and extra math
    assert set(rules_by_key["list_a"]["exclude_rules"]) == four_course_rules  # List A: the four course rules
    assert set(rules_by_key["list_b"]["exclude_rules"]) == four_course_rules | {"science"}  # List B: the same four plus science
