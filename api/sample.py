"""GET /api/sample?kind=line&seed=1  ->  a SIMULATED guess paper built from real JEE questions, plus the truth."""
import os
import sys

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead.web import send  # noqa: E402
from bulkhead.service import sample  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        kind = q.get("kind", ["line"])[0]
        try:
            seed = int(q.get("seed", ["1"])[0]) % 100_000
        except ValueError:
            return send(self, 400, {"error": "seed must be a whole number."})
        out = sample(kind, seed)
        send(self, 400 if "error" in out else 200, out)
