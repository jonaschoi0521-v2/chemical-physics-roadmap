# Workflow: Add a New Course

**When to use:** When you're enrolling in a course, planning a future semester, or adding a course you already took that isn't yet in the system.

---

## Option A — Course from the degree track (already scaffolded)

All degree-track courses (from the Columbia ChemE PDFs) already exist as files in `data/courses/`. To activate one:

1. Open the file (e.g., `data/courses/chem-un1403-general-chemistry-1.md`)
2. Change `**Status:** planned` to `**Status:** in-progress`
3. Fill in `**Semester:**`, `**Professor:**`, and `**Location:**` if known
4. Write a log entry: `### YYYY-MM-DD — Enrolled`

---

## Option B — Course NOT on the standard degree track

1. **Scaffold a new file:**
   ```
   python3 tools/new_entry.py course "Course Name"
   ```
   This creates `data/courses/slugified-name.md` with the standard template.

2. **Fill in the header fields:** code, semester, credits, what requirement it fulfills, professor.

3. **Write a first log entry:** Mark the date you enrolled or started.

---

---

## Moving a course between semesters

Don't hand-edit `templates/registration.html` — the semester tables and their credit
totals are generated from `data/courses/`.

Run `python3 tools/serve.py`, open the **Registration** page, and drag the course to
where you want it. Each drop writes `**Semester:**` and `**Order:**` back to the course
file, rebuilds the site, and re-syncs the private semester schedule. Dragging works only
while that local server is running; the published GitHub Pages copy is read-only.

To do it by hand instead: change `**Semester:**` in the course file, then run
`python3 tools/build.py && python3 tools/sync_schedule.py`.

---

## Naming convention

Files follow `dept-code-description.md`:
- `chen-e3110-transport-phenomena-1.md`
- `chem-un1403-general-chemistry-1.md`

Once created, **never rename** — filenames are stable identifiers.

---

## What to fill in immediately

- Status, Semester, Credits, Fulfills, Professor
- "Why This Course Matters" — one paragraph connecting this course to your ChemE or pharma/biotech goals

## What to fill in over time

- Key Concepts (update as the course progresses)
- Resources Used
- Connections to other courses or projects
- Log entries after each significant session
