"""Character n-gram TF-IDF with no dependencies.

Matches scikit-learn's TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
feature for feature (tests/test_parity.py checks this when scikit-learn is installed), so the engine
runs anywhere, including a serverless function, with no compiled packages.
"""
import math
import re
from collections import Counter, defaultdict

_WS = re.compile(r"\s\s+")
_MATH = re.compile(r"\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)", re.S)
_CMD = re.compile(r"\\[a-zA-Z]+|[{}_^\\&$]")


def strip_math(text):
    """The words of a question with every formula removed: what survives a photo, OCR or a hurried
    hand copy, where formulas come out garbled or are skipped."""
    t = _CMD.sub(" ", _MATH.sub(" ", text))
    return re.sub(r"\s+", " ", t).strip()


def char_wb_ngrams(text, lo=3, hi=5):
    """Character n-grams inside word boundaries, padded with one space each side (sklearn char_wb)."""
    text = _WS.sub(" ", text.lower())
    out = []
    for w in text.split():
        w = " " + w + " "
        size = len(w)
        for n in range(lo, hi + 1):
            off = 0
            out.append(w[off:off + n])
            while off + n < size:
                off += 1
                out.append(w[off:off + n])
            if off == 0:            # word shorter than n: counted once
                break
    return out


class CharTfidf:
    """Fit on the bank; score any text against every bank item by cosine similarity."""

    def __init__(self, lo=3, hi=5):
        self.lo, self.hi = lo, hi
        self.idf, self.rows, self.index = {}, [], defaultdict(list)

    def fit(self, docs):
        counts = [Counter(char_wb_ngrams(d, self.lo, self.hi)) for d in docs]
        df = Counter()
        for c in counts:
            df.update(c.keys())
        n = len(docs)
        self.idf = {g: math.log((1 + n) / (1 + k)) + 1 for g, k in df.items()}
        self.rows = [self._weigh(c) for c in counts]
        self.index = defaultdict(list)
        for i, row in enumerate(self.rows):
            for g, w in row.items():
                self.index[g].append((i, w))
        return self

    def _weigh(self, counts):
        v = {g: (1 + math.log(c)) * self.idf[g] for g, c in counts.items() if g in self.idf}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {g: x / norm for g, x in v.items()}

    def vector(self, text):
        return self._weigh(Counter(char_wb_ngrams(text, self.lo, self.hi)))

    def scores(self, text):
        """Cosine similarity of `text` to every bank item that shares at least one n-gram."""
        acc = defaultdict(float)
        for g, w in self.vector(text).items():
            for i, wi in self.index.get(g, ()):
                acc[i] += w * wi
        return acc

    def best(self, text):
        acc = self.scores(text)
        if not acc:
            return -1, 0.0
        i = max(acc, key=lambda k: (acc[k], -k))     # ties go to the lower index, like numpy argmax
        return i, acc[i]

    def best_many(self, texts):
        return [self.best(t) for t in texts]


def pairwise_max(model, texts):
    """Best bank index and score for each text."""
    return [model.best(t) for t in texts]
