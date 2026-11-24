"""Print one form, press or the setter's copy as numbered text, for the real-copy test.

    python3 scripts/export_form.py C3 > form_C3.txt      # what a candidate on line C3 sits
    python3 scripts/export_form.py P2 > press_P2.txt     # everything press 2 holds
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead.design import Design  # noqa: E402

node = sys.argv[1] if len(sys.argv) > 1 else "C0"
items = Design.load().holdings(node)
print("\n\n".join(f"{i}. {b['text']}" for i, b in enumerate(items, 1)))
