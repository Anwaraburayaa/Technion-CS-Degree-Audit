#this is the screen of the project, streamlit runs this file from top to bottom every time the student changes something
#day 4: the student enters the courses he passed in three ways and sees them in one table
#day 5 adds the manual numbers, the unknown courses choice, the audit result, and a switch between english and hebrew
import streamlit as st  #we use streamlit to build the web page

from app_texts import LANGUAGES, RULE_LABELS_HE, TEXTS  #every text of the page, in english and in hebrew
from core.assignment import build_assignment  #we use it to turn the student's choices into points
from core.audit import count_surplus_points, load_requirements_from_file, run_audit  #we use them to load the rules, run the audit and show what moved
from core.catalog import CourseCatalog  #we use the catalog to find each course by its number
from core.models import Category  #the manual numbers are saved under the category of their rule
from core.parsing import extract_course_ids  #we use it to read course numbers from pasted text
from core.transcript import read_transcript_rows_from_pdf, split_passed_rows_by_catalog  #we use them to read the grade sheet pdf

#where the course data lives
COURSES_PATH = "data/courses_data.json"
#where the degree rules live
REQUIREMENTS_PATH = "data/requirements.json"
#where the style of the page lives
STYLE_PATH = "assets/style.css"
#the points the whole degree needs, the ruler at the top counts toward it
TOTAL_POINTS = 118.5
#grade-sheet courses that are known to replace a mandatory course: grade-sheet id -> mandatory id
KNOWN_REPLACEMENTS = {"01040066": "01040166", "01040195": "01040031", "02340117": "02340114"}
#the categories the student can give to a grade-sheet course that is not in the catalog
ASSIGNABLE_CATEGORIES = [Category.LIST_A, Category.LIST_B, Category.SPORT, Category.MALAG, Category.FREE_OTHER]
#the key of the text of every choice except a replacement, the text itself comes from app_texts.py in the chosen language
CHOICE_TEXT_KEYS = {"ignore": "choice_ignore", Category.LIST_A: "choice_list_a", Category.LIST_B: "choice_list_b", Category.SPORT: "choice_sport", Category.MALAG: "choice_malag", Category.FREE_OTHER: "choice_free_other"}


#we load the catalog once and keep it, so streamlit does not read the json again on every click
@st.cache_resource
def load_catalog() -> CourseCatalog:
    #we read the 323 courses from the json file
    return CourseCatalog(COURSES_PATH)


#we load the 13 rules once and keep them, so streamlit does not read the json again on every click
@st.cache_resource
def load_requirements() -> dict:
    #we read the rules and the 118.5 total from the json file
    return load_requirements_from_file(REQUIREMENTS_PATH)


#we get one text in the chosen language, and put the values in its {names}
def t(key: str, **values) -> str:
    #the text of this key in the chosen language, with the values filled in
    return TEXTS[language][key].format(**values)


#we turn the columns of a table around in hebrew, the table draws the first column on the left, and hebrew reads from the right
def table_rows(rows: list[dict]) -> list[dict]:
    #in english the rows stay as they are
    if language != "he":
        return rows
    #in hebrew every row gets its columns in the opposite order
    return [dict(reversed(list(row.items()))) for row in rows]


#we get the name of a rule in the chosen language
def rule_label(rule: dict) -> str:
    #the science points and the chain are shown as one rule, the science chain
    if rule["key"] == "science":
        return t("science_chain_label")
    #in hebrew we use our own names, in english the label from data/requirements.json
    if language == "he":
        return RULE_LABELS_HE.get(rule["key"], rule["label"])
    #the english label
    return rule["label"]


#we turn what is missing in one rule into words, the unit depends on the kind of rule
def missing_text(rule: dict, remaining: float) -> str:
    #a rule that names courses, and english-taught courses, count courses
    if rule["kind"] in ("required_courses", "manual_count"):
        return t("one_course") if remaining == 1 else t("n_courses", n=f"{remaining:g}")
    #the science chain is done or not done
    if rule["kind"] == "one_complete_option":
        return t("a_chain")
    #all the other rules count points
    return t("n_points", n=f"{remaining:g}")


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
        return f"{t('replaces_mandatory')} {choice.split(':')[1]}"
    #ignore or a category, we take the text from the dict
    return t(CHOICE_TEXT_KEYS[choice])


