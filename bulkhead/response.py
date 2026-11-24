"""The pre-agreed response to a decoded leak, and percentile normalisation within compartments."""
from bisect import bisect_right


def respond(result, design, candidates=None):
    g = design.compartments
    shared_n, unique_n = len(design.shared), len(design.unique[0])
    present = result["present"]
    share = len(present) / g
    verdict = result["verdict"]
    if verdict == "NOT FOUND":
        actions = ["No re-test: no question in this text matches the bank."]
    elif verdict == "SHARED ONLY":
        actions = ["No re-test: only shared questions leaked, so no source can be named.",
                   f"Drop the {shared_n} shared questions from every score; rank each candidate on "
                   f"their line's {unique_n} own questions."]
    else:
        retest = ", ".join(f"C{c}" for c in present)
        actions = [f"Re-test the candidates on line{'s' if len(present) > 1 else ''} {retest}: "
                   f"{share:.1%} of all candidates.",
                   f"Everyone else keeps their result: drop the {shared_n} shared questions and score them on "
                   f"their line's {unique_n} own questions, none of which are in this leak.",
                   "Compare scores by percentile within each line, as JEE Main already does for each shift.",
                   "Send the matched questions and the named line or press to investigators. "
                   "A name starts an investigation; it is not a finding of guilt."]
        if verdict == "MULTIPLE":
            actions.insert(1, "Look for separate leakers, or for one holder upstream of all of them.")
    sections = None
    if result.get("panel") and result["nodes"] == ["SETTER"]:
        names = {"phy": "physics", "chem": "chemistry", "math": "maths"}
        sub = names.get(result["panel"], result["panel"])
        sections, share, present = [result["panel"]], 1.0, list(range(g))
        actions = [f"Only {sub} questions leaked, from every line: everyone re-sits the {sub} section only. "
                   "The other subjects' scores stand.",
                   f"Start with the {sub} setters and translators: they are the only people who held these "
                   "questions and nothing else.",
                   "Send the matched questions to investigators. "
                   "A name starts an investigation; it is not a finding of guilt."]
    out = {"retest": [f"C{c}" for c in present], "retest_share": share,
           "rescored_share": 0.0 if verdict == "NOT FOUND" or sections else 1 - share,
           "drop_shared": verdict != "NOT FOUND", "sections": sections,
           "actions": actions}
    if candidates:
        out["illustration"] = {"candidates": candidates, "retest": round(candidates * share),
                               "label": "ILLUSTRATIVE: NEET-scale round number, equal line sizes assumed"}
    return out


def nta_percentile(scores):
    """NTA's formula: 100 x (candidates in the group with a raw score <= this one) / group size."""
    ordered, n = sorted(scores), len(scores)
    return [100.0 * bisect_right(ordered, s) / n for s in scores]


def normalise(scores_by_compartment):
    return {c: nta_percentile(s) for c, s in scores_by_compartment.items()}
