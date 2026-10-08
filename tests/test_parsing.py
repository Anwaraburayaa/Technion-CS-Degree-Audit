#tests for core/parsing.py, the func that reads course numbers from pasted text
from core.parsing import extract_course_ids


#we check that the numbers are found inside a normal sentence
def test_finds_course_ids_inside_a_sentence():
    assert extract_course_ids("I did 02340218 and 02340114 last year") == {"02340218", "02340114"}


#we check that a number pasted twice is returned once
def test_a_repeated_course_id_is_returned_once():
    assert extract_course_ids("02340218 02340218, 02340218") == {"02340218"}


#we check the usual ways to paste a list: one per line, commas, tabs
def test_finds_course_ids_one_per_line_and_with_commas():
    assert extract_course_ids("02340218\n02340114,02340124\t02340125") == {"02340218", "02340114", "02340124", "02340125"}


#we check that 9 digits and 7 digits are not course numbers, and no 8 digits are taken from inside them
def test_numbers_that_are_not_8_digits_are_ignored():
    assert extract_course_ids("123456789 and 1234567") == set()


#we check that a number touching hebrew or english letters is still found
def test_finds_a_course_id_that_touches_letters():
    assert extract_course_ids("מבני נתונים02340218x") == {"02340218"}


#we check that the leading zero is kept, so the number still matches the catalog
def test_course_ids_are_strings_that_keep_the_leading_zero():
    assert extract_course_ids("01040031") == {"01040031"}


#we check that empty text and text without numbers give an empty set
def test_empty_text_and_text_without_numbers_give_an_empty_set():
    assert extract_course_ids("") == set()
    assert extract_course_ids("no courses here") == set()