#we build the blue band at the top: the title, one line about the app, and a ruler of the points counted so far
def hero_html(points: float) -> str:
    #how much of the ruler is filled, never more than the whole ruler
    filled_percent = min(points / TOTAL_POINTS, 1.0) * 100
    #the distance between two ticks of the ruler, one tick every 10 points
    tick_percent = 10 / TOTAL_POINTS * 100
    #the html of the band, the css in assets/style.css gives it its look
    return f"""
    <div class="audit-hero">
        <h1>{t("hero_title")}</h1>
        <p>{t("hero_subtitle")}</p>
        <div class="points-ruler" style="--tick: {tick_percent:.3f}%">
            <div class="points-ruler-fill" style="width: {filled_percent:.1f}%"></div>
        </div>
        <div class="points-ruler-caption">
            <span>{t("hero_points", points=f"{points:g}", total=f"{TOTAL_POINTS:g}")}</span>
            <span>{t("hero_note")}</span>
        </div>
    </div>
    """


#the title of the browser tab, and a centered page that is easy to read
st.set_page_config(page_title="Technion CS Degree Audit", page_icon="🎓", layout="centered")
#we load our style file and add it to the page
with open(STYLE_PATH, encoding="utf-8") as style_file:
    st.markdown(f"<style>{style_file.read()}</style>", unsafe_allow_html=True)

#the language switch at the top right, a small column next to an empty wide one
_, language_column = st.columns([3, 1])
#the switch shows "English" and "עברית", english is chosen at the start
with language_column:
    language_name = st.segmented_control("Language", list(LANGUAGES), default="English", key="language", label_visibility="collapsed")
#clicking the chosen option again leaves nothing chosen, then we stay in english
language = LANGUAGES.get(language_name, "en")
#hebrew is read from right to left, so the whole page turns
if language == "he":
    st.markdown(
        "<style>"
        ".stMainBlockContainer, .block-container { direction: rtl; }"
        "[data-testid='stMarkdownContainer'], [data-testid='stMarkdownContainer'] *, [data-testid='stHeading'], [data-testid='stHeading'] *, .audit-hero, .audit-hero * { text-align: right !important; }"
        "[data-testid='stCaptionContainer'], [data-testid='stCaptionContainer'] * { text-align: right !important; }"
        "[data-testid='stMetricValue'] { direction: ltr; text-align: right; }"
        ".result-banner { border-left-width: 0; border-right-width: 5px; border-right-style: solid; }"
        "</style>",
        unsafe_allow_html=True,
    )

#an empty place at the top, we fill it with the band at the end, when we know how many points the audit counted
hero_place = st.empty()

#we load the catalog (only the first time, then it comes from the cache)
catalog = load_catalog()

#the heading of the input part
st.header(t("s1_header"))
#we explain that the three ways can be used together
st.write(t("s1_intro"))

#three tabs, one for each way to enter courses
tab_choose, tab_paste, tab_pdf = st.tabs([t("tab_choose"), t("tab_paste"), t("tab_pdf")])

#way 1: the student chooses courses from the catalog list
with tab_choose:
    #all course numbers in a fixed order, so the list looks the same every time
    all_course_ids = [course.id for course in catalog.get_all_courses_sorted_by_id()]
    #a list where the student can search and choose many courses, it shows the label but returns the number
    #every input has a key, so what the student entered stays when the language changes
    chosen_course_ids = st.multiselect(
        t("search_label"),
        options=all_course_ids,
        format_func=lambda course_id: course_label(catalog, course_id),
        placeholder=t("search_placeholder"),
        key="chosen_courses",
    )

#way 2: the student pastes text with course numbers
with tab_paste:
    #a big text box for the pasted text
    #the paste box does not check grades, so we ask for passed courses only and send grade sheets to the pdf tab
    pasted_text = st.text_area(t("paste_label"), height=150, help=t("paste_help"), key="pasted_text")
    #we read every 8 digit number from the text
    pasted_course_ids = extract_course_ids(pasted_text)
    #we keep only the numbers our catalog knows
    pasted_known_ids = {course_id for course_id in pasted_course_ids if catalog.is_course_id_in_catalog(course_id)}
    #the numbers the catalog does not know
    pasted_unknown_ids = pasted_course_ids - pasted_known_ids
    #we tell the student how many numbers we found
    if pasted_course_ids:
        st.write(t("paste_found", found=len(pasted_course_ids), known=len(pasted_known_ids)))
    #we warn about the numbers we can not use, so nothing is lost silently
    if pasted_unknown_ids:
        st.warning(t("paste_unknown") + ", ".join(sorted(pasted_unknown_ids)))

