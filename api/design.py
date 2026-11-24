"""GET /api/design  ->  compartments, presses, bank size, tau and the presence rule."""
import os
import sys

from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead.web import send  # noqa: E402
from bulkhead.service import design_info  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        send(self, 200, design_info())
