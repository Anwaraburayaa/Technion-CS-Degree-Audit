#this file reads a technion grade sheet (the signed pdf "תעודת ציונים") and tells us which courses the student passed
#it is used by the ui when the student uploads the pdf instead of typing the course numbers
#the audit itself (core/audit.py) does not know this file, it only gets the set of course ids at the end
import re
from dataclasses import dataclass

import pypdf

from core.catalog import CourseCatalog

#the lowest numeric grade that counts as a pass, it is printed at the bottom of every grade sheet
PASSING_GRADE = 55
#the words in the grade column that count as a pass
PASSING_WORDS = ["עובר", "פטור עם ניקוד"]

#one table row of the grade sheet looks like this, from left to right on the page:
#semester (3 words) | grade | points | course name | course number (8 digits)
ROW_PATTERN = re.compile(
    r"^\s*\S+\s+\S+\s+\d{4}-\d{4}"       #the semester: hebrew year, season, years like 2024-2025
    r"\s{2,}(?P<grade>.+?)"              #the grade: a number or hebrew words
    r"\s{2,}(?P<points>\d+(?:\.\d+)?)"   #the points: 3 or 3.5
    r"\s{2,}(?P<name>.+?)"               #the course name
    r"\s{2,}(?P<course_id>\d{8})\s*$"    #the course number at the end of the line
)


#one course row of the grade sheet
#course_id is the 8 digit number, name is the hebrew name, points is the "ניקוד" column
#grade_text is the "ציון" column as text: a number like "85" or words like "עובר"
@dataclass(frozen=True)
class TranscriptRow:
    course_id: str
    name: str
    points: float
    grade_text: str


#the pdf gives hebrew text in the order it is drawn on the page, so every hebrew word comes out backwards
#this func turns it back to normal text
#1. reverse the whole text
#2. numbers and english words were fine before, so reverse each of them back
def fix_reversed_hebrew(text: str) -> str:
    #1. the whole text backwards
    reversed_text = text[::-1]
    #2. every run of digits, dots or english letters is turned back
    return re.sub(r"[0-9A-Za-z.]+", lambda match: match.group()[::-1], reversed_text)


#this func gets one text line of the grade sheet and returns a TranscriptRow, or None if the line is not a course row
#1. check that the line has the shape of a course row
#2. read the four parts and fix the hebrew ones
def parse_transcript_line(line: str) -> TranscriptRow | None:
    #1. lines like the title, the page number or the signature do not match
    match = ROW_PATTERN.match(line)
    if match is None:
        return None
    #2. a grade that is a number stays as it is, hebrew words are turned back to normal
    grade_text = match.group("grade").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", grade_text):
        grade_text = fix_reversed_hebrew(grade_text)
    return TranscriptRow(
        course_id=match.group("course_id"),
        name=fix_reversed_hebrew(match.group("name").strip()),
        points=float(match.group("points")),
        grade_text=grade_text,
    )


#this func reads the pdf and returns two lists: the course rows, and the lines that look like a course row but could not be read
#pdf_file is a path or an uploaded file
#1. read the text of every page, line by line, in the same layout as on the page
#2. turn each line into a TranscriptRow
#3. a line that ends with a course number but is not a row is kept in the second list, so the ui can warn the student
def read_transcript_rows_from_pdf(pdf_file) -> tuple[list[TranscriptRow], list[str]]:
    rows = []
    unreadable_lines = []
    #1. layout mode keeps every table row on one line
    reader = pypdf.PdfReader(pdf_file)
    for page in reader.pages:
        for line in page.extract_text(extraction_mode="layout").split("\n"):
            #2. try to read the line as a course row
            row = parse_transcript_line(line)
            if row is not None:
                rows.append(row)
            #3. it has a course number at the end but we could not read it
            elif re.search(r"\s\d{8}\s*$", line):
                unreadable_lines.append(line.strip())
    return rows, unreadable_lines


#this func says if the student passed the course of this row
#1. a number passes when it is 55 or more
#2. words pass only if they are "עובר" or "פטור עם ניקוד"
#an exemption without points ("פטור ללא ניקוד") and any word we do not know are not counted
def is_row_passed(row: TranscriptRow) -> bool:
    #1. the grade is a number
    if re.fullmatch(r"\d+(?:\.\d+)?", row.grade_text):
        return float(row.grade_text) >= PASSING_GRADE
    #2. the grade is words
    return row.grade_text in PASSING_WORDS


#this func splits the passed courses into the ones our catalog knows and the ones it does not know
#it returns a set of course ids (ready for run_audit) and a list of rows (for the student to decide what they are)
#1. skip the rows that are not passed
#2. a course that is in the catalog goes to the set
#3. a course that is not in the catalog goes to the list, but only if it has points
def split_passed_rows_by_catalog(rows: list[TranscriptRow], catalog: CourseCatalog) -> tuple[set[str], list[TranscriptRow]]:
    known_course_ids = set()
    unknown_rows = []
    for row in rows:
        #1. failed courses and exemptions without points are not counted
        if not is_row_passed(row):
            continue
        #2. the catalog knows this course
        if catalog.is_course_id_in_catalog(row.course_id):
            known_course_ids.add(row.course_id)
        #3. the catalog does not know it, and it is worth points
        elif row.points > 0:
            unknown_rows.append(row)
    return known_course_ids, unknown_rows
