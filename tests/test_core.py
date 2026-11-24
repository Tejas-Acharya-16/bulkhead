"""Core behaviour. Run: python3 -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead import service  # noqa: E402
from bulkhead.decoder import name_node, poisson_tail, presence_needed, split_questions  # noqa: E402
from bulkhead.design import Design, bank_size  # noqa: E402
from bulkhead.response import nta_percentile  # noqa: E402
from bulkhead.textsim import CharTfidf, char_wb_ngrams  # noqa: E402

D = Design.load()


class TextSim(unittest.TestCase):
    def test_ngrams_pad_words(self):
        self.assertEqual(char_wb_ngrams("ab", 3, 3), [" ab", "ab "])
        self.assertEqual(char_wb_ngrams("a", 3, 5), [" a "])          # short word counted once

    def test_self_match_is_best(self):
        m = CharTfidf().fit([b["text"] for b in D.bank])
        for i in (0, 57, 269):
            j, s = m.best(D.bank[i]["text"])
            self.assertEqual(j, i)
            self.assertAlmostEqual(s, 1.0, places=9)

    def test_unknown_text_scores_zero(self):
        m = CharTfidf().fit(["alpha beta gamma"])
        self.assertEqual(m.best("zzzz qqqq"), (-1, 0.0))


class WordsChannel(unittest.TestCase):
    def test_formula_free_copy_still_matches(self):
        from bulkhead.decoder import Decoder
        from bulkhead.textsim import strip_math
        dec = Decoder(D)
        items = [b for b in D.bank if "$" in b["text"] and len(strip_math(b["text"])) > 300][:5]
        self.assertTrue(items)
        hits = dec.match([strip_math(b["text"]) for b in items])
        for b, (i, s, via) in zip(items, hits):
            self.assertEqual(D.bank[i]["id"] if i >= 0 else None, b["id"])
            self.assertIn(via, ("full", "words"))

    def test_strip_math(self):
        from bulkhead.textsim import strip_math
        self.assertEqual(strip_math(r"Let $x^2=\frac{1}{2}$ be real and \[y=1\] hold"), "Let be real and hold")


class Splitting(unittest.TestCase):
    def test_numbered(self):
        t = "Q1. " + "a" * 50 + "\n\nmore of q1\n\nQ2) " + "b" * 50 + "\n3. " + "c" * 50
        self.assertEqual(len(split_questions(t)), 3)

    def test_blank_lines_glue_short_fragments(self):
        t = ("x" * 130) + "\n\n(A) 1 (B) 2\n\n" + ("y" * 130)
        qs = split_questions(t)
        self.assertEqual(len(qs), 2)
        self.assertIn("(A) 1", qs[0])


class Naming(unittest.TestCase):
    def test_nodes(self):
        self.assertEqual(name_node([3], 5, D), ("NAMED", ["C3"]))
        self.assertEqual(name_node([2, 3], 5, D), ("NAMED", ["P2"]))
        self.assertEqual(name_node([1, 6], 0, D), ("MULTIPLE", ["C1", "C6"]))
        self.assertEqual(name_node(list(range(8)), 0, D), ("NAMED", ["SETTER"]))
        self.assertEqual(name_node([], 4, D), ("SHARED ONLY", []))
        self.assertEqual(name_node([], 0, D), ("NOT FOUND", []))

    def test_presence_threshold_rises_with_length(self):
        self.assertEqual(presence_needed(100, D), 3)
        ks = [presence_needed(n, D) for n in (100, 500, 1500, 5000)]
        self.assertEqual(ks, sorted(ks))
        self.assertGreater(ks[-1], 3)

    def test_poisson_tail(self):
        self.assertAlmostEqual(poisson_tail(0, 2.0), 1.0)
        self.assertAlmostEqual(poisson_tail(1, 2.0), 1 - 2.718281828 ** -2, places=6)


class EndToEnd(unittest.TestCase):
    """Simulated leaks built from real questions; several seeds per kind."""
    EXPECT = {"line": ("NAMED", ["C3"]), "press": ("NAMED", ["P2"]), "small": ("NAMED", ["C5"]),
              "two": ("MULTIPLE", ["C1", "C6"]), "setter": ("NAMED", ["SETTER"]),
              "shared": ("SHARED ONLY", []), "null": ("NOT FOUND", []), "rewrite70": ("NAMED", ["C2"]),
              "panel": ("NAMED", ["SETTER"])}

    def test_samples(self):
        for kind, (v, nodes) in self.EXPECT.items():
            for seed in (1, 2, 3):
                r = service.decode_text(service.sample(kind, seed)["text"])
                self.assertEqual((r["verdict"], sorted(r["nodes"])), (v, sorted(nodes)), f"{kind} seed {seed}")
                self.assertEqual(r["panel"], "chem" if kind == "panel" else None, f"{kind} seed {seed}")

    def test_response_limits_retest(self):
        r = service.decode_text(service.sample("line", 5)["text"])
        self.assertEqual(r["response"]["retest"], ["C3"])
        self.assertAlmostEqual(r["response"]["retest_share"], 1 / 8)
        r = service.decode_text(service.sample("null", 5)["text"])
        self.assertEqual(r["response"]["retest_share"], 0.0)

    def test_guards(self):
        self.assertIn("error", service.decode_text(""))
        self.assertIn("error", service.decode_text("x" * (service.MAX_CHARS + 1)))
        self.assertIn("error", service.sample("nope", 1))


class Commitment(unittest.TestCase):
    def test_tamper_is_detected(self):
        import copy
        from bulkhead.design import commitment
        bank = copy.deepcopy(D.bank)
        self.assertEqual(commitment(bank, D.compartments, D.presses), D.commitment)
        bank[5]["block"] = 3                     # move one question to another line after the fact
        self.assertNotEqual(commitment(bank, D.compartments, D.presses), D.commitment)


class Arithmetic(unittest.TestCase):
    def test_neet_scale_bank(self):
        self.assertEqual(bank_size(180, 8, 90), 810)
        self.assertEqual(bank_size(60, 8, 30), len(D.bank))

    def test_nta_percentile(self):
        self.assertEqual(nta_percentile([10, 20, 20, 40]), [25.0, 75.0, 75.0, 100.0])


if __name__ == "__main__":
    unittest.main()
