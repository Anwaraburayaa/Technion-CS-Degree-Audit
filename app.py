#this is the screen of the project, streamlit runs this file from top to bottom every time the student changes something
#day 4: the student enters the courses he passed in three ways and sees them in one table
#day 5 adds the manual numbers, the unknown courses choice and the audit result
import streamlit as st  #we use streamlit to build the web page
from core.assignment import build_assignment  #we use it to turn the student's choices into points
from core.catalog import CourseCatalog  #we use the catalog to find each course by its number
from core.models import Category  #the manual numbers are saved under the category of their rule
from core.parsing import extract_course_ids  #we use it to read course numbers from pasted text
from core.transcript import read_transcript_rows_from_pdf, split_passed_rows_by_catalog  #we use them to read the grade sheet pdf

#where the course data lives
COURSES_PATH = "data/courses_data.json"
#where the style of the page lives
STYLE_PATH = "assets/style.css"
#the points the whole degree needs, the ruler at the top counts toward it
TOTAL_POINTS = 118.5
#grade-sheet courses that are known to replace a mandatory course: grade-sheet id -> mandatory id
KNOWN_REPLACEMENTS = {"01040066": "01040166", "01040195": "01040031", "02340117": "02340114"}
#the categories the student can give to a grade-sheet course that is not in the catalog
ASSIGNABLE_CATEGORIES = [Category.LIST_A, Category.LIST_B, Category.SPORT, Category.MALAG, Category.FREE_OTHER]
#the text the student sees for every choice except a replacement
CHOICE_LABELS = {"ignore": "Ignore (not counted)", Category.LIST_A: "List A", Category.LIST_B: "List B", Category.SPORT: "Sport", Category.MALAG: "Malag", Category.FREE_OTHER: "Other free elective"}


#we load the catalog once and keep it, so streamlit does not read the json again on every click
@st.cache_resource
def load_catalog() -> CourseCatalog:
    #we read the 324 courses from the json file
    return CourseCatalog(COURSES_PATH)


#we turn a course number into the text shown in the list, like "02340218 · מבני נתונים 1 · Data Structures 1"
def course_label(catalog: CourseCatalog, course_id: str) -> str:
    #we get the course from the catalog
    course = catalog.get_course_by_id(course_id)
    #we start with the number and the hebrew name
    label = f"{course.id} · {course.name_he}"
    #we add the english name only if the course has one
    if course.name_en:
        label += f" · {course.name_en}"
    #we return the full text
    return label


#we turn a choice into the text shown in the dropdown
def choice_label(choice: Category | str) -> str:
    # a replacement, we show which mandatory course it replaces
    if isinstance(choice, str) and choice.startswith("replace:"):
        return f"Replaces mandatory {choice.split(':')[1]}"
    #ignore or a category, we take the text from the dict
    return CHOICE_LABELS[choice]

#we build the blue band at the top: the title, one line about the app, and a ruler of the points entered so far
def hero_html(points: float) -> str:
    #how much of the ruler is filled, never more than the whole ruler
    filled_percent = min(points / TOTAL_POINTS, 1.0) * 100
    #the distance between two ticks of the ruler, one tick every 10 points
    tick_percent = 10 / TOTAL_POINTS * 100
    #the html of the band, the css in assets/style.css gives it its look
    return f"""
    <div class="audit-hero">
        <h1>Technion CS Degree Audit</h1>
        <p>See what you still need to graduate from the 3-year track, catalog 2024/2025 (תשפ"ה).</p>
        <div class="points-ruler" style="--tick: {tick_percent:.3f}%">
            <div class="points-ruler-fill" style="width: {filled_percent:.1f}%"></div>
        </div>
        <div class="points-ruler-caption">
            <span><strong>{points:g}</strong> of {TOTAL_POINTS:g} points from the courses you entered</span>
            <span>A planning tool, the faculty's audit is the official one</span>
        </div>
    </div>
    """


#the title of the browser tab, and a centered page that is easy to read
st.set_page_config(page_title="Technion CS Degree Audit", page_icon="🎓", layout="centered")
#we load our style file and add it to the page
with open(STYLE_PATH, encoding="utf-8") as style_file:
    st.markdown(f"<style>{style_file.read()}</style>", unsafe_allow_html=True)
#an empty place at the top, we fill it with the band at the end, when we know how many points the student entered
hero_place = st.empty()

#we load the catalog (only the first time, then it comes from the cache)
catalog = load_catalog()

#the heading of the input part
st.header("1. Your completed courses")
#we explain that the three ways can be used together
st.write("Use any of the three ways below, or all of them together. The courses from all three are joined.")

