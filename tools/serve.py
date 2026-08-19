#!/usr/bin/env python3
"""Build the site and serve it locally. Kills any existing server, finds a free port.

Serving locally also enables edit mode on the registration page: courses can be
dragged between and within semesters, and each drop writes straight back to
data/courses/*.md, then rebuilds. The published GitHub Pages copy has no such
endpoint, so it stays a static, read-only page.

Endpoints (localhost only):
    GET  /api/ping     -> {"ok": true}   the page's edit-mode probe
    POST /api/reorder  -> apply a new course arrangement
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


def rebuild() -> None:
    for script in ("build.py", "sync_schedule.py"):
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
        if self.path.split("?")[0] != "/api/reorder":
            self.send_error(404, "No such endpoint")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            changed = apply_reorder(payload.get("semesters", []))
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        rebuild()
        # flush: stdout is block-buffered when this runs detached from a terminal.
        print(f"  reordered: {', '.join(changed) if changed else '(no change)'}",
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
