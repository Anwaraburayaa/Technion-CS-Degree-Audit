# tests for core/assignment.py (build_assignment)
# all rows here are made up: fake course numbers, fake names, fake grades
# run from the project folder with:  ./run_tests.sh

# we compare floats with approx, because 0.1 + 0.2 is not exactly 0.3
from pytest import approx

# the function we test
from core.assignment import build_assignment
# the categories the student can choose
from core.models import Category
# one course row of a grade sheet
from core.transcript import TranscriptRow


# we build one made-up passed row, only the id and the points matter here
def make_row(course_id, points):
    # the name and the grade are fake, build_assignment does not read them
    return TranscriptRow(course_id, "fake course", points, "90")


# no rows and no choices give two empty dicts
def test_empty_input_returns_two_empty_dicts():
    # we call the function with nothing
    assigned_points, replacement_points = build_assignment([], {})
    # nothing is assigned
    assert assigned_points == {}
    # nothing is replaced
    assert replacement_points == {}


# a course chosen as list a counts in list a
def test_list_a_choice():
    # one row worth 3 points, chosen as list a
    assigned_points, replacement_points = build_assignment([make_row("09000001", 3.0)], {"09000001": Category.LIST_A})
    # list a gets the 3 points
    assert assigned_points == {Category.LIST_A: approx(3.0)}
    # nothing is replaced
    assert replacement_points == {}


# a course chosen as list b counts in list b
def test_list_b_choice():
    # one row worth 2.5 points, chosen as list b
    assigned_points, _ = build_assignment([make_row("09000002", 2.5)], {"09000002": Category.LIST_B})
    # list b gets the 2.5 points
    assert assigned_points == {Category.LIST_B: approx(2.5)}


# a course chosen as sport counts in sport
def test_sport_choice():
    # one row worth 1 point, chosen as sport
    assigned_points, _ = build_assignment([make_row("09000003", 1.0)], {"09000003": Category.SPORT})
    # sport gets the 1 point
    assert assigned_points == {Category.SPORT: approx(1.0)}


# a course chosen as malag counts in malag
def test_malag_choice():
    # one row worth 2 points, chosen as malag
    assigned_points, _ = build_assignment([make_row("09000004", 2.0)], {"09000004": Category.MALAG})
    # malag gets the 2 points
    assert assigned_points == {Category.MALAG: approx(2.0)}


# a course chosen as other free counts in other free
def test_free_other_choice():
    # one row worth 4 points, chosen as other free
    assigned_points, _ = build_assignment([make_row("09000005", 4.0)], {"09000005": Category.FREE_OTHER})
    # other free gets the 4 points
    assert assigned_points == {Category.FREE_OTHER: approx(4.0)}


# an ignored course is not counted anywhere
def test_ignore_counts_nothing():
    # one row, chosen as ignore
    assigned_points, replacement_points = build_assignment([make_row("09000006", 3.0)], {"09000006": "ignore"})
    # nothing is assigned
    assert assigned_points == {}
    # nothing is replaced
    assert replacement_points == {}


# a course with no choice at all is treated like ignore
def test_missing_choice_counts_nothing():
    # one row, and the choices dict does not have its id
    assigned_points, replacement_points = build_assignment([make_row("09000007", 3.0)], {})
    # nothing is assigned
    assert assigned_points == {}
    # nothing is replaced
    assert replacement_points == {}


# two different courses in the same category are added together
def test_two_courses_in_same_category_are_added():
    # two different malag courses, 3 and 2 points
    rows = [make_row("09000008", 3.0), make_row("09000009", 2.0)]
    # both are chosen as malag
    choices = {"09000008": Category.MALAG, "09000009": Category.MALAG}
    # we run the function
    assigned_points, _ = build_assignment(rows, choices)
    # malag has 3 + 2 = 5 points
    assert assigned_points == {Category.MALAG: approx(5.0)}


# the same course twice in the grade sheet is counted once (the day 4 known issue)
def test_duplicate_course_is_counted_once():
    # the same sport course passed in two semesters
    rows = [make_row("09000010", 1.0), make_row("09000010", 1.0)]
    # it is chosen as sport
    assigned_points, _ = build_assignment(rows, {"09000010": Category.SPORT})
    # sport has 1 point, not 2
    assert assigned_points == {Category.SPORT: approx(1.0)}


# a replacement goes to replacement_points under the mandatory id, with the real points
def test_replacement_goes_to_replacement_points():
    # a 5 point course taken instead of mandatory 01040166
    assigned_points, replacement_points = build_assignment([make_row("01040066", 5.0)], {"01040066": "replace:01040166"})
    # the mandatory id gets the real points of the course taken
    assert replacement_points == {"01040166": approx(5.0)}
    # a replacement is not also counted in a category
    assert assigned_points == {}


# a replacement that appears twice in the grade sheet is still one replacement
def test_duplicate_replacement_is_counted_once():
    # the same replacement course twice
    rows = [make_row("01040066", 5.0), make_row("01040066", 5.0)]
    # it replaces mandatory 01040166
    _, replacement_points = build_assignment(rows, {"01040066": "replace:01040166"})
    # one entry with 5 points
    assert replacement_points == {"01040166": approx(5.0)}


# all the kinds of choice together, the same example as the step 13 check
def test_mixed_example():
    # a replacement, a sport course twice, a malag course, and an ignored course
    rows = [make_row("01040066", 5.0), make_row("03940800", 1.0), make_row("03940800", 1.0), make_row("03240900", 3.0), make_row("09999999", 2.0)]
    # the student's choice for every course
    choices = {"01040066": "replace:01040166", "03940800": Category.SPORT, "03240900": Category.MALAG, "09999999": "ignore"}
    # we run the function
    assigned_points, replacement_points = build_assignment(rows, choices)
    # sport once, and malag
    assert assigned_points == {Category.SPORT: approx(1.0), Category.MALAG: approx(3.0)}
    # the replacement
    assert replacement_points == {"01040166": approx(5.0)}


# the function does not change the lists and dicts it gets
def test_inputs_are_not_changed():
    # two rows, one of them twice
    rows = [make_row("09000011", 2.0), make_row("09000011", 2.0)]
    # one choice
    choices = {"09000011": Category.LIST_A}
    # we run the function
    build_assignment(rows, choices)
    # the rows list still has both rows
    assert len(rows) == 2
    # the choices dict is the same as before
    assert choices == {"09000011": Category.LIST_A}
