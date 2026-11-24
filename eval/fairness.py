"""Fairness after a leak: how much ranking accuracy is lost when the unaffected candidates are scored on their
line's own questions only (percentile within the line), instead of the full paper?

    python3 eval/fairness.py            # needs numpy

Model (ASSUMED): candidate ability ~ N(0, 1); items follow a 2-parameter logistic IRT model with
discrimination a ~ U(0.8, 1.6) and difficulty b ~ N(0, 1); each line's own block is made deliberately easier
or harder (block mean shifted by -0.4 to +0.4); candidates are assigned to lines at random. Everything here is
SIMULATED; it shows the size of the trade-off, not a validated psychometric result.
"""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RNG = np.random.default_rng(42)
N, G = 200_000, 8


def responses(theta, a, b):
    p = 1 / (1 + np.exp(-a * (theta[:, None] - b[None, :])))
    return (RNG.random(p.shape) < p).sum(1)


def rank_corr(x, y):
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def top_overlap(true, est, q=0.01):
    k = int(len(true) * q)
    return len(set(np.argsort(-true)[:k]) & set(np.argsort(-est)[:k])) / k


def within_line_percentile(score, line):
    out = np.empty(len(score))
    for c in range(G):
        idx = np.where(line == c)[0]
        order = np.sort(score[idx])
        out[idx] = 100 * np.searchsorted(order, score[idx], side="right") / len(idx)
    return out


def run(shared_n, own_n):
    theta = RNG.standard_normal(N)
    line = RNG.integers(0, G, N)
    a_s, b_s = RNG.uniform(.8, 1.6, shared_n), RNG.standard_normal(shared_n)
    shifts = np.linspace(-.4, .4, G)
    shared = responses(theta, a_s, b_s)
    own = np.empty(N)
    for c in range(G):
        idx = np.where(line == c)[0]
        a_o, b_o = RNG.uniform(.8, 1.6, own_n), RNG.standard_normal(own_n) + shifts[c]
        own[idx] = responses(theta[idx], a_o, b_o)
    full_pct = within_line_percentile(shared + own, line)        # no leak: whole paper, per-line percentile
    own_pct = within_line_percentile(own, line)                  # after a leak: own block only
    own_raw = own                                                 # same, but without percentile scoring
    return {"items": f"{shared_n + own_n} per form, {own_n} own",
            "rank_corr_full": round(rank_corr(theta, full_pct), 3),
            "rank_corr_own_percentile": round(rank_corr(theta, own_pct), 3),
            "rank_corr_own_raw": round(rank_corr(theta, own_raw), 3),
            "top1pct_full": round(top_overlap(theta, full_pct + RNG.random(N) * 1e-6), 3),
            "top1pct_own_percentile": round(top_overlap(theta, own_pct + RNG.random(N) * 1e-6), 3)}


def main():
    rows = [run(30, 30), run(90, 90)]
    with open(os.path.join(ROOT, "results", "fairness.json"), "w") as f:
        json.dump({"candidates": N, "lines": G, "rows": rows, "label": "SIMULATED (2PL IRT, ASSUMED)"}, f, indent=1)
    lines = ["# Fairness after a leak (SIMULATED, 2PL IRT, own blocks of unequal difficulty)", "",
             f"{N:,} candidates, {G} lines, assigned at random. Rank correlation with true ability, and the share "
             "of the true top 1% that the score also puts in its top 1%.", "",
             "| Form | Whole paper (no leak) | Own block, percentile within line | Own block, raw marks | Top 1% kept: whole / own |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['items']} | {r['rank_corr_full']} | {r['rank_corr_own_percentile']} | "
                     f"{r['rank_corr_own_raw']} | {r['top1pct_full']} / {r['top1pct_own_percentile']} |")
    with open(os.path.join(ROOT, "results", "fairness.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
