"""Make the demo's sample "photo": two pages of a guess paper in a handwriting-style font.

    python3 scripts/make_sample_photo.py /path/to/Kalam-Regular.ttf

Contents (the answer key the web app shows): 14 questions only print line C3 received, 4 shared questions
and 8 real JEE questions that are not in the bank. Maths is removed and the pages get a tilt, blur and
grain, as in eval/ocr_eval.py. SYNTHETIC pages built from REAL questions.
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "eval"))
from bulkhead.design import DATA_DIR, Design  # noqa: E402
import ocr_eval  # noqa: E402


def main(font_path):
    rng = random.Random(5)
    d = Design.load()
    with open(os.path.join(DATA_DIR, "decoys.json"), encoding="utf-8") as f:
        decoys = json.load(f)["test"]
    picked = rng.sample(d.unique[3], 14) + rng.sample(d.shared, 4) + rng.sample(decoys, 8)
    texts = [ocr_eval.words_only(x["text"], keep=0.8) for x in picked]
    rng.shuffle(texts)
    out = os.path.join(ROOT, "public", "samples")
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    paths = ocr_eval.render(texts, font_path, tmp, rng)
    from PIL import Image
    names = []
    for k, p in enumerate(paths, 1):
        name = f"guess-paper-page{k}.jpg"
        Image.open(p).convert("L").save(os.path.join(out, name), quality=72)
        os.remove(p)
        names.append(name)
    os.rmdir(tmp)
    with open(os.path.join(out, "sample-photo.json"), "w") as f:
        json.dump({"pages": names, "truth": {"kind": "photo", "sources": ["C3"], "real_questions": 18,
                   "decoys": 8, "label": "SYNTHETIC handwriting-font pages built from REAL questions"}}, f)
    print(names)


if __name__ == "__main__":
    main(sys.argv[1])
