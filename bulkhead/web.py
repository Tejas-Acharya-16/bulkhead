"""HTTP helpers shared by the Vercel functions (api/) and the local server."""
import json


MAX_BODY = 400_000


def send(h, status, obj):
    body = json.dumps(obj).encode("utf-8")
    h.send_response(status)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Cache-Control", "no-store")
    h.send_header("Content-Length", str(len(body)))
    h.end_headers()
    h.wfile.write(body)


def read_json(h):
    n = int(h.headers.get("Content-Length") or 0)
    if n <= 0:
        return {}
    if n > MAX_BODY:
        raise ValueError(f"Request too large: limit is {MAX_BODY} bytes.")
    return json.loads(h.rfile.read(n).decode("utf-8"))
