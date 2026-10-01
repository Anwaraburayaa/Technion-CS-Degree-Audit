# Design Decisions — Technion CS Degree Audit

Decisions made before writing the data files. Main source for every rule: the official
Faculty of Computer Science catalog **2024/2025 (תשפ"ה)**, 3-year general track
(catalog pages 224–225, 227–229, 231). Rules that come from somewhere else are marked
with their source.

## Scope

| Topic | Decision |
|---|---|
| Catalog | 2024/2025 (תשפ"ה) exactly, 3-year general track |
| Course IDs | 8 digits only, exactly as in the catalog (e.g. `02340114`). Old 6-digit IDs are not accepted |
| English names | Provided manually by the student (not all courses have one yet) |
| Project requirement (≥1 project in List A) | Not in v1; maybe later |
| Replacing `01040134` + extra math with `01040158` + `01040279` | Not in v1; covered by manual entry |

## Requirements to check (3-year track, total 118.5)

| Category | Rule |
|---|---|
| Total | ≥ 118.5 points; each course's points counted **once** |
| Mandatory fixed courses | All fixed mandatory courses completed |
| Either-or group 1 | `00440252` **or** `02340252` (one is enough) |
| Either-or group 2 | `02360360` (תורת הקומפילציה) **or** `02360267` (מבנה מחשבים). Source: the student's information from the faculty — catalog p. 231 lists only `02360360` |
| Extra math course | One course from the list on catalog p. 225 |
| Science | ≥ 8 points from the science list **and** one complete chain (שרשרת) |
| List A | ≥ 18 points |
| List A + List B | ≥ 24.5 points together |
| General electives (כלל-טכניוני) | ≥ 10 points; within it ≥ 2 sport (חינוך גופני) and ≥ 6 enrichment (מל"ג / העשרה). **Manual entry only** (the catalog has no list of these courses) |
| English-taught courses | ≥ 2 **courses** (a count, not points). Manual entry: "How many English-taught courses have you completed?" These courses still count toward their normal category; this is an extra check only. Source: Technion-wide regulation (not in the faculty catalog chapter) |

## Counting rules

- **Each course counts in one category**, with exactly two exceptions:
  1. **Extra math course:** the course used as the extra math course counts toward the
     extra-math requirement **and** toward List B (if it is in List B, e.g. `01040174`).
     Its points count **once** in the total.
  2. **Science surplus:** science courses count toward List B **only** through the
     surplus — points above 8 go to List B (example: 10 science points → 2 points to List B).
     A science course never counts directly in List B, even if it appears there.
- **Mandatory courses never count in List A or List B**, even if they appear there
  (e.g. `02360360` is in List A in the catalog).
- **Compilation / Computer Architecture pair:**
  - Only one completed → it counts as mandatory only.
  - Both completed → one counts as mandatory, the other counts toward List A.
- **Manual entry in every category:** the student can enter "I completed X points in
  category Y" without course numbers. Manual points count toward that category,
  toward any combined category that includes it (e.g. List A → A+B), and toward the total.

## Output

- For each category: points remaining, or "completed".
- The list of missing mandatory courses (ID + name).
- Points remaining for the total degree.

## Data notes

- `02306651` in the catalog is a typo; stored as `02360651` (confirmed by the Technion portal).
- `02368035` (סמינר בבינה מלאכותית) is stored exactly as printed; it may be a typo for
  `02360835`, not confirmed.
- `02360267` (מבנה מחשבים, 3.0) is taken from the 4-year track table (catalog p. 225),
  because of either-or group 2.
- Courses from the Technion portal that are not in the 2024/2025 catalog are not included.
