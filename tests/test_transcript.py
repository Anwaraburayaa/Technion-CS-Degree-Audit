"""Tests for core/transcript.py (reading a Technion grade sheet).

All rows here are made up: fake course numbers, fake names, fake grades. No real grade sheet
is stored in the project. The lines are written the way the PDF library returns them: every
Hebrew word is backwards, numbers are normal, and the columns are separated by many spaces.

Reading a real PDF file is NOT covered here, because a real grade sheet holds personal data.
That part was checked by hand on one real file.

Run from the project folder with:  ./run_tests.sh
"""
import json                                         # to write the fake course file

from core.catalog import CourseCatalog              # the class that loads courses
from core.transcript import TranscriptRow           # one course row of a grade sheet
from core.transcript import fix_reversed_hebrew     # turns backwards Hebrew into normal text
from core.transcript import is_row_passed           # says if a row counts as passed
from core.transcript import parse_transcript_line   # turns one text line into a TranscriptRow
from core.transcript import split_passed_rows_by_catalog  # splits passed courses into known and unknown


# --------------------------------------------------------------------------------------
# Helper that builds one line in the shape of a real grade sheet row
# --------------------------------------------------------------------------------------

def make_line(grade, points, name_backwards, course_id):
    """Build one text line shaped like a course row of the grade sheet.

    Args:
        grade: The grade column as it comes from the PDF (a number, or backwards Hebrew words).
        points: The points column as text, for example "3" or "3.5".
        name_backwards: The course name with every Hebrew word backwards.
        course_id: The 8-digit course number.

    Returns:
        A line with the columns in page order: semester, grade, points, name, course number.
    """
    semester = 'ה"פשת  ביבא  2024-2025'             # a semester as the PDF gives it: year, season, years
    return f"     {semester}          {grade}          {points}          {name_backwards}          {course_id}"  # many spaces between columns


# --------------------------------------------------------------------------------------
# fix_reversed_hebrew
# --------------------------------------------------------------------------------------

def test_fix_reversed_hebrew_turns_words_back():
    assert fix_reversed_hebrew("רבוע") == "עובר"    # one backwards word
    assert fix_reversed_hebrew("דוקינ םע רוטפ") == "פטור עם ניקוד"  # three words: letters and word order are both fixed


def test_fix_reversed_hebrew_keeps_numbers_and_english_as_they_are():
    assert fix_reversed_hebrew("12 סרוק") == "קורס 12"  # 12 must not become 21
    assert fix_reversed_hebrew("VLSI ל אובמ") == "מבוא ל VLSI"  # an English word must not be reversed


# --------------------------------------------------------------------------------------
# parse_transcript_line
# --------------------------------------------------------------------------------------

def test_parse_line_with_a_numeric_grade():
    row = parse_transcript_line(make_line("85", "5", "המגודל סרוק", "00000001"))  # a normal row
    assert row == TranscriptRow(course_id="00000001", name="קורס לדוגמה", points=5.0, grade_text="85")  # all four parts


def test_parse_line_keeps_half_points():
    row = parse_transcript_line(make_line("70", "3.5", "המגודל סרוק", "00000002"))  # a course of 3.5 points
    assert row.points == 3.5                        # 3.5 must not become 3


def test_parse_line_with_pass_without_a_number():
    row = parse_transcript_line(make_line("רבוע", "5.5", "המגודל סרוק", "00000003"))  # the grade is the word "pass"
    assert row.grade_text == "עובר"                 # the word is turned back to normal


def test_parse_line_with_exemption_with_points():
    row = parse_transcript_line(make_line("דוקינ םע רוטפ", "3", "המגודל סרוק", "00000004"))  # exemption that gives points
    assert row.grade_text == "פטור עם ניקוד"        # three words, in the right order
    assert row.points == 3.0                        # the points are read


def test_parse_line_with_exemption_without_points():
    row = parse_transcript_line(make_line("דוקינ אלל רוטפ", "0", "המגודל סרוק", "00000005"))  # exemption with 0 points
    assert row.grade_text == "פטור ללא ניקוד"       # the words are read
    assert row.points == 0.0                        # zero points


def test_parse_line_with_a_number_inside_the_course_name():
    row = parse_transcript_line(make_line("90", "3", "12 סרוק", "00000006"))  # the name on the page is "קורס 12"
    assert row.name == "קורס 12"                    # the number in the name is not taken as the points
    assert row.points == 3.0                        # the points column is still 3


def test_parse_line_returns_none_for_lines_that_are_not_course_rows():
    assert parse_transcript_line("") is None        # an empty line
    assert parse_transcript_line("      רטסמס          ןויצ          דוקינ          עוצקמ") is None  # the table header
    assert parse_transcript_line("  123456789 :.ז.ת המגודל טנדוטס לש םינויצ תדועת") is None  # the title line with a 9-digit ID number
    assert parse_transcript_line("2 ךותמ 1 דומע") is None  # the page number line


# --------------------------------------------------------------------------------------
# is_row_passed
# --------------------------------------------------------------------------------------

