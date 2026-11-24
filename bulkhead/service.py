"""Shared entry points for the serverless API, the local server and the CLI."""
import json
import os

from .decoder import Decoder, split_questions
from .design import DATA_DIR, Design
from .leaks import KINDS, guess_paper
from .response import respond

MAX_CHARS = 300_000
MAX_QUESTIONS = 1500
ILLUSTRATIVE_CANDIDATES = 2_200_000   # NEET-scale round number, ILLUSTRATIVE only

_state = {}


def _load():
    if not _state:
        design = Design.load()
        with open(os.path.join(DATA_DIR, "decoys.json"), encoding="utf-8") as f:
            decoys = json.load(f)
        _state.update(design=design, decoder=Decoder(design), decoys=decoys["test"])
    return _state


def decode_text(text):
    s = _load()
    if not isinstance(text, str) or not text.strip():
        return {"error": "Paste the text of a leaked or guess paper."}
    if len(text) > MAX_CHARS:
        return {"error": f"Text too long: limit is {MAX_CHARS} characters."}
    questions = split_questions(text)[:MAX_QUESTIONS]
    result = s["decoder"].decode(questions)
    result["response"] = respond(result, s["design"], candidates=ILLUSTRATIVE_CANDIDATES)
    result["design"] = s["design"].summary()
    return result


def sample(kind="line", seed=1):
    s = _load()
    if kind not in KINDS:
        return {"error": f"Unknown sample. Choose one of: {', '.join(KINDS)}."}
    text, truth = guess_paper(s["design"], s["decoys"], kind, int(seed))
    return {"text": text, "truth": truth}


def design_info():
    return _load()["design"].summary()