#three tabs, one for each way to enter courses
tab_choose, tab_paste, tab_pdf = st.tabs(["Choose from the list", "Paste course numbers", "Upload grade sheet (PDF)"])

#way 1: the student chooses courses from the catalog list
with tab_choose:
    #all course numbers in a fixed order, so the list looks the same every time
    all_course_ids = [course.id for course in catalog.get_all_courses_sorted_by_id()]
    #a list where the student can search and choose many courses, it shows the label but returns the number
    chosen_course_ids = st.multiselect(
        "Search by number or name",
        options=all_course_ids,
        format_func=lambda course_id: course_label(catalog, course_id),
    )

#way 2: the student pastes text with course numbers
with tab_paste:
    #a big text box for the pasted text
    #the paste box does not check grades, so we ask for passed courses only and send grade sheets to the pdf tab
    pasted_text = st.text_area(
        "Paste only courses you passed. For a grade sheet, use the PDF upload, which checks the grades.",
        height=150,
        help="Any format works: one number per line, commas, or a whole copied page. Every 8-digit number is read.",
    )
    #we read every 8 digit number from the text
    pasted_course_ids = extract_course_ids(pasted_text)
    #we keep only the numbers our catalog knows
    pasted_known_ids = {course_id for course_id in pasted_course_ids if catalog.is_course_id_in_catalog(course_id)}
    #the numbers the catalog does not know
    pasted_unknown_ids = pasted_course_ids - pasted_known_ids
    #we tell the student how many numbers we found
    if pasted_course_ids:
        st.write(f"Found {len(pasted_course_ids)} course numbers, {len(pasted_known_ids)} of them are in the catalog.")
    #we warn about the numbers we can not use, so nothing is lost silently
    if pasted_unknown_ids:
        st.warning("Not in the catalog of this track, so they are not counted: " + ", ".join(sorted(pasted_unknown_ids)))

#way 3: the student uploads the grade sheet pdf
with tab_pdf:
    #we tell the student the file is not saved anywhere
    st.write("The file is read only in memory and is not saved.")
    #the upload box, it accepts only pdf files
    uploaded_pdf = st.file_uploader("Grade sheet (תעודת ציונים) as PDF", type="pdf")
    #until a file is uploaded there are no courses from the pdf
    pdf_known_ids = set()
    unknown_rows = []
    #we read the pdf only if the student uploaded one
    if uploaded_pdf is not None:
        #a broken or different pdf should show a message, not crash the page
        try:
            #we read all the course rows, and the lines we could not read
            rows, unreadable_lines = read_transcript_rows_from_pdf(uploaded_pdf)
        except Exception:
            #we tell the student we could not read the file
            st.error("Could not read this PDF. Please upload the grade sheet exactly as downloaded from the Technion.")
            rows, unreadable_lines = [], []
        #we split the passed courses into catalog courses and unknown courses
        pdf_known_ids, unknown_rows = split_passed_rows_by_catalog(rows, catalog)
        #we tell the student what we found
        if rows:
            st.success(f"Read {len(rows)} course rows. {len(pdf_known_ids)} passed courses are in the catalog.")
        #we warn if the pdf had no course rows at all
        elif not unreadable_lines:
            st.warning("No course rows were found in this PDF.")
        #we show the lines we could not read, so the student can add these courses by hand
        if unreadable_lines:
            st.warning("Some lines could not be read. Please add these courses with the list or the paste box:")
            st.code("\n".join(unreadable_lines))
        #we show the passed courses the catalog does not know, the student will choose what they are on day 5
        if unknown_rows:
            st.info("Passed courses that are not in this track's lists (sport, malag, other faculties...). Choose what each one is in section 4 below.")
            st.dataframe(
                [{"Number": row.course_id, "Name": row.name, "Points": row.points, "Grade": row.grade_text} for row in unknown_rows],
                hide_index=True,
            )

#we join the three ways into one set, this is what run_audit will get on day 5
completed_course_ids = set(chosen_course_ids) | pasted_known_ids | pdf_known_ids

#the heading of the table part
st.header("2. Selected courses")
#we show a table only if the student entered courses
if completed_course_ids:
    #one row per course, sorted by number
    selected_rows = []
    for course_id in sorted(completed_course_ids):
        #we get the course to show its names and points
        course = catalog.get_course_by_id(course_id)
        selected_rows.append({"Number": course.id, "Hebrew name": course.name_he, "English name": course.name_en, "Points": course.credits})
    #the table itself
    st.dataframe(selected_rows, hide_index=True, width="stretch")
    #the points of the selected courses, each course counted once
    entered_points = sum(row["Points"] for row in selected_rows)
    #the number of courses and their points
    st.write(f"{len(completed_course_ids)} courses, {entered_points:g} points from the catalog.")