#way 3: the student uploads the grade sheet pdf
with tab_pdf:
    #we tell the student the file is not saved anywhere
    st.write(t("pdf_privacy"))
    #the upload box, it accepts only pdf files
    uploaded_pdf = st.file_uploader(t("pdf_label"), type="pdf", key="grade_sheet")
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
            st.error(t("pdf_error"))
            rows, unreadable_lines = [], []
        #we split the passed courses into catalog courses and unknown courses
        pdf_known_ids, unknown_rows = split_passed_rows_by_catalog(rows, catalog)
        #we tell the student what we found
        if rows:
            st.success(t("pdf_read", rows=len(rows), known=len(pdf_known_ids)))
        #we warn if the pdf had no course rows at all
        elif not unreadable_lines:
            st.warning(t("pdf_no_rows"))
        #we show the lines we could not read, so the student can add these courses by hand
        if unreadable_lines:
            st.warning(t("pdf_unreadable"))
            st.code("\n".join(unreadable_lines))
        #we show the passed courses the catalog does not know, the student chooses what they are in section 4
        if unknown_rows:
            st.info(t("pdf_unknown"))
            st.dataframe(
                table_rows([{t("col_number"): row.course_id, t("col_name"): row.name, t("col_points"): row.points, t("col_grade"): row.grade_text} for row in unknown_rows]),
                hide_index=True,
            )

#we join the three ways into one set, this is what run_audit gets
completed_course_ids = set(chosen_course_ids) | pasted_known_ids | pdf_known_ids

#the heading of the table part
st.header(t("s2_header"))
#we show a table only if the student entered courses
if completed_course_ids:
    #one row per course, sorted by number
    selected_rows = []
    for course_id in sorted(completed_course_ids):
        #we get the course to show its names and points
        course = catalog.get_course_by_id(course_id)
        selected_rows.append({t("col_number"): course.id, t("col_name_he"): course.name_he, t("col_name_en"): course.name_en, t("col_points"): course.credits})
    #the table itself
    st.dataframe(table_rows(selected_rows), hide_index=True, width="stretch")
    #the points of the selected courses, each course counted once
    entered_points = sum(row[t("col_points")] for row in selected_rows)
    #the number of courses and their points
    st.write(t("s2_summary", count=len(completed_course_ids), points=f"{entered_points:g}"))
else:
    #no courses yet, so no points yet
    entered_points = 0.0
    #a short hint when nothing is selected yet
    st.info(t("s2_empty"))

#the heading of the manual part
st.header(t("s3_header"))
#we explain what these numbers are and when not to type them
st.write(t("s3_intro"))
#two columns, so the four boxes take less space
left_column, right_column = st.columns(2)
#the left column: sport and malag
with left_column:
    #sport points, the degree needs at least 2
    sport_points = st.number_input(t("sport_label"), min_value=0.0, step=0.5, help=t("sport_help"), key="sport_points")
    #malag points, the degree needs at least 6
    malag_points = st.number_input(t("malag_label"), min_value=0.0, step=0.5, help=t("malag_help"), key="malag_points")
#the right column: other free electives and english-taught courses
with right_column:
    #other free elective points, they count only in the general rule and the total
    free_other_points = st.number_input(t("free_label"), min_value=0.0, step=0.5, help=t("free_help"), key="free_other_points")
    #the number of courses taught in english, a count and not points
    english_taught_count = st.number_input(t("english_label"), min_value=0, step=1, help=t("english_help"), key="english_taught_count")
#the moved surplus is hidden in a closed box, most students do not need it
#we put all the typed numbers in one dict, run_audit gets it
manual_entries = {
    Category.SPORT: sport_points,  #points
    Category.MALAG: malag_points,  #points
    Category.FREE_OTHER: free_other_points,  #points
    Category.ENGLISH_TAUGHT: float(english_taught_count),  #a count, saved as a float like the others
}

