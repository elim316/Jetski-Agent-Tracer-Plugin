import os
import json
import time
import logging
import threading
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("ANTIGRAVITY_SIDECAR_WEB_PORT", "8080"))
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
_FETCH_TTL_SECONDS = 600
_last_fetch_ts = 0.0
_git_lock = threading.Lock()


def _run_git(*args, timeout=10):
    """Run a git command inside the plugin repository."""
    try:
        proc = subprocess.run(
            ["git", "-C", _REPO_ROOT, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def _check_update_status(force_fetch=False):
    """Return local/remote SHA, commits behind origin/main, and working tree status."""
    global _last_fetch_ts
    if not os.path.isdir(os.path.join(_REPO_ROOT, ".git")):
        return {"supported": False, "behind": 0}

    now = time.time()
    if force_fetch or (now - _last_fetch_ts) >= _FETCH_TTL_SECONDS:
        with _git_lock:
            _run_git("fetch", "origin", "main", "--quiet", timeout=12)
            _last_fetch_ts = time.time()

    _, local_sha, _ = _run_git("rev-parse", "--short", "HEAD")
    _, remote_sha, _ = _run_git("rev-parse", "--short", "origin/main")
    rc_cnt, behind_str, _ = _run_git("rev-list", "HEAD..origin/main", "--count")
    behind = int(behind_str) if (rc_cnt == 0 and behind_str.isdigit()) else 0

    commits = []
    if behind > 0:
        _, log_out, _ = _run_git("log", "HEAD..origin/main", "--oneline", "-n", "8")
        if log_out:
            commits = [line.strip() for line in log_out.splitlines() if line.strip()]

    _, status_out, _ = _run_git("status", "--porcelain", "--untracked-files=no")
    dirty = bool(status_out)

    return {
        "supported": True,
        "local_sha": local_sha,
        "remote_sha": remote_sha,
        "behind": behind,
        "dirty": dirty,
        "commits": commits,
    }


_SELF_FILE = os.path.abspath(__file__)
_STARTUP_MTIME = os.path.getmtime(_SELF_FILE) if os.path.exists(_SELF_FILE) else 0.0


def _perform_update():
    """Fetch origin/main and reset the plugin repository to the latest upstream commit."""
    global _last_fetch_ts
    with _git_lock:
        rc_fetch, _, err_fetch = _run_git("fetch", "origin", "main", "--quiet", timeout=15)
        if rc_fetch != 0:
            return {"ok": False, "error": err_fetch or "git fetch origin main failed"}
        _last_fetch_ts = time.time()
        rc_reset, _, err_reset = _run_git("reset", "--hard", "origin/main", timeout=10)
        if rc_reset != 0:
            return {"ok": False, "error": err_reset or "git reset --hard origin/main failed"}
        _, new_sha, _ = _run_git("rev-parse", "--short", "HEAD")
        return {"ok": True, "sha": new_sha}


def _background_maintenance_loop():
    """Continuously auto-sync clean clones every 15m and auto-restart if server.py changes on disk."""
    last_sync = 0.0
    while True:
        try:
            # 1. If server.py was updated on disk (via git pull/reset or edit), exit so
            # Jetski's `restart_policy: always` supervisor respawns the new server.py.
            if os.path.exists(_SELF_FILE) and os.path.getmtime(_SELF_FILE) != _STARTUP_MTIME:
                logging.info("server.py updated on disk; exiting for supervisor hot-restart.")
                os._exit(0)

            # 2. Every 15 minutes (and on initial startup), auto-update if working tree is clean.
            now = time.time()
            if (now - last_sync) >= 900:
                last_sync = now
                if os.path.isdir(os.path.join(_REPO_ROOT, ".git")):
                    _, status_out, _ = _run_git("status", "--porcelain", "--untracked-files=no")
                    if not status_out:
                        status = _check_update_status(force_fetch=True)
                        if status.get("behind", 0) > 0:
                            res = _perform_update()
                            if res.get("ok"):
                                logging.info(f"Auto-updated Agent Tracer to {res.get('sha')}")
        except Exception as e:
            logging.debug(f"Background maintenance tick skipped: {e}")
        time.sleep(5)


class AgentTracerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy logging
        pass

    def _transcript_path(self, conv_id, full=False):
        """Resolve a conversation's transcript file across Jetski and Antigravity.

        `transcript.jsonl` is the compact log (long fields abbreviated);
        `transcript_full.jsonl` carries the untruncated content.
        """
        name = "transcript_full.jsonl" if full else "transcript.jsonl"
        env_dir = os.environ.get("AGENT_TRACER_BRAIN_DIR")
        candidates = [
            *( [os.path.expanduser(env_dir)] if env_dir else [] ),
            os.path.expanduser("~/.gemini/jetski/brain"),
            os.path.expanduser("~/.gemini/antigravity/brain"),
        ]
        for brain_dir in candidates:
            candidate = os.path.join(brain_dir, conv_id, ".system_generated/logs", name)
            if os.path.exists(candidate):
                return candidate
        return os.path.join(candidates[0], conv_id, ".system_generated/logs", name)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            # Resolve via absolute path from root so it survives CWD inode replacements
            abs_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(abs_dir, "index.html")
            
            try:
                with open(html_path, "rb") as f:
                    self.wfile.write(f.read())
            except Exception as e:
                logging.error(f"Failed to serve index.html: {e}")
                self.wfile.write(b"Error: UI file not found or inaccessible.")
            return

        elif path == "/api/update-status":
            qs = urllib.parse.parse_qs(parsed_url.query)
            force = qs.get("force", ["0"])[0] == "1"
            self._send_json(_check_update_status(force_fetch=force))
            return
            
        elif path == "/api/transcript":
            qs = urllib.parse.parse_qs(parsed_url.query)
            conv_id = qs.get("conversationId", [""])[0]
            if not conv_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing conversationId")
                return

            # Clients send the highest step_index they already hold so we only
            # ship the tail. Transcripts grow into the megabytes, and re-sending
            # the whole file every poll is wasteful.
            try:
                since = int(qs.get("since", ["-1"])[0])
            except ValueError:
                since = -1

            transcript_path = self._transcript_path(conv_id, full=False)

            lines = []
            if os.path.exists(transcript_path):
                with open(transcript_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            step = json.loads(line)
                        except Exception:
                            continue
                        if step.get("step_index", -1) > since:
                            lines.append(step)

            self._send_json(lines)
            return

        elif path == "/api/step_full":
            # Serves the untruncated version of a single step so the inspector can
            # expand content that was abbreviated in the compact transcript.
            qs = urllib.parse.parse_qs(parsed_url.query)
            conv_id = qs.get("conversationId", [""])[0]
            try:
                want = int(qs.get("step", ["-1"])[0])
            except ValueError:
                want = -1
            if not conv_id or want < 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing conversationId or step")
                return

            full_path = self._transcript_path(conv_id, full=True)
            found = None
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            step = json.loads(line)
                        except Exception:
                            continue
                        if step.get("step_index") == want:
                            found = step
                            break

            self._send_json(found if found else {})
            return
            
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/update":
            res = _perform_update()
            self._send_json(res, status=200 if res.get("ok") else 500)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=_background_maintenance_loop, daemon=True).start()
    logging.info(f"Starting Agent Tracer on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), AgentTracerHandler)
    server.serve_forever()
