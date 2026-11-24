"""The dependency-free engine must equal scikit-learn's TfidfVectorizer(char_wb, 3-5, sublinear_tf).
Skipped when scikit-learn is not installed."""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bulkhead.design import Design  # noqa: E402
from bulkhead.leaks import noisy  # noqa: E402
from bulkhead.textsim import CharTfidf  # noqa: E402

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:  # pragma: no cover
    TfidfVectorizer = None


@unittest.skipIf(TfidfVectorizer is None, "scikit-learn not installed")
class Parity(unittest.TestCase):
    def test_same_scores_and_argmax(self):
        d = Design.load()
        docs = [b["text"] for b in d.bank]
        sk = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        M = sk.fit_transform(docs)
        ours = CharTfidf().fit(docs)
        self.assertEqual(set(sk.vocabulary_), set(ours.idf))
        rng = random.Random(3)
        queries = [noisy(docs[rng.randrange(len(docs))], 0.1, 0.8, rng) for _ in range(150)]
        sims = (sk.transform(queries) @ M.T).toarray()
        for q, row in zip(queries, sims):
            i, s = ours.best(q)
            self.assertEqual(i, int(row.argmax()))
            self.assertAlmostEqual(s, float(row.max()), places=9)


if __name__ == "__main__":
    unittest.main()
