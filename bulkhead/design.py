"""The exam design: compartments, the custody map, and the item bank."""
import hashlib
import json
import os
from dataclasses import dataclass

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def commitment(bank, compartments, presses):
    """SHA-256 over the bank and the custody map. Published before the exam, it lets anyone check later
    that the map used to name a source is the one fixed in advance, not one chosen after the leak."""
    canon = json.dumps({"compartments": compartments, "presses": presses,
                        "bank": [[b["id"], b["block"], b["text"]] for b in bank]},
                       ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


class TamperError(RuntimeError):
    pass


@dataclass
class Design:
    compartments: int          # G: one compartment per print line
    presses: dict              # press name -> compartments it prints, e.g. {"P2": [2, 3]}
    presence_t: int            # unique-item hits needed to call a compartment present
    tau: float                 # similarity threshold, calibrated above every noisy real decoy
    bank: list                 # [{"id", "subject", "block": "S" | int, "text", "source"}]
    false_match_upper: float = 0.005   # per-question false-match bound from calibration (rule of three)
    alpha: float = 1e-4                # chance a compartment is called present by false matches alone
    tau_words: float = None            # threshold of the words-only channel (formulas removed)

    def __post_init__(self):
        self.by_id = {b["id"]: b for b in self.bank}
        self.shared = [b for b in self.bank if b["block"] == "S"]
        self.unique = {c: [b for b in self.bank if b["block"] == c] for c in range(self.compartments)}
        self.slot = {b["id"]: i for blk in [self.shared, *self.unique.values()] for i, b in enumerate(blk)}

    @classmethod
    def load(cls, data_dir=DATA_DIR):
        with open(os.path.join(data_dir, "design.json"), encoding="utf-8") as f:
            meta = json.load(f)
        with open(os.path.join(data_dir, "bank.json"), encoding="utf-8") as f:
            bank = json.load(f)
        got = commitment(bank, meta["compartments"], meta["presses"])
        if meta.get("commitment") and got != meta["commitment"]:
            raise TamperError("Bank or custody map does not match its published commitment.")
        d = cls(meta["compartments"], meta["presses"], meta["presence_t"], meta["tau"], bank,
                meta.get("false_match_upper", 0.005), meta.get("alpha", 1e-4), meta.get("tau_words"))
        d.commitment = got
        return d

    def press_of(self, c):
        return next(p for p, cs in self.presses.items() if c in cs)

    def form(self, c):
        """What a candidate in compartment c answers: the shared block plus c's unique block."""
        return self.shared + self.unique[c]

    def holdings(self, node):
        """Items a custody node holds: 'C3' (a print line), 'P2' (a press), 'SETTER' (everything) or
        'PANEL:chem' (one subject's setters and translators: that subject's questions on every form)."""
        if node == "SETTER":
            return list(self.bank)
        if node.startswith("PANEL:"):
            return [b for b in self.bank if b["subject"] == node[6:]]
        if node in self.presses:
            return self.shared + [b for c in self.presses[node] for b in self.unique[c]]
        return self.form(int(node[1:]))

    def summary(self):
        return {
            "compartments": self.compartments,
            "presses": self.presses,
            "shared": len(self.shared),
            "unique_per_compartment": len(self.unique[0]),
            "subjects": sorted({b["subject"] for b in self.bank}, key=["phy", "chem", "math"].index),
            "form_size": len(self.form(0)),
            "bank": len(self.bank),
            "presence_t": self.presence_t,
            "tau": self.tau,
            "tau_words": self.tau_words,
            "false_match_upper": self.false_match_upper,
            "alpha": self.alpha,
            "commitment": getattr(self, "commitment", None),
        }


def bank_size(slots, compartments, unique_slots):
    """Questions needed: one shared block plus a unique block per compartment."""
    return (slots - unique_slots) + compartments * unique_slots
