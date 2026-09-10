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

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == "/":
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())
            return
            
        elif path == "/api/transcript":
            qs = urllib.parse.parse_qs(parsed_url.query)
            conv_id = qs.get("conversationId", [""])[0]
            if not conv_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing conversationId")
                return
            
            brain_dir = os.path.expanduser("~/.gemini/jetski/brain")
            transcript_path = os.path.join(brain_dir, conv_id, ".system_generated/logs/transcript.jsonl")
            
            lines = []
            if os.path.exists(transcript_path):
                with open(transcript_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                lines.append(json.loads(line))
                            except Exception as e:
                                pass
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(lines).encode('utf-8'))
            return
            
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Starting Agent Tracer on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), AgentTracerHandler)
    server.serve_forever()
