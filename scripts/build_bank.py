"""Build data/bank.json, data/decoys.json and data/design.json from JEEBench.

Source: JEEBench, dair-iitd/jeebench (MIT licence), 515 JEE Advanced questions 2016-2023.
    git clone https://github.com/dair-iitd/jeebench
    python3 scripts/build_bank.py jeebench/data/dataset.json

Steps (all deterministic, SEED = 7):
  1. Keep questions of 80+ characters.
  2. Remove near-duplicates (cosine > 0.5): JEE paragraph questions share a passage, so a decoy
     could otherwise be a sibling of a bank item.
  3. Per subject: 10 shared items, then 10 unique items for each of 8 compartments; the rest are
     decoys (real JEE questions NOT in the bank), split into a calibration half and a test half.
  4. tau = highest similarity any calibration decoy reaches against the bank, clean or with
     ASSUMED copy noise (5 draws each), + 0.02.
  5. false_match_upper: no calibration decoy reaches tau by construction, so the per-question false
     match rate is bounded by the rule of three, 3 / N. The decoder uses it to raise the presence
     threshold for very long papers (see decoder.presence_needed).
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead.design import commitment  # noqa: E402
from bulkhead.leaks import noisy  # noqa: E402
from bulkhead.decoder import WORDS_MIN, WORDS_Q_MIN  # noqa: E402
from bulkhead.textsim import CharTfidf, strip_math  # noqa: E402

SEED = 7
SUBJECTS = ("phy", "chem", "math")
SHARED_PER_SUBJ, UNIQUE_PER_SUBJ, G = 10, 10, 8
PRESSES = {"P1": [0, 1], "P2": [2, 3], "P3": [4, 5], "P4": [6, 7]}
PRESENCE_T = 3
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def dedupe(items, thr=0.5):
    model = CharTfidf().fit([x["question"] for x in items])
    keep, dropped = [], set()
    for i in range(len(items)):
        if i in dropped:
            continue
        keep.append(items[i])
        dropped.update(j for j, s in model.scores(items[i]["question"]).items() if j > i and s > thr)
    return keep, len(items) - len(keep)


def split(path):
    with open(path, encoding="utf-8") as f:
        items = [x for x in json.load(f) if len(x["question"]) >= 80]
    items, n_drop = dedupe(items)
    by = {s: [x for x in items if x["subject"] == s] for s in SUBJECTS}
    rng = random.Random(SEED)
    for s in SUBJECTS:
        rng.shuffle(by[s])
    shared, unique, decoys = [], {c: [] for c in range(G)}, []
    for s in SUBJECTS:
        pool = by[s]
        shared += pool[:SHARED_PER_SUBJ]
        k = SHARED_PER_SUBJ
        for c in range(G):
            unique[c] += pool[k:k + UNIQUE_PER_SUBJ]
            k += UNIQUE_PER_SUBJ
        decoys += pool[k:]
    rng.shuffle(decoys)
    half = len(decoys) // 2
    return shared, unique, decoys[:half], decoys[half:], len(items), n_drop


def rec(x, block, n):
    return {"id": f"Q{n:03d}", "subject": x["subject"], "block": block, "text": x["question"],
            "source": f"{x['description']}, Q{x['index']}"}


def main(path):
    shared, unique, cal, test, kept, dropped = split(path)
    bank = [rec(x, "S", 0) for x in shared]
    for c in range(G):
        bank += [rec(x, c, 0) for x in unique[c]]
    for n, b in enumerate(bank, 1):
        b["id"] = f"Q{n:03d}"
    model = CharTfidf().fit([b["text"] for b in bank])
    rng = random.Random(SEED + 1)
    null = [model.best(d["question"])[1] for d in cal]
    null += [model.best(noisy(d["question"], 0.08, 0.8, rng))[1] for _ in range(5) for d in cal]
    tau = round(max(null) + 0.02, 4)
    fm_upper = round(3 / len(null), 5)
    # Words-only channel: same bank with formulas removed; calibrated the same way, on the words of
    # clean decoys, of noisy decoys, and of noisy copies of their words.
    words = [strip_math(b["text"]) for b in bank]
    ok = [len(w) >= WORDS_MIN for w in words]
    wmodel = CharTfidf().fit([w if k else "" for w, k in zip(words, ok)])
    wq = [strip_math(d["question"]) for d in cal]
    wq += [strip_math(noisy(d["question"], 0.08, 0.8, rng)) for _ in range(5) for d in cal]
    wq += [noisy(strip_math(d["question"]), 0.08, 0.8, rng) for _ in range(5) for d in cal]
    wnull = [s for i, s in (wmodel.best(q) for q in wq if len(q) >= WORDS_Q_MIN) if i >= 0 and ok[i]]
    tau_words = round(max(wnull) + 0.02, 4)
    dec = {k: [{"text": d["question"], "subject": d["subject"],
                "source": f"{d['description']}, Q{d['index']}"} for d in v]
           for k, v in (("calibration", cal), ("test", test))}
    design = {"compartments": G, "presses": PRESSES, "presence_t": PRESENCE_T, "tau": tau,
              "tau_words": tau_words, "words_items": sum(ok), "words_calibration_queries": len(wnull),
              "false_match_upper": fm_upper, "alpha": 1e-4, "calibration_queries": len(null),
              "seed": SEED, "kept": kept, "near_duplicates_dropped": dropped,
              "calibration_null_max": round(max(null), 4),
              "source": "JEEBench (dair-iitd/jeebench, MIT licence)",
              "commitment": commitment(bank, G, PRESSES)}
    os.makedirs(OUT, exist_ok=True)
    for name, obj in (("bank", bank), ("decoys", dec), ("design", design)):
        with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f"kept {kept} (dropped {dropped} near-duplicates) | bank {len(bank)} | decoys "
          f"{len(cal)} calibration, {len(test)} test | tau {tau} | tau_words {tau_words} "
          f"({sum(ok)} items with enough words) | false-match bound {fm_upper}\n"
          f"commitment sha256 {design['commitment']}")


if __name__ == "__main__":
    main(sys.argv[1])