#the heading of the part for grade-sheet courses that are not in the catalog
st.header(t("s4_header"))
#the student's choice for every course id, empty when there is no pdf
choices = {}
#how many grade-sheet courses the student marked as taught in english
english_from_grade_sheet = 0
#we show the dropdowns only if the grade sheet has such courses
if unknown_rows:
    #we tell the student what to do
    st.write(t("s4_intro"))
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
        #the choice the student made before, kept apart from the dropdown so it stays when the language changes
        saved_choice = st.session_state.get(f"saved_choice_{row.course_id}", options[0])
        #the dropdown and the "taught in english" box side by side, in one row
        choice_column, english_column = st.columns([4, 1], vertical_alignment="bottom")
        #the dropdown: its key has the language, because its texts change with the language, and it starts on the saved choice
        choice = choice_column.selectbox(
            t("course_option", id=row.course_id, points=f"{row.points:g}", name=row.name),
            options,
            index=options.index(saved_choice) if saved_choice in options else 0,
            format_func=choice_label,
            key=f"choice_{language}_{row.course_id}",
        )
        #we save the choice for the next run, and use it
        st.session_state[f"saved_choice_{row.course_id}"] = choice
        choices[row.course_id] = choice
        #the points of a course go to one category, but the course can also be taught in english: a yes or no next to it
        taught_in_english = english_column.checkbox(t("taught_in_english"), key=f"english_{row.course_id}")
        #an ignored course is not counted at all, also not as english
        if taught_in_english and choice != "ignore":
            english_from_grade_sheet += 1
else:
    #no such courses, we say so
    st.info(t("s4_empty"))
#we turn the choices into points, this works also when there are no choices
assigned_points, replacement_points = build_assignment(unknown_rows, choices)
#the english-taught courses marked in section 4 are added to the number typed in section 3
manual_entries[Category.ENGLISH_TAUGHT] += english_from_grade_sheet
#a replaced mandatory course counts as done in the mandatory rule
for mandatory_id in replacement_points:
    completed_course_ids.add(mandatory_id)

#the heading of the results part
st.header(t("s5_header"))
#the 13 rules and the 118.5 total (only the first time, then from the cache)
requirements = load_requirements()
#we run the audit with everything the student entered in sections 1 to 4
result = run_audit(requirements, catalog, completed_course_ids, manual_entries, replacement_points, assigned_points)
#the points the audit counted, it is what is left after we take the missing points from 118.5
counted_points = TOTAL_POINTS - result.remaining_total_points
#the rules that have a minimum of their own, list b and other free electives have none (they only count inside a sum rule)
#the science chain is shown together with the science points, so it is not counted as a rule of its own here
required_rules = [rule for rule in requirements["rules"] if rule.get("min_points") != 0 and rule["key"] != "science_chain"]
#how many of them are done, 0 means done, and science is done only when its chain is done too
rules_done = sum(1 for rule in required_rules if result.remaining_by_category[Category(rule["key"])] == 0 and (rule["key"] != "science" or result.remaining_by_category[Category.SCIENCE_CHAIN] == 0))
#the number of rules that have a minimum
rules_total = len(required_rules)

#the banner: green when every rule and the total are done, red otherwise
if result.is_eligible_to_graduate:
    #the green banner
    st.markdown(f"<div class='result-banner result-ok'><strong>{t('eligible_title')}</strong><span>{t('eligible_text')}</span></div>", unsafe_allow_html=True)
else:
    #the red banner, with how much is left
    not_eligible_text = t("not_eligible_text", left=rules_total - rules_done, total=rules_total, points=f"{result.remaining_total_points:g}", needed=f"{TOTAL_POINTS:g}")
    st.markdown(f"<div class='result-banner result-missing'><strong>{t('not_eligible_title')}</strong><span>{not_eligible_text}</span></div>", unsafe_allow_html=True)

#three numbers side by side
points_column, missing_column, rules_column = st.columns(3)
#the points counted out of 118.5
points_column.metric(t("metric_counted"), f"{counted_points:g} / {TOTAL_POINTS:g}")
#the points still missing
missing_column.metric(t("metric_missing"), f"{result.remaining_total_points:g}")
#the rules done out of the rules that have a minimum
rules_column.metric(t("metric_rules"), f"{rules_done} / {rules_total}")

#for every rule key, the name of the sum rule it counts in, for example list_b -> "List A + List B"
sum_rule_label = {}
for rule in requirements["rules"]:
    #only the sum rules list other rules
    for part_key in rule.get("rules", []):
        #we remember the name of the sum rule for each of its parts
        sum_rule_label[part_key] = rule_label(rule)

