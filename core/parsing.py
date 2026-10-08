import re

#a course number is exactly 8 digits that do not touch another digit
COURSE_ID_PATTERN =re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
#we find every course number in the pasted text and return them without repeats
#this is needed so the student can paste a list instead of choosing the courses one by one
def extract_course_ids(text: str) -> set[str]:
    #we find all course number in texr using regex and return them as a set
    return set(COURSE_ID_PATTERN.findall(text))
