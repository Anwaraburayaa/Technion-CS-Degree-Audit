#this is the screen of the project, streamlit runs this file from top to bottom every time the student changes something
#day 4: the student enters the courses he passed in three ways and sees them in one table
#day 5 adds the manual numbers, the unknown courses choice and the audit result
import streamlit as st  #we use streamlit to build the web page

from core.catalog import CourseCatalog  #we use the catalog to find each course by its number
from core.parsing import extract_course_ids  #we use it to read course numbers from pasted text
from core.transcript import read_transcript_rows_from_pdf, split_passed_rows_by_catalog  #we use them to read the grade sheet pdf

#where the course data lives
COURSES_PATH = "data/courses_data.json"
#where the style of the page lives
STYLE_PATH = "assets/style.css"
#the points the whole degree needs, the ruler at the top counts toward it
TOTAL_POINTS = 118.5


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
    pasted_text = st.text_area("Paste course numbers (any format: one per line, commas, or a whole copied page)", height=150)
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
            st.info("Passed courses that are not in this track's lists (sport, malag, other faculties...). You will choose what each one is in the next step.")
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

#now we know the points, so we fill the band at the top of the page
hero_place.markdown(hero_html(entered_points), unsafe_allow_html=True)