else:
    #no courses yet, so no points yet
    entered_points = 0.0
    #a short hint when nothing is selected yet
    st.info("No courses yet. Choose them from the list, paste their numbers or upload your grade sheet.")

#the heading of the manual part
st.header("3. Manual inputs")
#we explain what these numbers are and when not to type them
st.write("Points the catalog has no course list for. Type only what is not in an uploaded grade sheet, those courses are assigned in the next section.")
#two columns, so the four boxes take less space
left_column, right_column = st.columns(2)
#the left column: sport and malag
with left_column:
    #sport points, the degree needs at least 2
    sport_points = st.number_input("Sport points", min_value=0.0, step=0.5, help="Physical education courses. The degree needs at least 2.")
    #malag points, the degree needs at least 6
    malag_points = st.number_input("Malag points", min_value=0.0, step=0.5, help="General enrichment courses (מל\"ג). The degree needs at least 6.")
#the right column: other free electives and english-taught courses
with right_column:
    #other free elective points, they count only in the general rule and the total
    free_other_points = st.number_input("Other free-elective points", min_value=0.0, step=0.5, help="Free electives that are not sport or malag.")
    #the number of courses taught in english, a count and not points
    english_taught_count = st.number_input("English-taught courses (count)", min_value=0, step=1, help="How many courses you took that were taught in English. The degree needs at least 2.")
#the moved surplus is hidden in a closed box, most students do not need it
with st.expander("Moved surplus (advanced)"):
    #we explain what a moved surplus is and that it does not raise the total
    st.write("Points above a rule's minimum that the faculty lets you move to another rule. They count in that rule only, not in the total, because the course is already counted once.")
    #science points moved here by hand
    science_surplus = st.number_input("Science surplus", min_value=0.0, step=0.5)
    #list a points moved here by hand
    list_a_surplus = st.number_input("List A surplus", min_value=0.0, step=0.5)
    #list b points moved here by hand, for example the extra math above 2.5
    list_b_surplus = st.number_input("List B surplus", min_value=0.0, step=0.5, help="For example the extra math points above 2.5.")
#we put all the typed numbers in one dict, run_audit gets it in step 17
manual_entries = {
    Category.SPORT: sport_points,  #points
    Category.MALAG: malag_points,  #points
    Category.FREE_OTHER: free_other_points,  #points
    Category.ENGLISH_TAUGHT: float(english_taught_count),  #a count, saved as a float like the others
    Category.SCIENCE: science_surplus,  #moved surplus, not in the total
    Category.LIST_A: list_a_surplus,  #moved surplus, not in the total
    Category.LIST_B: list_b_surplus,  #moved surplus, not in the total
}

#the heading of the part for grade-sheet courses that are not in the catalog
st.header("4. Grade-sheet courses not in the catalog")
#the student's choice for every course id, empty when there is no pdf
choices = {}
#we show the dropdowns only if the grade sheet has such courses
if unknown_rows:
    #we tell the student what to do
    st.write("Choose what each course is. Courses left on Ignore are not counted.")
    #the ids that already got a dropdown
    seen_ids = set()
    #one dropdown for every course id
    for row in unknown_rows:
        #a course passed twice gets one dropdown
        if row.course_id in seen_ids:
            continue
        #we remember this id
        seen_ids.add(row.course_id)
        #the normal options, ignore first so it is chosen at the start
        options = ["ignore"] + ASSIGNABLE_CATEGORIES
        #a known replacement goes first, so it is chosen at the start
        if row.course_id in KNOWN_REPLACEMENTS:
            options = ["replace:" + KNOWN_REPLACEMENTS[row.course_id]] + options
        #the dropdown, the hebrew name is last so the browser keeps the order of the numbers
        choices[row.course_id] = st.selectbox(f"{row.course_id} · {row.points:g} pts · {row.name}", options, format_func=choice_label)
else:
    #no such courses, we say so
    st.info("No grade-sheet courses outside the catalog. Upload a grade sheet in section 1 to see them here.")
#we turn the choices into points, this works also when there are no choices
assigned_points, replacement_points = build_assignment(unknown_rows, choices)
#a replaced mandatory course counts as done in the mandatory rule
for mandatory_id in replacement_points:
    completed_course_ids.add(mandatory_id)

#now we know the points, so we fill the band at the top of the page
hero_place.markdown(hero_html(entered_points), unsafe_allow_html=True)


