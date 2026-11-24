"""Reproduce the BULKHEAD results table.

    python3 eval/run_eval.py              # 200 trials per scenario; uses scikit-learn if installed
    python3 eval/run_eval.py --trials 50  # quicker
    python3 eval/run_eval.py --pure       # dependency-free engine only (slower, same numbers)

Labels: question text is REAL (JEEBench). Leak copies are SIMULATED from it with ASSUMED noise.
The design (60 slots, 8 compartments, 4 presses) is ASSUMED. Writes results/eval.json and results/eval.md.
"""
import argparse
import json
import os
import platform
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bulkhead.decoder import Decoder  # noqa: E402
from bulkhead.design import DATA_DIR, Design  # noqa: E402
from bulkhead.leaks import leak, noisy, rewrite  # noqa: E402

SEED = 11


class SkTfidf:
    """scikit-learn twin of bulkhead.textsim.CharTfidf (tests/test_parity.py checks they agree)."""

    def __init__(self, docs):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self.M = self.vec.fit_transform(docs)

    def best_many(self, texts):
        if not texts:
            return []
        sims = (self.vec.transform(texts) @ self.M.T).toarray()
        return [(int(i), float(sims[r, i])) if sims[r, i] > 0 else (-1, 0.0)
                for r, i in enumerate(sims.argmax(1))]


SCENARIOS = [
    # name, sources, truth, share leaked, char error, share copied, words dropped, decoy multiplier
    ("Line leak: 75% of one form, 2:1 decoys", ["C3"], ("NAMED", ["C3"]), .75, .08, .8, 0, 1),
    ("Press leak: both lines of one press", ["P2"], ("NAMED", ["P2"]), .75, .08, .8, 0, 1),
    ("Small leak: 12 questions", ["C5"], ("NAMED", ["C5"]), .20, .08, .8, 0, 1),
    ("Heavy noise: 20% char errors, 60% copied", ["C1"], ("NAMED", ["C1"]), .75, .20, .6, 0, 1),
    ("Rewritten: 50% of words dropped, shuffled", ["C2"], ("NAMED", ["C2"]), .75, .08, 1.0, .5, 1),
    ("Rewritten: 70% of words dropped, shuffled", ["C2"], ("NAMED", ["C2"]), .75, .08, 1.0, .7, 1),
    ("Two leakers, different presses", ["C1", "C6"], ("MULTIPLE", ["C1", "C6"]), .5, .08, .8, 0, 1),
    ("Setter leak: master copy", ["SETTER"], ("NAMED", ["SETTER"]), .75, .08, .8, 0, 1),
    ("Setter side: one subject panel (chemistry)", ["PANEL:chem"], ("NAMED", ["SETTER"]), .75, .08, .8, 0, 1),
    ("Shared block only", ["SHARED"], ("SHARED ONLY", []), .8, .08, .8, 0, 1),
    ("Null: real decoys only", [], ("NOT FOUND", []), 0, .08, .8, 0, 1),
    ("Null, rewritten decoys (70% dropped)", [], ("NOT FOUND", []), 0, .08, 1.0, .7, 1),
    ("Flood: line leak inside 1,080 decoys", ["C3"], ("NAMED", ["C3"]), .75, .08, .8, 0, 10),
    ("Flood null: 1,080 decoys, no leak", [], ("NOT FOUND", []), 0, .08, .8, 0, 10),
]


def compartments_of(design, sources):
    out = set()
    for s in sources:
        if s == "SETTER" or s.startswith("PANEL:"):
            out |= set(range(design.compartments))
        elif s in design.presses:
            out |= set(design.presses[s])
        elif s.startswith("C"):
            out.add(int(s[1:]))
    return out


def run_scenario(design, dec, decoys, spec, trials, rng):
    name, sources, (want_v, want_n), frac, e, keep, drop, mult = spec
    true_c = compartments_of(design, sources)
    ok = false_c = 0
    recalls, sizes, worst_all = [], [], 0
    for _ in range(trials):
        pool = decoys * mult
        qs, leaked = leak(design, sources, frac, e, keep, drop, pool, rng)
        r = dec.decode(qs)
        sizes.append(len(qs))
        want_panel = next((x[6:] for x in sources if x.startswith("PANEL:")), None)
        ok += (r["verdict"] == want_v and sorted(r["nodes"]) == sorted(want_n)
               and r["panel"] == want_panel)
        false_c += len(set(r["present"]) - true_c)
        if leaked:
            got = {m["bank_id"] for m in r["matches"]}
            ids = {x["id"] for x in leaked}          # two holders can leak the same shared item
            recalls.append(len(got & ids) / len(ids))
        # Leaked questions that would still count toward someone's score after the response.
        leaked_ids = {x["id"] for x in leaked}
        worst = 0
        # A setter verdict re-tests every line (a panel verdict: every line, one subject).
        retested = set(range(design.compartments)) if r["nodes"] == ["SETTER"] else set(r["present"])
        for c in range(design.compartments):
            if c in retested:
                continue
            kept = [b for b in design.unique[c]] + ([] if r["response"] else design.shared)
            worst = max(worst, sum(1 for b in kept if b["id"] in leaked_ids))
        worst_all = max(worst_all, worst)
    return {"scenario": name, "source_named": ok / trials, "false_compartments": false_c / trials,
            "exposed": len(true_c) / design.compartments if true_c else 0.0,
            "leaked_yet_scored_worst": worst_all,
            "recall": round(statistics.mean(recalls), 3) if recalls else None,
            "paper_questions": int(statistics.median(sizes))}


