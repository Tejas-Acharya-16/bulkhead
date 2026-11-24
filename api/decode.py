"""POST /api/decode  {"text": "<leaked or guess paper>"}  ->  verdict, custody nodes, evidence, response."""
import os
import sys

from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead.web import read_json, send  # noqa: E402
from bulkhead.service import decode_text  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            out = decode_text(read_json(self).get("text", ""))
        except ValueError as e:
            return send(self, 400, {"error": str(e)})
        send(self, 400 if "error" in out else 200, out)

    def do_GET(self):
        send(self, 405, {"error": "Send a POST with JSON {\"text\": \"...\"}."})
