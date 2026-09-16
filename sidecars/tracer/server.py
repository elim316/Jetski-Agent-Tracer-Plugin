import os
import json
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("ANTIGRAVITY_SIDECAR_WEB_PORT", "8080"))

class AgentTracerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy logging
        pass

    def _transcript_path(self, conv_id, full=False):
        """Resolve a conversation's transcript file.

        `transcript.jsonl` is the compact log (long fields abbreviated);
        `transcript_full.jsonl` carries the untruncated content.
        """
        brain_dir = os.path.expanduser("~/.gemini/jetski/brain")
        name = "transcript_full.jsonl" if full else "transcript.jsonl"
        return os.path.join(brain_dir, conv_id, ".system_generated/logs", name)

    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Starting Agent Tracer on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), AgentTracerHandler)
    server.serve_forever()