#one table row per rule, in the order of the file
rule_rows = []
for rule in requirements["rules"]:
    #"other free electives" has no minimum and only adds to the free elective rule, so it gets no row of its own
    if rule["key"] == "free_other":
        continue
    #the science chain is shown in the science row
    if rule["key"] == "science_chain":
        continue
    #the category of this rule
    category = Category(rule["key"])
    #what is still missing in this rule, 0 means done
    remaining = result.remaining_by_category[category]
    #the science points and the complete chain are one row: done only when both are done
    if rule["key"] == "science":
        #what is still missing: the points, the chain, or both
        missing_parts = []
        if remaining > 0:
            missing_parts.append(missing_text(rule, remaining))
        if result.remaining_by_category[Category.SCIENCE_CHAIN] > 0:
            missing_parts.append(t("a_chain"))
        status = t("status_missing") if missing_parts else t("status_done")
        still_needed = " + ".join(missing_parts)
    #a rule with no minimum of its own is never done or missing alone, its points count in a sum rule
    elif rule.get("min_points") == 0:
        status = t("status_none")
        still_needed = t("counts_in", rule=sum_rule_label.get(rule["key"], t("the_total")))
    #a done rule
    elif remaining == 0:
        status = t("status_done")
        still_needed = ""
    #a rule that is not done yet
    else:
        status = t("status_missing")
        still_needed = missing_text(rule, remaining)
    #the row: the rule, its status, and what is still needed in the right unit
    rule_rows.append({t("col_requirement"): rule_label(rule), t("col_status"): status, t("col_still"): still_needed})
#the table of the 13 rules, tall enough to show every row without scrolling (35 pixels per row)
st.dataframe(
    table_rows(rule_rows),
    hide_index=True,
    width="stretch",
    height=(len(rule_rows) + 1) * 35 + 3,
    #the first column is wide, so long rule names are not cut
    column_config={
        t("col_requirement"): st.column_config.TextColumn(width="large"),
        t("col_status"): st.column_config.TextColumn(width="small"),
        t("col_still"): st.column_config.TextColumn(width="medium"),
    },
)
#the points that moved by themselves from one rule to another (science, extra math, the pair)
moved_lines = []
#every rule key with its rule, to find the rules points move from
rules_by_key = {rule["key"]: rule for rule in requirements["rules"]}
for rule in requirements["rules"]:
    #every rule this rule takes a surplus from
    for source_key in rule.get("surplus_from", []):
        #how many points moved from this one source
        moved = count_surplus_points({"surplus_from": [source_key]}, requirements, result.points_by_category)
        #we show only what really moved
        if moved > 0:
            moved_lines.append(t("moved_line", points=f"{moved:g}", source=rule_label(rules_by_key[source_key]), target=rule_label(rule)))
#a short box with the moved points, only if something moved
if moved_lines:
    st.info(t("moved_title") + "  \n" + "  \n".join(moved_lines))

#the courses the student can still take, only for the rules that name courses
st.subheader(t("still_need_header"))
#we remember if any rule has missing courses
any_missing = False
for rule in requirements["rules"]:
    #only the rules that name courses have a list of missing courses
    if rule["kind"] != "required_courses":
        continue
    #the category of this rule
    category = Category(rule["key"])
    #the courses of this rule the student did not do yet, empty means done
    missing_courses = result.missing_courses_by_category.get(category, [])
    #a done rule has nothing to show
    if not missing_courses:
        continue
    #this rule has missing courses
    any_missing = True
    #how many of them the student still needs
    remaining = result.remaining_by_category[category]
    #when every listed course is needed we say how many are missing, otherwise how many to take from the list
    if remaining == len(missing_courses):
        box_title = t("box_missing", rule=rule_label(rule), what=missing_text(rule, remaining))
    else:
        box_title = t("box_take", rule=rule_label(rule), what=missing_text(rule, remaining), n=len(missing_courses))
    #a closed box per rule
    with st.expander(box_title):
        #one row per course
        st.dataframe(
            table_rows([{t("col_number"): course.id, t("col_points"): course.credits, t("col_name_en"): course.name_en, t("col_name_he"): course.name_he} for course in missing_courses]),
            hide_index=True,
            width="stretch",
            height=(len(missing_courses) + 1) * 35 + 3,
        )
#if nothing is missing, we say so
if not any_missing:
    st.write(t("no_missing"))

#the disclaimer at the end of the page
st.caption(t("disclaimer"))

#now we know the points, so we fill the band at the top of the page
hero_place.markdown(hero_html(counted_points), unsafe_allow_html=True)
