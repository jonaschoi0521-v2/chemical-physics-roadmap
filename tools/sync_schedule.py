#!/usr/bin/env python3
"""Regenerate the private semester schedule from data/courses/.

Keeps private/chem-phy/chemical-physics-semester-schedule.md in step with the
course files, so a drag in the registration page updates it automatically
instead of by hand (CLAUDE.md rule 6).

private/ is gitignored — this output never leaves the machine.

Run: python3 tools/sync_schedule.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402  — reuse the same loader/sorter the site uses

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE = ROOT / "private" / "chem-phy" / "chemical-physics-semester-schedule.md"

ARABIC = {
    "Semester I": 1, "Semester II": 2, "Semester III": 3, "Semester IV": 4,
    "Semester V": 5, "Semester VI": 6, "Semester VII": 7, "Semester VIII": 8,
}


def pts(value: str) -> str:
    """3.00 -> 3pt, 2.50 -> 2.5pt."""
    return f"{float(value):g}pt"


def render(blocks: list[dict]) -> str:
    lines = ["# Semester Schedule — Chemical Physics + Builder", ""]
    for block in blocks:
        n = ARABIC[block["label"]]
        lines += [f"## Semester {n} — {pts(block['total'])}", ""]
        lines += ["| Course | Code | Points |", "| ------ | ---- | ------ |"]
        for row in block["rows"]:
            lines.append(f"| {row['name']} | {row['code']} | {pts(row['credits'])} |")
        lines.append("")

    lines += ["---", "", "## Summary", ""]
    lines += ["| Semester | Points |", "| -------- | ------ |"]
    for block in blocks:
        lines.append(f"| {ARABIC[block['label']]} | {pts(block['total'])} |")
    total = sum(float(b["total"]) for b in blocks)
    lines.append(f"| **Total** | **{total:g}pt** |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if not SCHEDULE.parent.exists():
        sys.stderr.write(f"Missing {SCHEDULE.parent} — nothing to sync.\n")
        return 1
    blocks = build.build_registration(build.load_courses())
    SCHEDULE.write_text(render(blocks), encoding="utf-8")
    print(f"Synced {SCHEDULE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