def matcher_rates(design, model, decoys, rng, reps=20):
    bank_texts = [b["text"] for b in design.bank]
    pos = [s for _ in range(reps // 4) for _, s in model.best_many([noisy(t, .08, .8, rng) for t in bank_texts])]
    clean = [s for _, s in model.best_many([d["text"] for d in decoys])]
    neg = [s for _ in range(reps) for _, s in model.best_many([noisy(d["text"], .08, .8, rng) for d in decoys])]
    rew = [s for _ in range(reps) for _, s in model.best_many(
        [noisy(rewrite(d["text"], .7, rng), .08, 1.0, rng) for d in decoys])]
    t = design.tau
    return {"recall_noisy_bank": sum(s >= t for s in pos) / len(pos),
            "false_match_clean_decoys": sum(s >= t for s in clean) / len(clean),
            "false_match_noisy_decoys": sum(s >= t for s in neg) / len(neg),
            "false_match_rewritten_decoys": sum(s >= t for s in rew) / len(rew),
            "noisy_decoy_queries": len(neg), "bound_used_by_decoder": design.false_match_upper}


class _Wrap:
    """Adds the response flag the residual check needs without importing the API layer."""

    def __init__(self, dec):
        self.dec = dec

    def decode(self, qs):
        r = self.dec.decode(qs)
        r["response"] = r["verdict"] != "NOT FOUND"   # any detection drops the shared block
        return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--pure", action="store_true")
    a = ap.parse_args()
    design = Design.load()
    with open(os.path.join(DATA_DIR, "decoys.json"), encoding="utf-8") as f:
        decoys = json.load(f)["test"]
    engine = "pure-python"
    model = None
    if not a.pure:
        try:
            SkTfidf([b["text"] for b in design.bank[:3]])
            model = SkTfidf
            engine = "scikit-learn"
        except ImportError:
            pass
    dec = Decoder(design, factory=model)
    rng = random.Random(SEED)
    t0 = time.time()
    rates = matcher_rates(design, dec.model, decoys, rng)
    rows = [run_scenario(design, _Wrap(dec), decoys, s, a.trials, rng) for s in SCENARIOS]
    out = {"design": design.summary(), "engine": engine, "trials": a.trials, "seed": SEED,
           "python": platform.python_version(), "seconds": round(time.time() - t0, 1),
           "matcher": rates, "scenarios": rows,
           "labels": {"question_text": "REAL (JEEBench, MIT)", "leak_copies": "SIMULATED",
                      "noise_and_design": "ASSUMED"}}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "eval.json"), "w") as f:
        json.dump(out, f, indent=1)
    lines = [f"# BULKHEAD evaluation ({a.trials} trials per scenario, engine: {engine})", "",
             "Question text REAL (JEEBench, MIT). Leak copies SIMULATED. Noise and design ASSUMED.", "",
             f"tau {design.tau} | recall on noisy bank items {rates['recall_noisy_bank']:.3f} | false matches "
             f"per held-out decoy: clean {rates['false_match_clean_decoys']:.4f}, noisy "
             f"{rates['false_match_noisy_decoys']:.4f}, rewritten {rates['false_match_rewritten_decoys']:.4f} "
             f"(decoder assumes at most {design.false_match_upper})", "",
             "| Scenario | Source named | False compartments | Re-tested | Leaked yet scored (worst) | Recall | Questions |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        rec = "n/a" if r["recall"] is None else f"{r['recall']:.3f}"
        lines.append(f"| {r['scenario']} | {r['source_named']:.3f} | {r['false_compartments']:.3f} | "
                     f"{r['exposed']:.3f} | {r['leaked_yet_scored_worst']} | {rec} | {r['paper_questions']} |")
    with open(os.path.join(ROOT, "results", "eval.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n{out['seconds']} s")


if __name__ == "__main__":
    main()
