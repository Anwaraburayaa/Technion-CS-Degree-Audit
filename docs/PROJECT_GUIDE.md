# Technion CS Degree Audit — Project Guide

What every file is, what it contains, why it exists, and who writes it.

---

## 1. How the whole project works

Data flows through the project in this order:

```
data/courses_data.json  ┐
data/requirements.json  ┘ → core/catalog.py → (student's selections in app.py / parsing.py)
                                                        ↓
                                                  core/audit.py
                                                        ↓
                                              AuditResult → app.py displays it
```

1. **The two JSON files** hold the facts: which courses exist and what the degree requires. They contain no code.
2. **`catalog.py`** reads the courses file when the program starts, turns each course into a `Course` object, and builds three lookup dictionaries from them.
3. The student selects their courses in the UI (`app.py`) or pastes course numbers; `parsing.py` extracts the numbers from the pasted text.
4. **`audit.py`** takes the completed courses and the degree requirements and calculates what is missing.
5. The result is collected in an `AuditResult` object, and `app.py` displays it.

**`models.py`** does not appear in the flow because it defines the **data types** that move through it: `Course`, `Category` and `AuditResult`. Every other file imports from it.

---

## 2. `data/courses_data.json` — the courses file

**What it is:** a text file in JSON format — a format for storing structured data using lists `[...]` and key–value pairs `{"key": value}`. Python reads it with `json.load` and turns it into ordinary `dict` and `list` objects.

**Its role:** the single source of information about courses. The program knows about a course only if it is listed here.

**Why a separate file and not inside the code:** when the courses change for a new catalog year, you edit only this file and do not touch a single line of Python.

**Its content:**

```json
{
  "catalog_year": "2024/2025 (תשפ\"ה)",
  "source": "Technion Faculty of Computer Science catalog 2024/2025, pages ...",
  "courses": [
    {
      "id": "02360766",
      "name_he": "מבוא ללמידת מכונה",
      "name_en": "Introduction to Machine Learning",
      "credits": 3.5
    }
  ]
}
```

The file has **324 courses**: the mandatory courses, the extra math list, the science list, List A and List B, all from the 2024/2025 catalog.

| Field | Meaning | Note |
|---|---|---|
| `catalog_year` | The catalog year the data was copied from | Shown in the page footer |
| `source` | Where the data came from (catalog and pages) | Also shown, so the student can verify |
| `id` | Course number, **8 digits**, exactly as in the catalog | **A string, not a number**: stored as a number, the leading zeros of `02340114` would disappear |
| `name_he` / `name_en` | Hebrew and English name | Used for searching. `name_en` is `""` when no English name is known yet (201 courses) |
| `credits` | Credit points | A float, because some courses are 3.5 points |

**There is no `category` field.** One course can belong to several lists (for example, `01040174` is in the extra-math list and in List B). So the file holds only **facts about each course**, and which list a course belongs to is written in `requirements.json`.

**Skills needed:** knowing JSON syntax (very simple) and reading the official catalog carefully. This is data work, not programming.

**Who filled it:** Claude extracted it from the catalog PDF; you verify a sample against the catalog (see `docs/QUESTIONS_TO_VERIFY.md` for the suspicious entries).

---

## 3. `data/requirements.json` — the degree requirements file

**What it is:** a second JSON file. It does not describe courses; it describes **what the degree requires**.

**Why separate from the courses file:** a course is a fact (its number, its points). A requirement is a rule (you must complete X points from List A). Keeping them apart means you can change the rules without touching the course list, and vice versa.

**Its content:** **you design the shape** (Day 2). The old shape (`thresholds` with three keys, `mandatory`, `mandatory_groups`) cannot express the real rules, so it is replaced.

The file must express every v1 rule in `docs/DECISIONS.md`:

