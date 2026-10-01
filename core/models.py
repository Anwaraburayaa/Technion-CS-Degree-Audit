# In this file we define the data models used in the project.
#all modules imports its type from this file, so we can change the implementation of the models without changing the rest of the code.

from dataclasses import dataclass
from enum import Enum


#class Category(Enum):
  #  pass

#this creats a course object for each course in the database (JSON FILE)
#id is 8 digits-name_he is the name of the course in hebrew and name_en is the name of the course in english and credits is the number of points assigned for the course
@dataclass(frozen=True)
class Course:
    id: str
    name_he: str
    name_en: str
    credits: float
