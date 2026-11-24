"""Baselines run on the same simulated leaks as Bulkhead.

    python3 eval/baselines.py --trials 50

For each leak source (a print line, a press, the setter, the chemistry setters, nobody) the leak is drawn
from what that insider would hold UNDER EACH DESIGN, copied with the same noise, mixed with the same real
decoys, and matched with the same matcher. Each design then answers with its own rule:

  B0  One paper for everyone (today). Every node held every question.
  B1  B0 + a unique QR code or serial number on every copy (CBSE since 2018, Telangana 2025). A retyped or
      handwritten copy carries no code, so on text leaks B1 answers exactly like B0.
  B2  Eight sets, but every press prints every set (multi-set papers). The set is known; the press is not.
  BH  Bulkhead: sets keyed to the custody chain.

Reported: share of candidates who must re-sit (all subjects unless stated), whether the source node is named
uniquely, and how many custody nodes remain suspects. Labels: question text REAL, leaks SIMULATED, designs
ASSUMED (8 lines, 4 presses).
"""
import argparse
import json
import os
import random
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bulkhead.decoder import Decoder  # noqa: E402
from bulkhead.design import DATA_DIR, Design  # noqa: E402

SOURCES = [("Print line leak", "LINE"), ("Press leak", "PRESS"), ("Setter leak", "SETTER"),
           ("Chemistry setters only", "PANEL"), ("No leak (decoys only)", None)]
NODES = 1 + 4 + 8          # setter, presses, print lines


def holding(design, kind, scheme):
    """What the insider holds. Line = C3 (set 3), press = P2, panel = all chemistry."""
    if kind is None:
        return []
    if kind == "PANEL":
        return design.holdings("PANEL:chem")
    if kind == "SETTER" or scheme in ("B0", "B1"):
        return design.holdings("SETTER")
    if kind == "LINE":
        return design.holdings("C3")                        # one set either way
    return design.holdings("P2" if scheme == "BH" else "SETTER")   # B2: a press prints every set


def answer(scheme, r, design):
    """(re-sit share, section only?, source named?, suspects) from one decode."""
    present = set(r["present"])
    any_match = r["matched"] > 0
    panel = r["panel"] if r["nodes"] == ["SETTER"] or (scheme != "BH" and r["panel"]) else None
    if not any_match:
        return 0.0, False, True, 0
    if scheme in ("B0", "B1"):
        if panel:
            return 1.0, True, False, NODES
        return 1.0, False, False, NODES
    if scheme == "B2":
        if panel:
            return 1.0, True, False, 5          # setter or any press could hold every set's chemistry
        if not present:
            return 0.0, False, False, NODES
        share = len(present) / design.compartments
        suspects = 1 + 4 + (4 if len(present) == 1 else 0)   # setter + every press (+ a line at each)
        return (1.0 if len(present) == design.compartments else share), False, False, suspects
    named = r["verdict"] == "NAMED"
    share = r["response"]["retest_share"]
    return share, bool(r["response"].get("sections")), named, 1 if named else NODES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=50)
    a = ap.parse_args()
    from run_eval import SkTfidf
    from bulkhead.response import respond
    design = Design.load()
    with open(os.path.join(DATA_DIR, "decoys.json"), encoding="utf-8") as f:
        decoys = json.load(f)["test"]
    try:
        dec = Decoder(design, factory=SkTfidf)
    except ImportError:
        dec = Decoder(design)
    rng = random.Random(31)
    rows = []
    for label, kind in SOURCES:
        row = {"source": label}
        for scheme in ("B0", "B1", "B2", "BH"):
            shares, sections, named, suspects = [], 0, 0, []
            for _ in range(a.trials):
                qs = _leak_from(holding(design, kind, scheme), decoys, rng)
                r = dec.decode(qs)
                r["response"] = respond(r, design)
                s, sec, nm, sus = answer(scheme, r, design)
                shares.append(s)
                sections += sec
                named += nm
                suspects.append(sus)
            row[scheme] = {"resit": round(statistics.mean(shares), 3), "section_only": sections / a.trials,
                           "named": named / a.trials, "suspects": round(statistics.mean(suspects), 1)}
        rows.append(row)
        print(row, flush=True)
    with open(os.path.join(ROOT, "results", "baselines.json"), "w") as f:
        json.dump({"trials": a.trials, "rows": rows}, f, indent=1)
    names = {"B0": "One paper (today)", "B1": "+ QR/serial per copy", "B2": "8 sets, presses print all",
             "BH": "Bulkhead"}
    lines = [f"# Baselines on the same simulated leaks ({a.trials} trials per cell)", "",
             "Each cell: share of candidates who re-sit / source named / custody nodes still suspected "
             f"(of {NODES}). Text copies only: a QR code does not survive retyping.", "",
             "| Leak from | " + " | ".join(names.values()) + " |", "|---|---|---|---|---|"]
    for row in rows:
        cells = []
        for k in names:
            c = row[k]
            resit = f"{c['resit']:.1%}" + (" (1 section)" if c["section_only"] > 0.5 else "")
            cells.append(f"{resit} / {'yes' if c['named'] > 0.5 else 'no'} / {c['suspects']:g}")
        lines.append(f"| {row['source']} | " + " | ".join(cells) + " |")
    with open(os.path.join(ROOT, "results", "baselines.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def _leak_from(items, decoys, rng):
    from bulkhead.leaks import noisy
    leaked = rng.sample(items, round(0.75 * len(items))) if items else []
    qs = [noisy(x["text"], .08, .8, rng) for x in leaked] + [noisy(d["text"], .08, .8, rng) for d in decoys]
    rng.shuffle(qs)
    return qs


if __name__ == "__main__":
    main()