| Rule | Kind of check |
|---|---|
| Total ≥ 118.5 | Points, each course once |
| Fixed mandatory courses | "All of these" |
| `00440252` / `02340252` and `02360360` / `02360267` | "One of these" |
| Extra math course | "One course from this list" |
| Science ≥ 8 | Points from a list |
| List A ≥ 18 | Points from a list |
| List A + List B ≥ 24.5 | Points from two categories together |
| General ≥ 10, sport ≥ 2, enrichment ≥ 6 | Manual points only, with sub-categories |
| English-taught courses ≥ 2 | Manual **count**, not points |

**Questions to think about while designing:** what kinds of rules exist, and what fields each kind needs? How do you write "A+B" without copying List A's 226 IDs again? How do you tell points from a count?

**Skills needed:** the difficulty is not JSON syntax; it is turning each rule into data that code can read without the rule being written in Python.

**Who fills it:** you design the shape; Claude fills the long ID lists into it. Course numbers are never invented.

---

## 4. `core/models.py` — defining the data types

**What it is:** a Python file that defines three types (classes). It contains no calculation logic, only the shape of the data.

**Why we need it:** after `json.load` we get a plain `dict` like `{"id": "02340114", "credits": 4.0, ...}`. Problems with a plain `dict`:

- If you write `course["credit"]` instead of `course["credits"]`, you only find out when the program runs.
- Nothing stops a wrong value like a category written `"LIST_a"`.
- There is no single place that says "these are the fields of a course".

So we convert each `dict` into an object with fixed fields, **once, at load time**, and from then on all code works with objects whose shape is guaranteed.

**The three types:**

**a) `Category`:** an `Enum` — a fixed set of named values for the categories in `requirements.json` (for example List A, List B, science). If a value arrives from JSON that is not in this set, Python raises an error immediately at load time, instead of the program silently computing a wrong result. It is **not** a field of `Course`. Its exact values depend on your `requirements.json` design, so it is written on Day 2.

**b) `Course`:** defined with `@dataclass(frozen=True)`, with four fields: `id`, `name_he`, `name_en`, `credits`. Written on Day 1.

- `@dataclass` automatically generates `__init__` (to create the object), `__repr__` (to print it readably) and `__eq__` (to compare two objects by their fields).
- `frozen=True` makes the object unchangeable after creation. Two reasons: (1) course data should not change while the program runs, and (2) an unchangeable object becomes **hashable**, meaning it can be put in a `set` or used as a `dict` key. This is required because `audit.py` will use set operations (set difference).

**c) `AuditResult`:** the object that `audit.py` returns, containing everything the UI needs to display. Written on Day 2.

**Skills needed:** Python classes, `Enum`, dataclasses, type hints (e.g. `credits: float`), and what "hashable" means.

**This part requires thinking — you write it, then it gets reviewed.**

- ✅ **Answered:** where the category lives. Not in the course; in `requirements.json`, because one course can be in several lists.
- **Still to think about (Day 2):** what are the fields of `AuditResult` and their types? Look at what the UI shows: missing mandatory courses, points left per category, total left, eligibility.
- **Still to think about (Day 2):** should "eligible to graduate" be a stored field, or computed from the other fields? (Look up `@property`.)

---

## 5. Which parts of the project need your thinking

| File | Type of work | Who writes it |
|---|---|---|
| `courses_data.json` | Data entry from the catalog | Claude extracted, you verify |
| `requirements.json` | Design of the rules as data | You design, Claude fills the long lists |
| `models.py` | Small design | You, then review |
| `catalog.py` | Logic: dictionaries, name normalization, errors | You |
| `parsing.py` | Regex | You |
| `audit.py` | **The core of the project**: sets, deficits, combined categories | You; Claude repeats a function after you write the first one |
| `tests/` | Deciding which cases must be tested | You write the first test of each kind, Claude the rest |
| `app.py` | Learning Streamlit commands | You (structure), Claude (repeated widgets, styling) |

For every "You" file: the concepts and requirements are explained first, then you make an attempt, then it gets reviewed line by line. Every line Claude writes is explained before moving on.

---

## Next steps

See `docs/PLAN.md`, Day 1: copy the data file and the docs into the repo, then write `Course` in `models.py`.
