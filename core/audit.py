#this is the base of the search engine in our project
"It is the calculation engine of the project. It contains only functions that calculate. "
"It shows nothing on screen and it never imports Streamlit, for two reasons: "
"it can be tested with pytest alone, and the same engine could later serve a different interface."
import json                                     # reads data/requirements.json and turns it into a Python dict
from core.catalog import CourseCatalog          # the Day 1 class that turns a course number into a Course object
from core.models import AuditResult, Category   # the result object the engine returns, and the Enum of rule names

#this func gets the path file  and returns it as a dict
def load_requirements_from_file(path: str) -> dict:
    with open(path,"r", encoding='utf-8') as f:
        data = json.load(f) 
        for rule in data["rules"]:
            Category(rule["key"])  # validate that the category is a valid enum member
        return data


  #this func gets one rule of kind required_courses and the set of course ids that the student finished
#it returns the list of course ids from this rule that the student still did not do
#if the student already did enough courses for the rule (needed or more) it returns an empty list
#it is used only for the rules that name exact courses (mandatory, the two pairs, extra math), not for the points rules
def find_missing_course_ids(rule: dict, completed_course_ids: set[str]) -> list[str]:
    #the course ids that belong to this rule, as written in the json file
    rule_course_ids = rule["courses"]
    #how many of these courses the student must finish
    needed_courses_count = rule["needed"]
    #we count how many courses of this rule the student already finished
    completed_courses_count = 0
    for course_id in rule_course_ids:
        #if this course is in the set of finished courses we count it
        if course_id in completed_course_ids:
            completed_courses_count += 1
    #if the student finished enough courses the rule is done, so nothing is missing
    if completed_courses_count >= needed_courses_count:
        return []
    else:
        #the rule is not done, so we collect the courses of the rule that the student did not finish
        missing_course_ids = []
        for course_id in rule_course_ids:
            #if this course is not in the set of finished courses it is missing
            if course_id not in completed_course_ids:
                missing_course_ids.append(course_id)
        return missing_course_ids

#this func calc needed courses number minus completed courses number of the rules
#used for none mandatory courses we only show num of points left for these categorys
def count_remaining_courses(rule: dict, completed_course_ids: set[str]) -> int:
    #the course ids that belong to this rule, as written in the json file
    rule_course_ids = rule["courses"]
    #how many of these courses the student must finish
    needed_courses_count = rule["needed"]
    #we count how many courses of this rule the student already finished
    completed_courses_count = 0
    for course_id in rule_course_ids:
        #if this course is in the set of finished courses we count it
        if course_id in completed_course_ids:
            completed_courses_count += 1
    #the remaining courses is the needed minus the completed, if negative we return 0
    remaining_courses_count = needed_courses_count - completed_courses_count
    return max(remaining_courses_count, 0)
   
 