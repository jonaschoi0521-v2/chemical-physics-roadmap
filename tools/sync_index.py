#!/usr/bin/env python3
"""Regenerate data/courses/_index.md from the course files.

_index.md is the tracked, public "course master list". It was written by hand for the
old CC -> SEAS Chemical Engineering transfer plan and never updated after the switch to
Chemical Physics, so it sat in the repo describing a degree Jonas isn't pursuing.
Generating it removes that failure mode: it is now a view over data/courses/, not a
second source of truth.

The loader skips files starting with "_", so this file is never itself a course.

Run: python3 tools/sync_index.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "courses" / "_index.md"

# Section heading -> which courses belong in it, in the order they should appear
SECTIONS = [
    ("Chemistry", lambda c: c["subject"] == "Chemistry"),
    ("Physics", lambda c: c["subject"] == "Physics"),
    ("Mathematics", lambda c: c["subject"] == "Mathematics"),
    ("Builder Stack — CS & ML", lambda c: c["subject"] == "Programming"),
    ("Core Curriculum", lambda c: c["subject"] == "Core Curriculum"),
]


def pts(value: str | float) -> str:
    return f"{float(value):g}"


def table(rows: list[dict]) -> list[str]:
    out = ["| Course | Code | Credits | Status | Semester | Grade |",
           "|---|---|---|---|---|---|"]
    for c in rows:
        out.append(
            f"| {c['name']} | {c['code']} | {pts(c['credits'])} | {c['status']} "
            f"| {c['semester'] or '—'} | {c['grade'] or ''} |"
        )
    return out


def waived_courses() -> list[tuple[str, str]]:
    """(title, reason-ish first line of Why) for courses explicitly not being taken."""
    out = []
    for path in sorted((ROOT / "data" / "courses").glob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        fields = build.parse_fields(text)
        if fields.get("Status", "").lower() == "waived":
            out.append(build.parse_title(text))
    return out


def render(courses: list[dict]) -> str:
    lines = [
        "# Course Master List",
        "",
        f"Last generated: {date.today().isoformat()} — **do not edit by hand.**",
        "Run `python3 tools/sync_index.py` after changing anything in `data/courses/`.",
        "",
        "Degree: **Columbia College, Chemical Physics** (Chemistry Track 3 + Physics",
        "Sequence B), with a self-directed CS/ML stack alongside it.",
        "",
        "---",
        "",
    ]

    for heading, match in SECTIONS:
        rows = [c for c in courses if match(c)]
        if not rows:
            continue
        rows.sort(key=lambda c: (c["semester_order"], c["order"], c["code"]))
        subtotal = sum(float(c["credits"]) for c in rows)
        lines += [f"## {heading} — {pts(subtotal)}pt", ""]
        lines += table(rows)
        lines.append("")

    lines += ["---", "", "## Load by Semester", "",
              "| Semester | Points |", "|---|---|"]
    blocks = build.build_registration(courses)
    for block in blocks:
        lines.append(f"| {block['label']} | {pts(block['total'])} |")
    total = sum(float(b["total"]) for b in blocks)
    lines.append(f"| **Total** | **{pts(total)}** |")
    lines += ["",
              "Columbia College caps registration at **18 points** per term; above that "
              "needs a petition.", ""]

    waived = waived_courses()
    if waived:
        lines += ["---", "", "## Not Taking (waived)", "",
                  "Kept as files so the decision stays on the record.", ""]
        lines += [f"- {title}" for title in waived]
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    INDEX.write_text(render(build.load_courses()), encoding="utf-8")
    print(f"Synced {INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
