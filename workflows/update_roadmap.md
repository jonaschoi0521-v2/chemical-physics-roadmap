# Workflow: End-of-Semester Review

**When to use:** At the end of each semester and at the start of each new semester. This is the "step back and see the whole picture" workflow.

Estimated time: 30–45 minutes.

---

## End of Semester

### 1. Close out courses

For each course taken this semester:
- Change `**Status:**` to `completed`
- Fill in `**Grade:**`
- Write a final log entry: what you learned, what surprised you, what you'd tell yourself at the start of the semester, how it connects to the major or the mission

### 2. Update `data/courses/_index.md`

Update the Status and Grade columns for all completed courses. Check if any major requirements are now met.

### 3. Debrief active projects

For each project:
- If completed: mark `completed`, fill in Outcome, write final log entry
- If ongoing: write a progress log entry, update Next Action
- If stalled: decide honestly — `paused` with a restart plan, or `abandoned` with a lessons-learned note

### 4. Review the research pipeline

For each researcher:
- Is the status current?
- Is there a Next Action you've been ignoring? Act on it or drop it.
- Did any relationship go cold? Mark it `cold`.

### 5. Review internship applications

- Close out any outcomes (accepted/rejected) with Outcome Notes
- Note which opportunities to watch for next year

---

## Start of New Semester

### 1. Advance planned courses to in-progress

For each course you're enrolling in:
- Change `**Status:**` to `in-progress`
- Fill in `**Semester:**`, `**Professor:**`
- Write an enrollment log entry

### 2. Identify upcoming internship deadlines

Add any deadlines you know about for the next 6 months to `data/internships/`.

### 3. Set 1–2 research goals for the semester

What researcher do you want to contact? What lab do you want to visit?

### 4. Rebuild the dashboard

```
python3 tools/build.py
```

Open `site/index.html` and look at the full picture. Does the progress bar feel right? Are there gaps you're surprised by?

---

## Registration Checkpoint

Before each registration period:
- Run `python3 tools/status.py` and confirm the upcoming semester's courses are all present
- Check `data/courses/_index.md` — every major requirement should map to a scheduled course
- Verify no semester exceeds Columbia College's **18-point cap** (the schedule totals are
  computed, so read them rather than counting by hand); petition or move a course if one does
- Confirm prerequisites and term availability for anything new — several courses in this plan
  are offered in one term only
