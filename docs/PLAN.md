# Technion CS Degree Audit — Project Plan (v3)

What we build, in what order, who writes each part, and when each day is done.

Catalog: Faculty of Computer Science **2024/2025 (תשפ"ה)**, 3-year general track.
Related docs: `docs/PROJECT_GUIDE.md` (what each file is), `docs/DECISIONS.md` (every rule and its source), `docs/QUESTIONS_TO_VERIFY.md` (open questions).

---

## 1. What changed from v2

| # | Change |
|---|---|
| 1 | Course IDs are **8 digits** (`02340114`), exactly as in the catalog. The regex becomes `\b\d{8}\b`. 6-digit IDs are not accepted. |
| 2 | `courses_data.json` holds **facts only**: `id`, `name_he`, `name_en`, `credits`. The `category` field is removed, because one course can be in several lists. |
| 3 | Real requirement structure: 118.5 total = 84 mandatory + 24.5 faculty electives + 10 general. **No List B minimum**; instead List A ≥ 18 and A+B ≥ 24.5. |
| 4 | New categories: extra math course, science (≥ 8), sport (≥ 2) and enrichment (≥ 6) inside general, English-taught courses (≥ 2, a count). |
| 5 | Manual entry of points in **every** category (replaces "אישור חריג" for List A/B only). |
| 6 | Two either-or groups: `00440252` / `02340252` and `02360360` / `02360267`. |
| 7 | Scope split into v1 (this week) and v2 (later). See section 3. |
| 8 | Who writes what: you write the logic; Claude writes repetitive and purely technical parts and explains every line. |
| 9 | New `docs/` folder for the project documents. |

---

## 2. The project in one paragraph

A Streamlit web app for Technion CS students on the 3-year track. The student selects or pastes the courses they passed, and can add points manually in any category. The app shows the missing mandatory courses, the points left in every category, the points left for the whole degree, and whether the student is eligible to graduate.

**The problem it solves:** there is no official tool to simulate your degree status until close to graduation, so students check it by hand. That is slow and error-prone.

---

## 3. Scope: v1 now, v2 later

**The rule for splitting:** v1 contains every requirement that is a simple check (a list of courses, or points against a minimum). v2 contains the rules where **points move from one category to another**. Those rules are the hardest part of `audit.py`, and most of them still wait for answers from the faculty. Until v2, the student covers these cases with manual entry.

| Feature | Version |
|---|---|
| Input: searchable multiselect (ID / Hebrew / English) | v1 |
| Input: paste box, with a report of unknown IDs | v1 |
| Mandatory fixed courses + both either-or groups | v1 |
| Extra math course: one course from the list | v1 |
| Science ≥ 8 points | v1 |
| List A ≥ 18, A+B ≥ 24.5 | v1 |
| General ≥ 10, with sport ≥ 2 and enrichment ≥ 6 (manual) | v1 |
| English-taught courses ≥ 2 (manual count) | v1 |
| Total ≥ 118.5, each course counted once | v1 |
| Mandatory courses never count in List A/B | v1 |
| Manual points in every category | v1 |
| Dashboard, eligibility banner, reset button, footer + disclaimer | v1 |
| Deploy on Streamlit Community Cloud + README | v1 |
| Science chain (שרשרת) | v2 |
| Science surplus above 8 → List B | v2 |
| Extra math course also counts in List B / math surplus (waits for an answer) | v2 |
| Compilation / Computer Architecture: the second one counts in List A | v2 |
| At least one project in List A | v2 |
| Math replacement `01040158` + `01040279`; condition on `01040135` | v2 |
| "All faculty courses" count in List A (if confirmed) | v2 |
| GitHub Actions running pytest; remaining English names | v2 |

**Effect on v1 results:** without the v2 rules, v1 may show slightly **more** points left in List B than the real number (for example, the science surplus is not moved). It never shows the student as finished when they are not. The disclaimer says this, and manual entry fixes it.

---

## 4. Who writes what

| You write | Claude writes (and explains every line) |
|---|---|
| Design of `requirements.json` | Filling the long ID lists (List A, List B, science, math) |
| `Course`, `Category`, `AuditResult` in `models.py` | — |
| `catalog.py`: dictionaries, `normalize()`, `resolve()` | Error message wording |
| All logic in `audit.py` | Repeated functions, after you write the first one |
| The first test of each kind | The rest of the tests of the same kind |
| `parsing.py` (regex) | — |
| UI structure: what appears and where | Repeated widgets, styling, Hebrew display |
| — | README, deployment settings, GitHub Actions |

**One condition:** no line stays in the project that you cannot explain.

---

## 5. Directory structure

```
technion-cs-degree-audit/
├── .gitignore
├── README.md
├── requirements.txt          # streamlit==1.64.0, pytest==9.1.1
├── app.py                    # Streamlit UI only
├── core/
│   ├── __init__.py
│   ├── models.py             # Course, Category, AuditResult
│   ├── catalog.py            # CourseCatalog: 3 dicts + normalize() + resolve()
│   ├── parsing.py            # extract_course_ids()
│   └── audit.py              # pure audit engine, no Streamlit imports
├── data/
│   ├── courses_data.json     # 324 courses: facts only
│   └── requirements.json     # all rules (designed by you)
├── docs/
│   ├── PLAN.md
│   ├── PROJECT_GUIDE.md
│   ├── DECISIONS.md
│   └── QUESTIONS_TO_VERIFY.md
└── tests/
    ├── __init__.py
    ├── test_catalog.py
    ├── test_parsing.py
    └── test_audit.py
```

---

## 6. Day-by-day roadmap

Each day ends with a **"done when"** check and a commit. Hours are rough estimates of focused work for a student who is still learning.

| Day | Focus | Hours |
|---|---|---|
| 1 | Data in the repo, `Course`, catalog, catalog tests | 8–12 |
| 2 | `requirements.json`, models, mandatory audit | 5–7 |
| 3 | Points audit: all categories + total | 4–6 |
| 4 | Paste parsing + input UI | 4–6 |
| 5 | Manual entry, results, session state | 4–6 |
| 6 | Deploy + README | 2–3 |
| | **Total** | **27–40** |

---

### Day 1 — Data and catalog

**Goal:** all data and documents are in the repo, and a course can be found by ID, Hebrew name or English name.

| # | Step | Who |
|---|---|---|
| 1 | Setup: repo, WSL, venv, `.gitignore`, pinned `requirements.txt` ✅ **done** | — |
| 2 | Copy `courses_data.json` into `data/` and the docs into `docs/`; commit | You (Claude gives the commands) |
| 3 | Send `QUESTIONS_TO_VERIFY.md` to the faculty; spot-check 15 courses against the catalog. **Runs in parallel; does not block the next steps.** | You |
| 4 | `models.py`: frozen dataclass `Course` with `id`, `name_he`, `name_en`, `credits` | You |
| 5 | `catalog.py` part 1: read the JSON (utf-8) → `Course` objects → `_by_id` dictionary | You |
| 6 | `catalog.py` part 2: `normalize()` — extra spaces, geresh `׳`, gershayim `״`, English lowercase | You |
| 7 | `catalog.py` part 3: `_by_name_he`, `_by_name_en`, `resolve()`, error on duplicate IDs | You |
| 8 | `tests/test_catalog.py` with a small fake JSON (`tmp_path`) | You write the first tests, Claude the rest |
| 9 | Run `pytest`; load the real file (324 courses) without errors | You |

**Decisions you make in step 7:**
- `00440252` and `02340252` have **the same Hebrew name** (same course, two numbers). A "duplicate name → error" rule would stop the program on the real data. What should happen, and what should a search by that name return?
- 201 courses have an empty English name (`""`). What happens if they all go into `_by_name_en`?

**Done when:** `pytest` is green, and ID, Hebrew name and English name all return **the same** `Course` object.
**Learn first:** venv, `@dataclass`, `frozen=True`, hashable, type hints, `json.load`, dictionary lookups, pytest basics (`assert`, `pytest.raises`, `tmp_path`).
**Commit:** `Day 1: models, data, triple-key catalog`

---

### Day 2 — Requirements and mandatory audit

**Goal:** all v1 rules live in `requirements.json`, and the engine finds the missing mandatory courses.

| # | Step | Who |
|---|---|---|
| 1 | Update the data and `DECISIONS.md` from the faculty answers | Claude |
| 2 | Design `requirements.json` for v1: types of rules, their fields, the combined A+B category, manual-only categories, count vs points | You |
| 3 | Review the design together | Both |
| 4 | Fill the long ID lists into your design | Claude |
| 5 | `models.py`: `Category` enum and `AuditResult` | You |
| 6 | Test: every ID in `requirements.json` exists in `courses_data.json` | You |
| 7 | `audit.py`: missing mandatory = set difference; either-or groups; extra math "one of the list" | You |
| 8 | Validate manual entries: negative values raise `ValueError` | You |
| 9 | Tests: empty input, everything done, one course of each pair, both courses of a pair | You first, Claude the rest |

**Done when:** every mandatory edge case has a passing test.
**Learn first:** set operations, `Enum`, `@property`, `pytest.raises`.
**Commit:** `Day 2: requirements and mandatory audit`

---

### Day 3 — Points audit

**Goal:** the engine computes the points left in every category and in the total.

| # | Step | Who |
|---|---|---|
| 1 | Sum course points per category: science, List A, List B | You |
| 2 | Rule: mandatory courses never count in List A/B | You |
| 3 | Add manual points to each category and to combined categories (List A → A+B → total) | You |
| 4 | Deficit = `max(0, required − have)` for science 8, List A 18, A+B 24.5, general 10 (sport 2, enrichment 6), English 2 courses | You first, Claude repeats |
| 5 | Total 118.5: each course counted once, plus manual points | You |
| 6 | "Eligible to graduate" as a `@property` of `AuditResult` | You |
| 7 | Tests: duplicates counted once, deficit never negative, manual entry only, half points (3.5), everything done | You first, Claude the rest |

**Done when:** all points edge cases pass, and a full real example (a sample transcript) gives the expected numbers.
**Learn first:** generator expressions with `sum()`, `pytest.approx` for floats.
**Commit:** `Day 3: points audit for all categories`

---

### Day 4 — Paste parsing and input UI

**Goal:** the student can select or paste courses and see them in a table.

| # | Step | Who |
|---|---|---|
| 1 | `parsing.py`: `extract_course_ids(text)` with `\b\d{8}\b`, no duplicates, in first-seen order | You |
| 2 | Split the results into found and unknown using the catalog | You |
| 3 | Tests: commas, newlines, Hebrew text around IDs, 6/7/9-digit numbers ignored, duplicates | You first, Claude the rest |
| 4 | `app.py`: page config; catalog loaded once with `@st.cache_resource` | You (Claude explains the commands) |
| 5 | Multiselect with labels "ID – Hebrew / English"; paste box inside an expander; unknown-ID notice | You |
| 6 | Table of selected courses; Hebrew displayed right-to-left | Claude |

**Done when:** `streamlit run app.py` works and courses from both inputs appear in the table.
**Learn first:** `re.findall`, `\b`, `dict.fromkeys()`, the Streamlit rerun model, `st.expander`, caching.
**Commit:** `Day 4: paste parsing and input UI`

---

### Day 5 — Manual entry and results

**Goal:** the app shows the full audit and keeps everything across reruns.

| # | Step | Who |
|---|---|---|
| 1 | `st.session_state` for selections and manual entries, initialized safely | You |
| 2 | Manual inputs: one `st.number_input` per category (min 0, step 0.5) + English-course count | You first, Claude repeats |
| 3 | Results: per category "X points left" or "Completed"; missing mandatory list; total left | You (logic), Claude (layout) |
| 4 | Eligibility banner: "Eligible to graduate" / "Not yet" | You |
| 5 | Reset button that clears the session | You |
| 6 | Footer: catalog year, source, disclaimer (the official audit is final; v1 limits) | Claude |

**Done when:** changing a manual entry updates the numbers without losing the selected courses.
**Learn first:** `st.session_state` and widget `key=`, `st.metric`, `st.columns`.
**Commit:** `Day 5: manual entry, results and session state`

---

### Day 6 — Deploy and document

**Goal:** a live link that works on a phone, and a README a recruiter can read in one minute.

| # | Step | Who |
|---|---|---|
| 1 | Check that `requirements.txt` has only the packages used, pinned | You |
| 2 | Deploy on Streamlit Community Cloud | You (Claude gives the steps) |
| 3 | README: demo link, screenshot, features, getting started, running tests, updating data, structure, disclaimer | Claude drafts, you review |
| 4 | Test the live link on a phone | You |

**Done when:** the live link works on your phone and the README has the link and a screenshot.
**Learn first:** Streamlit Cloud deployment, README structure.
**Commit:** `Day 6: deploy and README`

---

## 7. v2 backlog

Ordered by value. Each item needs a rule in `requirements.json`, logic in `audit.py`, and tests.

1. Science chain (שרשרת): one complete chain out of four
2. Science surplus above 8 → List B
3. Extra math course: also counts in List B, or only its surplus above 2.5 (depends on the faculty answer)
4. Compilation / Computer Architecture: the second one counts in List A
5. At least one project in List A
6. Math replacement `01040158` + `01040279`; condition on `01040135`
7. "All faculty courses" count in List A (if confirmed)
8. GitHub Actions: run pytest on every push
9. English names for the remaining 201 courses

---

## 8. Open questions that affect Day 2

Full list with Hebrew wording: `docs/QUESTIONS_TO_VERIFY.md`.

- **Q1:** Is the extra math course counted as 2.5 in mandatory with the surplus in List B, or fully in both?
- **Q5:** Where is the Compilation / Computer Architecture rule written?
- **Q7:** Does List A include every faculty course, even ones not listed?
- **Q9–Q10:** Sport and enrichment minimums on the 3-year track.

---

## 9. Next step

Day 1, step 2: copy the data file and the docs into the repo and commit. Then `models.py`.
