"""OCR test: does the verdict survive a real OCR engine reading page images?

    python3 eval/ocr_eval.py --trials 3          # needs the tesseract binary and Pillow

Each trial builds a guess paper (real bank questions + real JEE decoys, as in run_eval.py), REMOVES all
maths (a copied formula rarely survives OCR, so only the words are kept), renders it as page images in a
handwriting-style font (Kalam, Indian Type Foundry, OFL) and in a printed serif, adds a small tilt, blur
and grain like a phone photo, runs Tesseract 5, and decodes the OCR text.

Labels: question text REAL; pages SYNTHETIC (rendered, not written by a person); OCR REAL (Tesseract).
This is a step between simulated noise and real handwritten copies, not a replacement for them.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bulkhead.decoder import Decoder, split_questions  # noqa: E402
from bulkhead.design import DATA_DIR, Design  # noqa: E402

FONTS = {"handwriting (Kalam)": os.environ.get("KALAM", "/home/claude/vendor/Kalam-Regular.ttf"),
         "printed (DejaVu Serif)": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"}
SCENARIOS = [("Line leak C3", ["C3"], .75, ("NAMED", ["C3"])),
             ("Press leak P2", ["P2"], .75, ("NAMED", ["P2"])),
             ("Small leak, 12 questions", ["C5"], .20, ("NAMED", ["C5"])),
             ("Null: decoys only", [], 0, ("NOT FOUND", []))]
_MATH = re.compile(r"\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)", re.S)


def words_only(t, keep=0.8):
    t = _MATH.sub(" ", t)
    t = re.sub(r"\\[a-zA-Z]+|[{}_^\\]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:max(80, int(len(t) * keep))]


def render(questions, font_path, out_dir, rng):
    font = ImageFont.truetype(font_path, 34)
    W, H, M, LH = 1700, 2200, 110, 50
    pages, img, y = [], None, H

    def new_page():
        nonlocal img, y
        if img is not None:
            pages.append(img)
        img, y = Image.new("L", (W, H), 250), M
        return ImageDraw.Draw(img)

    draw = new_page()
    for i, q in enumerate(questions, 1):
        lines, cur = [], f"Q{i}."
        for w in q.split():
            if font.getlength(cur + " " + w) > W - 2 * M:
                lines.append(cur)
                cur = w
            else:
                cur += " " + w
        lines.append(cur)
        if y + LH * (len(lines) + 1) > H - M:
            draw = new_page()
        for ln in lines:
            draw.text((M, y), ln, font=font, fill=25)
            y += LH
        y += LH                                     # blank line between questions
    pages.append(img)
    paths = []
    for k, p in enumerate(pages):
        p = p.rotate(rng.uniform(-1.5, 1.5), fillcolor=250, resample=Image.BICUBIC)
        p = p.filter(ImageFilter.GaussianBlur(rng.uniform(0.6, 1.1)))
        noise = Image.effect_noise(p.size, 18)
        p = Image.blend(p, noise, 0.12)
        path = os.path.join(out_dir, f"p{k}.png")
        p.save(path)
        paths.append(path)
    return paths


def _ocr_one(p):
    return subprocess.run(["tesseract", p, "-", "--psm", "4"], capture_output=True, text=True, check=True).stdout


def ocr(paths):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        return "\n\n".join(ex.map(_ocr_one, paths))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=3)
    a = ap.parse_args()
    design = Design.load()
    with open(os.path.join(DATA_DIR, "decoys.json"), encoding="utf-8") as f:
        decoys = json.load(f)["test"]
    dec = Decoder(design)
    rng = random.Random(23)
    rows, t0 = [], time.time()
    for font_name, font_path in FONTS.items():
        for name, sources, frac, (want_v, want_n) in SCENARIOS:
            ok = 0
            recalls, chars_ok = [], []
            for _ in range(a.trials):
                leaked = []
                for node in sources:
                    items = design.holdings(node)
                    leaked += rng.sample(items, max(1, round(frac * len(items))))
                texts = [words_only(x["text"]) for x in leaked] + [words_only(d["text"]) for d in decoys]
                rng.shuffle(texts)
                with tempfile.TemporaryDirectory() as tmp:
                    text = ocr(render(texts, font_path, tmp, rng))
                r = dec.decode(split_questions(text))
                ok += r["verdict"] == want_v and sorted(r["nodes"]) == sorted(want_n)
                if leaked:
                    ids = {x["id"] for x in leaked}
                    recalls.append(len(ids & {m["bank_id"] for m in r["matches"]}) / len(ids))
            rows.append({"font": font_name, "scenario": name, "trials": a.trials, "source_named": ok / a.trials,
                         "recall": round(sum(recalls) / len(recalls), 3) if recalls else None})
            print(rows[-1], flush=True)
    out = {"rows": rows, "seconds": round(time.time() - t0), "tesseract": subprocess.run(
        ["tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()[0],
        "labels": {"question_text": "REAL (JEEBench)", "pages": "SYNTHETIC renders, maths removed",
                   "ocr": "REAL (Tesseract)"}}
    with open(os.path.join(ROOT, "results", "ocr_eval.json"), "w") as f:
        json.dump(out, f, indent=1)
    lines = ["# OCR test (Tesseract on rendered pages, maths removed)", "",
             "Question text REAL (JEEBench). Pages SYNTHETIC: rendered in a font, with tilt, blur and grain. "
             "OCR REAL (" + out["tesseract"] + "). Every formula is deleted before rendering.", "",
             "| Font | Scenario | Trials | Source named | Recall of leaked questions |", "|---|---|---|---|---|"]
    for r in rows:
        rec = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
        lines.append(f"| {r['font']} | {r['scenario']} | {r['trials']} | {r['source_named']:.2f} | {rec} |")
    with open(os.path.join(ROOT, "results", "ocr_eval.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
