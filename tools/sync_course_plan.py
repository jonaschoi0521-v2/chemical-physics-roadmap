#!/usr/bin/env python3
"""Regenerate the private course plan from data/courses/.

private/chem-phy/chemical-physics-course-plan.md used to be maintained by hand and
drifted out of step with the real schedule — it still listed PHYS GU4021/4022,
MATH UN2010 and STAT GU4001 long after they were dropped. Same fix as
sync_schedule.py: generate the tables, keep the prose.

Everything from the "## Self-Study" heading onward is preserved verbatim; only the
course table and the type totals are rewritten.

private/ is gitignored — this output never leaves the machine.

Run: python3 tools/sync_course_plan.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  — reuse the same loader the site uses

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "private" / "chem-phy" / "chemical-physics-course-plan.md"
KEEP_FROM = "## Self-Study"

# **Fulfills:** in a course file -> the "Type" column in the plan table
TYPE_BY_FULFILLS = {
    "Core Curriculum": "Core",
    "Chemical Physics Major": "Major",
    "Builder Stack": "Builder",
}
TYPE_ORDER = ["Core", "Major", "Builder"]


def pts(value: str | float) -> str:
    """3.00 -> 3pt, 2.50 -> 2.5pt."""
    return f"{float(value):g}pt"


def course_type(fulfills: str) -> str:
    return TYPE_BY_FULFILLS.get(fulfills.strip(), "Major")


def render(courses: list[dict]) -> str:
    rows = []
    for kind in TYPE_ORDER:
        group = [c for c in courses if course_type(c["fulfills"]) == kind]
        # chronological within each type, matching the registration order
        group.sort(key=lambda c: (c["semester_order"], c["order"], c["code"]))
        rows += [(kind, c) for c in group]

    width = max((len(c["name"]) for _, c in rows), default=6)
    lines = ["# Course Plan — Chemical Physics + Builder", ""]
    lines.append(f"| #  | {'Course'.ljust(width)} | Code        | Points | Type    |")
    lines.append(f"| -- | {'-' * width} | ----------- | ------ | ------- |")
    for i, (kind, c) in enumerate(rows, 1):
        code = c["code"] if c["code"] != "—" else "—"
        lines.append(
            f"| {str(i).ljust(2)} | {c['name'].ljust(width)} | {code.ljust(11)} "
            f"| {pts(c['credits']).ljust(6)} | {kind.ljust(7)} |"
        )

    lines += ["", "", "| Type             | Points      |",
              "| ---------------- | ----------- |"]
    total = 0.0
    for kind in TYPE_ORDER:
        subtotal = sum(float(c["credits"]) for k, c in rows if k == kind)
        total += subtotal
        lines.append(f"| {kind.ljust(16)} | {pts(subtotal).ljust(11)} |")
    lines.append(f"| **Total**        | {('**' + pts(total) + '**').ljust(11)} |")
    lines.append(f"| **Avg/Semester** | {('**' + f'{total / 8:.1f}pt' + '**').ljust(11)} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if not PLAN.exists():
        sys.stderr.write(f"Missing {PLAN} — nothing to sync.\n")
        return 1

    old = PLAN.read_text(encoding="utf-8")
    tail = ""
    if KEEP_FROM in old:
        tail = "\n" + old[old.index(KEEP_FROM):]
    else:
        sys.stderr.write(f"Warning: no '{KEEP_FROM}' section found — prose not preserved.\n")

    PLAN.write_text(render(build.load_courses()) + tail, encoding="utf-8")
    print(f"Synced {PLAN.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
