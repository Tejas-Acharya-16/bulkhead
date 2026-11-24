"""Read a leaked or 'guess' paper and name the smallest custody node that could have held it.

Truth/speed split: the verdict depends only on set membership (which bank items appear) and the
custody map. Matching text to items is the speed layer; a weaker matcher can only make the
verdict NOT FOUND (fall back to today's practice), never name a wrong compartment while tau holds.
"""
import math
import re
from collections import Counter

from .textsim import CharTfidf, strip_math

PANEL_MIN, PANEL_SHARE = 10, 0.9
WORDS_MIN, WORDS_Q_MIN = 80, 60    # words-only channel: bank items and questions with enough prose

# "12.", "12)", "Q12." and OCR's usual misreads of a Q-number ("QI2.", "Ql.", "QO3.")
_NUMBERED = re.compile(r"(?m)^\s*(?:Q\s*\.?\s*[0-9IlO|]{1,3}|\d{1,3})\s*[.):]\s+")


def split_questions(text, min_len=40, merge_below=120):
    """Split pasted text into questions.

    Numbered lines ('12.', 'Q12)', '12:') win when there are 3 or more, because JEE/NEET questions
    themselves contain blank lines (options, passages). Otherwise split on blank lines and glue any
    short block (an option list, a stray line) onto the block before it, so fragments are not matched
    on their own.
    """
    text = text.replace("\r\n", "\n")
    if len(_NUMBERED.findall(text)) >= 3:
        blocks = [p.strip() for p in _NUMBERED.split(text)]
    else:
        blocks = []
        for b in (x.strip() for x in re.split(r"\n\s*\n", text)):
            if not b:
                continue
            if blocks and len(b) < merge_below:
                blocks[-1] += "\n" + b
            else:
                blocks.append(b)
    return [b for b in blocks if len(b) >= min_len]


def poisson_tail(k, lam):
    """P(X >= k) for X ~ Poisson(lam)."""
    term, cdf = math.exp(-lam), 0.0
    for i in range(k):
        cdf += term
        term *= lam / (i + 1)
    return max(0.0, 1.0 - cdf)


def presence_needed(n_questions, design):
    """Unique-item hits a compartment needs before it counts as present.

    At least design.presence_t (3). For long papers, also enough that false matches alone would
    reach it with probability <= design.alpha: each question falsely matches with probability at
    most false_match_upper, and lands in a given compartment's unique block in proportion to its size.
    """
    share = len(design.unique[0]) / len(design.bank)
    lam = n_questions * design.false_match_upper * share
    k = design.presence_t
    while poisson_tail(k, lam) > design.alpha:
        k += 1
    return k


def name_node(present, shared_hits, design):
    """Smallest custody node(s) covering every present compartment."""
    if not present:
        return ("SHARED ONLY" if shared_hits else "NOT FOUND"), []
    if len(present) == design.compartments:
        return "NAMED", ["SETTER"]
    nodes = []
    for press, cs in design.presses.items():
        got = [c for c in present if c in cs]
        if len(got) == len(cs):
            nodes.append(press)
        nodes += [f"C{c}" for c in got if len(got) < len(cs)]
    return ("NAMED" if len(nodes) == 1 else "MULTIPLE"), nodes


class Decoder:
    def __init__(self, design, factory=None):
        """Two matchers over the same bank: the full text (formulas included) and its words only, for
        copies that lost their formulas to OCR or haste. `factory(docs)` returns a fitted model with
        best_many(texts) -> [(bank_index, cosine)]; default is the dependency-free CharTfidf. The eval
        harness passes a faster scikit-learn twin."""
        fit = factory or (lambda docs: CharTfidf().fit(docs))
        self.design = design
        self.model = fit([b["text"] for b in design.bank])
        words = [strip_math(b["text"]) for b in design.bank]
        self.words_ok = [len(w) >= WORDS_MIN for w in words]
        self.words = fit([w if ok else "" for w, ok in zip(words, self.words_ok)])

    def match(self, questions):
        """(bank_index, score, channel) per question, or (-1, 0.0, None) below both thresholds."""
        d = self.design
        full = self.model.best_many(questions)
        wq = [strip_math(q) for q in questions]
        words = self.words.best_many([w if len(w) >= WORDS_Q_MIN else "" for w in wq])
        out = []
        for (i, s), (j, sw) in zip(full, words):
            if i >= 0 and s >= d.tau:
                out.append((i, s, "full"))
            elif d.tau_words and j >= 0 and self.words_ok[j] and sw >= d.tau_words:
                out.append((j, sw, "words"))
            else:
                out.append((-1, 0.0, None))
        return out

    def decode(self, questions):
        d = self.design
        best = {}
        for line, (q, (i, s, via)) in enumerate(zip(questions, self.match(questions)), 1):
            if i < 0:
                continue
            item = d.bank[i]
            if item["id"] not in best or s > best[item["id"]]["score"]:
                best[item["id"]] = {"line": line, "bank_id": item["id"], "block": item["block"],
                                    "slot": d.slot[item["id"]],
                                    "subject": item["subject"], "source": item["source"],
                                    "score": round(s, 3), "via": via, "excerpt": q[:110]}
        per = Counter(m["block"] for m in best.values())
        hits = {c: per.get(c, 0) for c in range(d.compartments)}
        need = presence_needed(len(questions), d)
        present = sorted(c for c, k in hits.items() if k >= need)
        verdict, nodes = name_node(present, per.get("S", 0), d)
        # Upstream of printing, the setting stage is split by subject. If nearly every match is one
        # subject, the leak points at that subject's setters and translators.
        subj = Counter(m["subject"] for m in best.values())
        top, top_n = (subj.most_common(1) or [(None, 0)])[0]
        panel = top if len(best) >= PANEL_MIN and top_n >= PANEL_SHARE * len(best) else None
        # One subject only, across 3+ presses: line leakers would leak every subject of their forms,
        # so this pattern points upstream of printing, to that subject's setters and translators.
        if panel and verdict == "MULTIPLE":
            presses = {p for p, cs in d.presses.items() if any(c in cs for c in present)}
            if len(presses) >= 3:
                verdict, nodes = "NAMED", ["SETTER"]
        return {
            "verdict": verdict,
            "nodes": nodes,
            "present": present,
            "hits": hits,
            "shared_hits": per.get("S", 0),
            "by_subject": dict(subj),
            "panel": panel,
            "questions_read": len(questions),
            "matched": len(best),
            "matches": sorted(best.values(), key=lambda m: m["line"]),
            "commitment": getattr(d, "commitment", None),
            "rule": {"tau": d.tau, "tau_words": d.tau_words, "presence_needed": need, "alpha": d.alpha,
                     "false_match_upper": d.false_match_upper},
        }
