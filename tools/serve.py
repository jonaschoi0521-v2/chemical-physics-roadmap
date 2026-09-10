#!/usr/bin/env python3
"""Build the site and serve it locally. Kills any existing server, finds a free port.

Serving locally also enables edit mode on the registration page: courses can be
dragged between and within semesters, and each drop writes straight back to
data/courses/*.md, then rebuilds. The published GitHub Pages copy has no such
endpoint, so it stays a static, read-only page.

Endpoints (localhost only):
    GET  /api/ping     -> {"ok": true}   the page's edit-mode probe
    POST /api/reorder  -> apply a new course arrangement
    POST /api/remove   -> take a course off the schedule (waives it, keeps the file)
    POST /api/add      -> scaffold a new course into a semester
"""

from __future__ import annotations

import functools
import http.server
import json
import os
import re
import signal
import socket
import socketserver
import subprocess
import sys
import webbrowser
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
COURSE_DIR = ROOT / "data" / "courses"
START_PORT = 8000

VALID_SEMESTERS = {
    "Semester I", "Semester II", "Semester III", "Semester IV",
    "Semester V", "Semester VI", "Semester VII", "Semester VIII",
}


# ── Course file writing ──────────────────────────────────────────────────────

def set_field(text: str, name: str, value: object) -> str:
    """Set a **Field:** value, inserting it after the last field if absent.

    Everything else in the file — logs, notes, sections — is left untouched.
    """
    pattern = re.compile(rf"^\*\*{re.escape(name)}:\*\*[ \t]*.*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(lambda _: f"**{name}:** {value}", text, count=1)

    fields = list(re.finditer(r"^\*\*.+?:\*\*.*$", text, re.MULTILINE))
    if not fields:
        raise ValueError("file has no **Field:** header block")
    end = fields[-1].end()
    return f"{text[:end]}\n**{name}:** {value}{text[end:]}"


def apply_reorder(semesters: list[dict]) -> list[str]:
    """Write Semester + Order for every course in the affected semesters."""
    known = {p.name for p in COURSE_DIR.glob("*.md") if not p.name.startswith("_")}
    changed = []
    for block in semesters:
        label = block.get("semester", "")
        if label not in VALID_SEMESTERS:
            raise ValueError(f"unknown semester: {label!r}")
        for position, filename in enumerate(block.get("files", []), start=1):
            # Membership in `known` is the only way a path is accepted, so a
            # crafted name cannot escape data/courses/.
            if filename not in known:
                raise ValueError(f"unknown course file: {filename!r}")
            path = COURSE_DIR / filename
            original = path.read_text(encoding="utf-8")
            updated = set_field(original, "Semester", label)
            updated = set_field(updated, "Order", position)
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                changed.append(filename)
    return changed


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", s.strip())[:60]


def known_files() -> set[str]:
    return {p.name for p in COURSE_DIR.glob("*.md") if not p.name.startswith("_")}


def remove_course(filename: str) -> str:
    """Take a course off the schedule.

    Waives rather than deletes: the file, its log and its reasoning stay in the
    repo, which is the same convention every dropped course here follows. The
    build skips waived courses, so it disappears from the site and the totals.
    """
    if filename not in known_files():
        raise ValueError(f"unknown course file: {filename!r}")
    path = COURSE_DIR / filename
    text = path.read_text(encoding="utf-8")
    text = set_field(text, "Status", "waived")
    text = set_field(text, "Semester", "—")
    text = re.sub(r"^\*\*Order:\*\*.*\n", "", text, count=1, flags=re.MULTILINE)
    path.write_text(text, encoding="utf-8")
    return filename


def next_order(label: str) -> int:
    """One past the highest explicit Order already in that semester."""
    highest = 0
    for path in COURSE_DIR.glob("*.md"):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(rf"^\*\*Semester:\*\* {re.escape(label)}\s*$", text, re.MULTILINE):
            found = re.search(r"^\*\*Order:\*\*[ \t]*([\d.]+)", text, re.MULTILINE)
            if found:
                highest = max(highest, int(float(found.group(1))))
    return highest + 1


def add_course(label: str, code: str, name: str, credits: str) -> str:
    """Scaffold a new course file, placed at the end of the given semester."""
    if label not in VALID_SEMESTERS:
        raise ValueError(f"unknown semester: {label!r}")
    code, name = code.strip(), name.strip()
    if not code or not name:
        raise ValueError("code and name are both required")
    try:
        credits = f"{float(credits):g}"
    except (TypeError, ValueError):
        raise ValueError(f"credits must be a number, got {credits!r}")

    filename = f"{slugify(code)}-{slugify(name)}.md"
    path = COURSE_DIR / filename
    if path.exists():
        raise ValueError(f"{filename} already exists")

    path.write_text(f"""# {code} — {name}

**Status:** planned
**Semester:** {label}
**Credits:** {credits}
**Fulfills:**
**Grade:**
**Order:** {next_order(label)}

---

## Why This Course Matters

[Added from the registration page. Fill in why this course is here.]

---

## Log

### {date.today().isoformat()} — Added to the plan

---

## Key Concepts

---

## Resources Used

---

## Connections
""", encoding="utf-8")
    return filename


def rebuild() -> None:
    for script in ("build.py", "sync_schedule.py",
                   "sync_course_plan.py", "sync_index.py"):
        subprocess.run([sys.executable, str(ROOT / "tools" / script)],
                       capture_output=True)


# ── Server ───────────────────────────────────────────────────────────────────

class EditHandler(http.server.SimpleHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        # Always serve the freshest build after a reorder.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def do_GET(self) -> None:
        if self.path.split("?")[0] == "/api/ping":
            self._json(200, {"ok": True})
            return
        super().do_GET()

    def do_POST(self) -> None:
        route = self.path.split("?")[0]
        if route not in ("/api/reorder", "/api/remove", "/api/add"):
            self.send_error(404, "No such endpoint")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            if route == "/api/reorder":
                changed = apply_reorder(payload.get("semesters", []))
                verb = "reordered"
            elif route == "/api/remove":
                changed = [remove_course(payload.get("file", ""))]
                verb = "removed"
            else:
                changed = [add_course(payload.get("semester", ""),
                                      payload.get("code", ""),
                                      payload.get("name", ""),
                                      payload.get("credits", ""))]
                verb = "added"
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        rebuild()
        # flush: stdout is block-buffered when this runs detached from a terminal.
        print(f"  {verb}: {', '.join(changed) if changed else '(no change)'}",
              flush=True)
        self._json(200, {"ok": True, "changed": changed})

    def log_message(self, fmt: str, *args) -> None:
        pass  # keep the console focused on reorder output


def kill_port(port: int) -> None:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True
        )
        for pid in result.stdout.strip().splitlines():
            os.kill(int(pid), signal.SIGTERM)
    except Exception:
        pass


def find_free_port(start: int) -> int:
    kill_port(start)
    for port in range(start, start + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError("No free port found in range.")


def main() -> int:
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")])
    if result.returncode != 0:
        return result.returncode

    if not SITE_DIR.exists():
        sys.stderr.write("site/ does not exist after build — aborting.\n")
        return 1

    port = find_free_port(START_PORT)
    handler = functools.partial(EditHandler, directory=str(SITE_DIR))

    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"Serving site/ at {url}")
        print("Registration page is drag-editable while this server runs.")
        print("Ctrl-C to stop.")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