def make_row(grade_text, course_id="00000001", points=3.0):
    """Build a TranscriptRow with a given grade, for the tests below.

    Args:
        grade_text: The grade column as normal text.
        course_id: The course number (a default is given because most tests do not care).
        points: The points of the course.

    Returns:
        A TranscriptRow with a made-up name.
    """
    return TranscriptRow(course_id=course_id, name="קורס לדוגמה", points=points, grade_text=grade_text)  # only the grade matters


def test_grade_of_55_or_more_is_passed():
    assert is_row_passed(make_row("55")) is True    # exactly the passing grade
    assert is_row_passed(make_row("100")) is True   # the highest grade


def test_grade_below_55_is_not_passed():
    assert is_row_passed(make_row("54")) is False   # one below the passing grade
    assert is_row_passed(make_row("0")) is False    # the lowest grade


def test_pass_word_and_exemption_with_points_are_passed():
    assert is_row_passed(make_row("עובר")) is True  # pass without a number
    assert is_row_passed(make_row("פטור עם ניקוד")) is True  # exemption that gives points


def test_exemption_without_points_is_not_counted():
    assert is_row_passed(make_row("פטור ללא ניקוד")) is False  # it gives no points, so it is not counted


def test_unknown_grade_word_is_not_counted():
    assert is_row_passed(make_row("לא השלים")) is False  # a word we do not know never counts as passed


# --------------------------------------------------------------------------------------
# split_passed_rows_by_catalog
# --------------------------------------------------------------------------------------

def create_catalog_with_two_courses(tmp_path):
    """Write a fake course file with two courses and return a CourseCatalog loaded from it.

    Args:
        tmp_path: The temporary folder pytest gives each test.

    Returns:
        A CourseCatalog that knows only the courses 00000001 and 00000002.
    """
    fake_file = tmp_path / "courses.json"           # the fake file inside the temp folder
    fake_data = {                                   # same shape as data/courses_data.json
        "catalog_year": "TEST-YEAR",                # any text
        "source": "TEST-SOURCE",                    # any text
        "courses": [                                # two made-up courses
            {"id": "00000001", "name_he": "קורס א", "name_en": "", "credits": 3.0},  # the first known course
            {"id": "00000002", "name_he": "קורס ב", "name_en": "", "credits": 3.5},  # the second known course
        ],
    }
    with open(fake_file, "w", encoding="utf-8") as f:  # utf-8 so Hebrew is written correctly
        json.dump(fake_data, f, ensure_ascii=False)    # write the fake courses as JSON
    return CourseCatalog(str(fake_file))            # load them with the real class


def test_split_puts_passed_catalog_courses_in_the_set(tmp_path):
    catalog = create_catalog_with_two_courses(tmp_path)  # knows 00000001 and 00000002
    rows = [make_row("80", "00000001"), make_row("עובר", "00000002")]  # both passed, both in the catalog
    known_course_ids, unknown_rows = split_passed_rows_by_catalog(rows, catalog)  # split them
    assert known_course_ids == {"00000001", "00000002"}  # both are ready for the audit
    assert unknown_rows == []                       # nothing for the student to decide


def test_split_leaves_out_failed_courses(tmp_path):
    catalog = create_catalog_with_two_courses(tmp_path)  # knows 00000001 and 00000002
    rows = [make_row("40", "00000001"), make_row("90", "00000002")]  # the first one is failed
    known_course_ids, unknown_rows = split_passed_rows_by_catalog(rows, catalog)  # split them
    assert known_course_ids == {"00000002"}         # the failed course is not counted


def test_split_counts_a_course_once_when_it_was_failed_and_then_passed(tmp_path):
    catalog = create_catalog_with_two_courses(tmp_path)  # knows 00000001 and 00000002
    rows = [make_row("40", "00000001"), make_row("75", "00000001")]  # the same course: failed, then passed
    known_course_ids, unknown_rows = split_passed_rows_by_catalog(rows, catalog)  # split them
    assert known_course_ids == {"00000001"}         # it is in the set, and a set holds it once


def test_split_puts_passed_courses_outside_the_catalog_in_the_list(tmp_path):
    catalog = create_catalog_with_two_courses(tmp_path)  # does not know 00000009
    outside_row = make_row("95", "00000009", points=2.0)  # passed, worth 2 points, not in the catalog
    known_course_ids, unknown_rows = split_passed_rows_by_catalog([outside_row], catalog)  # split it
    assert known_course_ids == set()                # nothing goes to the audit by itself
    assert unknown_rows == [outside_row]            # the student decides what this course is


def test_split_drops_courses_outside_the_catalog_that_have_no_points(tmp_path):
    catalog = create_catalog_with_two_courses(tmp_path)  # does not know 00000008 and 00000009
    rows = [                                        # two rows the student has nothing to decide about
        make_row("עובר", "00000008", points=0.0),   # passed, but worth 0 points
        make_row("פטור ללא ניקוד", "00000009", points=0.0),  # exemption without points
    ]
    known_course_ids, unknown_rows = split_passed_rows_by_catalog(rows, catalog)  # split them
    assert known_course_ids == set()                # none is in the catalog
    assert unknown_rows == []                       # none is shown to the student
