#purpous is to Load the 324 courses from data/courses_data.json once, turn each one into a Course (from core/models.py), and let the rest of the program find any course instantly by ID, Hebrew name, or English name(if found)
import json
from core.models import Course


class CourseCatalog:

    @staticmethod
    def normalize(name: str) -> str:
        """
        Normalizes course names for robust exact-match searching.
        Prevents lookup failures caused by extra spaces or different quote characters.
        
        1. Returns empty string if name is empty.
        2. Converts text to lowercase and strips edge spaces.
        3. Removes standard quotes, single quotes, and both types of Hebrew geresh (״ and ׳).
        4. Splits into words and joins with exactly one space to remove extra inner spaces.
        """
        if not name:
            return ""
        
        #we replace all types of quotes and make it lowercase
        clean_name = name.lower().strip().replace('"', '').replace('״', '').replace("'", "").replace('׳', '')
        
        #we remove duplicate spaces between words
        return " ".join(clean_name.split())

    

 #ctor that takes catalog year(this becouse we wanna expand later ion) and source, and course id, hebrew name and english name (if found) and credits, and creates a course object for each course in the database (JSON FILE
    def __init__(self, path: str):
        #the encoding thing is becouse the hebrew names are in hebrew and we need to read them correctly
        with open(path, encoding='utf-8') as f:
            #we read thw whole json file and load it into a python dictionary, so we can access the data easily
            data = json.load(f)
            
        #now we create a list of Course objects from the data in the JSON file, and store it in the courses attribute
        self.catalog_year = data['catalog_year']
        self.source = data['source']
        
        #now we creat dicts to store courses by id, hebrew name and english name, so we can find any course instantly by id, hebrew name or english name
        self.courses_by_id = {}
        self.courses_by_name_he = {}
        self.courses_by_name_en = {}
        
        #we iterate over the courses in the JSON file and create a Course object for each one
        for course_data in data['courses']:
            #we create a Course object from the data in the JSON file
            course = Course(**course_data)
            
            #we check if id is already in the dict, if it is we raise an error, becouse we don't want to have duplicate courses in the catalog
            if course.id in self.courses_by_id:
                raise ValueError(f"Duplicate course id found: {course.id}")
                
            #now we add the course to the dicts, so we can find it by id, hebrew name or english name
            self.courses_by_id[course.id] = course
            
            #we normalize the hebrew name and keep the first one we find to avoid overwriting duplicates accidentally
            norm_he = CourseCatalog.normalize(course.name_he)
            if norm_he not in self.courses_by_name_he:
                self.courses_by_name_he[norm_he] = course
                
            #we only normalize and add the english name if it's not empty, so we don't map all empty strings to the same course
            if course.name_en:
                norm_en = CourseCatalog.normalize(course.name_en)
                self.courses_by_name_en[norm_en] = course

                #method to find course by id
    def get_course_by_id(self, course_id: str) -> Course |None:
        """
        Returns the Course object with the given ID, or None if not found.
        """
        return self.courses_by_id.get(course_id)
    
#a function that is used in UI to find course by he_name or en_name or id
    def find_course_by_name_or_id(self, search_text:str) -> Course |None:
        """
        Returns the Course object with the given Hebrew name, English name, or ID, or None if not found.
        """
        #we normalize the search text to make sure we can find the course even if the user types it differently
        norm_search_text = CourseCatalog.normalize(search_text)
        
        #we first check if the search text is an id, if it is we return the course by id
        if norm_search_text in self.courses_by_id:
            return self.courses_by_id[norm_search_text]
        
        #if it's not an id we check if it's a hebrew name, if it is we return the course by hebrew name
        if norm_search_text in self.courses_by_name_he:
            return self.courses_by_name_he[norm_search_text]
        
        #if it's not a hebrew name we check if it's an english name, if it is we return the course by english name
        if norm_search_text in self.courses_by_name_en:
            return self.courses_by_name_en[norm_search_text]
        
        #if we didn't find the course by id, hebrew name or english name we return None
        return None


    #methode to return all courses in catalog stored by id so all the courses apear at the same order each time for the user
    #the order is by id and we will use lambada for that
    def get_all_courses_sorted_by_id(self) -> list[Course]:
        """
        Returns a list of all Course objects in the catalog, sorted by ID.
        """
        return sorted(list(self.courses_by_id.values()), key=lambda current_course: current_course.id)


    #func to return num of courses in catalog'- used for teting
    def count_courses(self) -> int:
        """
        Returns the number of courses in the catalog.
        """
        return len(self.courses_by_id)

    #func to return if this id in catalog boolean
    def is_course_id_in_catalog(self, course_id: str) -> bool:
        """
        Returns True if the given course ID exists in the catalog, False otherwise.
        """
        return course_id in self.courses_by_id
    