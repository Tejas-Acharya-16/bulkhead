"""Run BULKHEAD locally with no dependencies:  python3 server.py  ->  http://localhost:8000

Serves public/ and the same three endpoints as the Vercel functions in api/.
"""
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from bulkhead.service import decode_text, design_info, sample  # noqa: E402
from bulkhead.web import read_json, send  # noqa: E402


with open(os.path.join(ROOT, "vercel.json"), encoding="utf-8") as _f:
    HEADERS = [(h["key"], h["value"]) for h in json.load(_f)["headers"][0]["headers"]]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(ROOT, "public"), **k)

    def end_headers(self):                       # same security headers as the Vercel deployment
        for k, v in HEADERS:
            self.send_header(k, v)
        super().end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/design":
            return send(self, 200, design_info())
        if url.path == "/api/sample":
            q = parse_qs(url.query)
            try:
                seed = int(q.get("seed", ["1"])[0]) % 100_000
            except ValueError:
                return send(self, 400, {"error": "seed must be a whole number."})
            out = sample(q.get("kind", ["line"])[0], seed)
            return send(self, 400 if "error" in out else 200, out)
        if url.path.startswith("/api/"):
            return send(self, 404, {"error": "Unknown endpoint."})
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/decode":
            return send(self, 404, {"error": "Unknown endpoint."})
        try:
            out = decode_text(read_json(self).get("text", ""))
        except ValueError as e:
            return send(self, 400, {"error": str(e)})
        send(self, 400 if "error" in out else 200, out)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"BULKHEAD on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
