"""Simulated leak copies for tests and the demo. Every output here is SIMULATED.

Questions are real bank items; decoys are real JEE questions that are not in the bank. Noise models a
hand-copied, OCR'd paper (ASSUMED rates). A real paraphrase or translation is not modelled.
"""
import random

ALPHA = "abcdefghijklmnopqrstuvwxyz "

KINDS = {
    # kind: (source node(s), share of held items leaked, char error rate, share of each question copied, words dropped)
    "line": (["C3"], 0.75, 0.08, 0.8, 0.0),
    "press": (["P2"], 0.75, 0.08, 0.8, 0.0),
    "small": (["C5"], 0.20, 0.08, 0.8, 0.0),
    "heavy": (["C1"], 0.75, 0.20, 0.6, 0.0),
    "rewrite70": (["C2"], 0.75, 0.08, 1.0, 0.7),
    "two": (["C1", "C6"], 0.50, 0.08, 0.8, 0.0),
    "setter": (["SETTER"], 0.75, 0.08, 0.8, 0.0),
    "panel": (["PANEL:chem"], 0.75, 0.08, 0.8, 0.0),
    "shared": (["SHARED"], 0.80, 0.08, 0.8, 0.0),
    "null": ([], 0.0, 0.08, 0.8, 0.0),
}


def noisy(text, e, keep, rng):
    t = text[:max(60, int(len(text) * keep))]
    out = []
    for ch in t:
        r = rng.random()
        if r < e / 3:
            continue
        if r < 2 * e / 3:
            out.append(rng.choice(ALPHA))
            continue
        out.append(ch)
        if r < e:
            out.append(rng.choice(ALPHA))
    return "".join(out)


def rewrite(text, drop, rng):
    words = [w for w in text.split() if rng.random() > drop]
    rng.shuffle(words)
    return " ".join(words)


def leak(design, sources, frac, e, keep, drop, decoys, rng):
    """Return (questions, leaked_items). `sources` are custody nodes, 'SHARED' or nothing (null)."""
    leaked = []
    for node in sources:
        items = design.shared if node == "SHARED" else design.holdings(node)
        leaked += rng.sample(items, max(1, round(frac * len(items))))
    tx = (lambda t: rewrite(t, drop, rng)) if drop else (lambda t: t)
    qs = [noisy(tx(x["text"]), e, keep, rng) for x in leaked]
    qs += [noisy(tx(d["text"]), e, keep, rng) for d in decoys]
    rng.shuffle(qs)
    return qs, leaked


def guess_paper(design, decoys, kind="line", seed=1):
    """A numbered 'guess paper' as plain text, plus the truth for the demo's answer key."""
    sources, frac, e, keep, drop = KINDS[kind]
    rng = random.Random(seed)
    qs, leaked = leak(design, sources, frac, e, keep, drop, decoys, rng)
    text = "\n\n".join(f"Q{i}. {q}" for i, q in enumerate(qs, 1))
    truth = {"kind": kind, "sources": sources or ["none"], "real_questions": len(leaked),
             "decoys": len(decoys), "label": "SIMULATED leak copy built from real JEE questions"}
    return text, truth
