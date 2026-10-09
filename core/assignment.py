#this file turns the student's choices for grade-sheet courses that are not in the catalog
#into the two dicts that run_audit gets: assigned_points and replacement_points
#app.py calls it after the student picks an option for every unknown course
from core.models import Category             
from core.transcript import TranscriptRow     


#we turn the student's choices into points per category and points per replaced mandatory course
#every course id is counted once, even if the grade sheet shows it twice
def build_assignment(unknown_rows: list[TranscriptRow], choices: dict[str, Category | str]) -> tuple[dict[Category, float], dict[str, float]]:
   # we start the two results empty
    assigned_points = {}                        #assigned_points
    replacement_points = {}                     #replacement_points
    seen_ids = set()                            #seen_ids
  
    for row in unknown_rows:
                    #if id is seen we skip  
        if row.course_id in seen_ids:
            continue
        #if not that means this is the first time we see this course id, so we add it to the seen_ids set
        seen_ids.add(row.course_id) 
        #we read choices input from student
        choice = choices.get(row.course_id, "ignore")  #default is ignore if the student did not choose anything
        if choice == "ignore":
            continue
        #if the choice is a category we add the points to the assigned_points dict
        if isinstance(choice, str) and choice.startswith("replace"):
            #that means the student chose to replace a mandatory course with this unknown course, so we add the points to the replacement_points dict
            mandatory_course_id = choice.split(":")[1]  
            replacement_points[mandatory_course_id] = row.points
            continue
        #otherwise its non mandatory course, we add the points to the assigned_points dict
        assigned_points[choice] = assigned_points.get(choice, 0) + row.points
    return assigned_points, replacement_points