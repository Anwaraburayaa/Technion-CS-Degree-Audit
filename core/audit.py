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


   #func for siecnce chaic req that checks if the student has finished the sci chain he chose
def is_chain_complete(rule: dict, completed_course_ids: set[str]) -> bool:
    for option in rule["options"]:
        #check if all courses in this option are completed
        if all(course_id in completed_course_ids for course_id in option["courses"]):
            return True
    return False 

#func for manual entrys put by ueser
#it validates that the user put a valid  non negative num
def check_manual_entries(manual_entries: dict[Category, float]) -> None:
    """
    Validates manual credit entries.
    
    Iterates through each category-points pair. If any points value
    is below zero, immediately raises a ValueError identifying the category.
    Zero points are permitted.
    """
    #  Iterate over each (key, value) pair in the dictionary
    for category, points in manual_entries.items():
        
        # Check if the numerical value is negative
        if points < 0:
            raise ValueError(
                f"Manual entry for {category.value} cannot be negative: {points}"
            )


#the main func of the audit, the ui calls only this one
#it checks every rule and returns one AuditResult
def run_audit(requirements: dict, catalog: CourseCatalog, completed_course_ids: set[str], manual_entries: dict[Category, float]) -> AuditResult:
    # stop here if a manual number is negative
    check_manual_entries(manual_entries)
    #the two result dicts, we fill them in the loop
    missing_courses_by_category = {}
    remaining_by_category = {}
    # we iterate over the rules
    for rule in requirements["rules"]:
        # the rule key as a Category, it is the key of both dicts
        category = Category(rule["key"])
        # rules that name exact courses
        if rule["kind"] == "required_courses":
            #we get the missing ids and turn each one into a Course
            missing_course_ids = find_missing_course_ids(rule, completed_course_ids)
            missing_courses = []
            for course_id in missing_course_ids:
                missing_courses.append(catalog.get_course_by_id(course_id))
            #we save the missing courses and how many remain
            missing_courses_by_category[category] = missing_courses
            remaining_by_category[category] = count_remaining_courses(rule, completed_course_ids)
        # the science chain rule
        elif rule["kind"] == "one_complete_option":
            #0 if one option is complete, 1 if not
            if is_chain_complete(rule, completed_course_ids):
                remaining_by_category[category] = 0
            else:
                remaining_by_category[category] = 1
    #we return the result
    return AuditResult(missing_courses_by_category, remaining_by_category)




#this func returns how many points the student has in one points rule (science, list_a or list_b)
#it adds the points of the completed courses of the rule, without the excluded courses
#manual points are not added here, run_audit adds them

def sum_completed_points(rule: dict, completed_course_ids: set[str], excluded_course_ids: set[str], catalog: CourseCatalog) -> float:
   total_points = 0.0
   for course_id in rule["courses"]:
       # skip a course the student did not complete
       if course_id not in completed_course_ids:
           continue
       #skip a course that is excluded from this rule
       if course_id in excluded_course_ids:
           continue
       #add the points of the course from the catalog
       course = catalog.get_course_by_id(course_id)
       if course is not None:
           total_points += course.credits
   # return the total
   return total_points


#some courses are written in list a or list b but must not count there directly:
#a mandatory course never counts in list a or b, for example 02360360 compilation is printed in list a but it is mandatory
#(only if a student did both compilation and computer architecture, the second one counts in list a, this is not handled yet)
#a science or extra math course counts in list b only through its surplus (above 8 or above 2.5 points), also not handled yet
#the rule only names these rules in "exclude_rules", this func turns the names into course ids so sum_completed_points skips them
def collect_excluded_course_ids(rule: dict, requirements: dict) -> set[str]:
    #intialize an empty set
    excluded_course_ids = set()

    #get the names of the excluded rules, or an empty list
    exclude_rule_keys = rule.get("exclude_rules", [])
    #go over all the rules of the degree
    for other_rule in requirements["rules"]:
        #if a rule is excluded, add all its courses to the set
        if other_rule["key"] in exclude_rule_keys:
            excluded_course_ids.update(other_rule["courses"])
    #return the set
    return excluded_course_ids


#returns how much is still missing in one category: the minimum it requires minus what the student has
#0 means done
#used for every points category, for the english courses count, and for the degree total
def count_remaining_points(minimum: float, have: float) -> float:
    remaining = minimum - have
    return max(remaining, 0.0)

#some courses count in a rule only if the student also did another course
#in our catalog  01040135 (ode) counts as the extra math course only together with 01140073, 01150203, 01240400 or 01140101
#this func returns the completed courses as this rule should see them: a course whose condition is not met is removed
def filter_conditional_courses(rule: dict, completed_course_ids: set[str]) -> set[str]:
    #we copy the completed courses because we dont want to change the original set, all the rules use it
    completed_courses_copy = set(completed_course_ids)
    #we get the conditions of the rule, or an empty dict if the rule has none
    rule_conditions = rule.get("conditional_courses", {})
    #we iterate over the conditional courses and their condition courses
    for course_id, condition_course_ids in rule_conditions.items():
        #we check if the student did none of the condition courses
        if not any(condition_course_id in completed_course_ids for condition_course_id in condition_course_ids):
            #the condition is not met, so we remove the course from the copy
            completed_courses_copy.discard(course_id)
    #we return the copy
    return completed_courses_copy

        