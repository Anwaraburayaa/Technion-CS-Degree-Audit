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