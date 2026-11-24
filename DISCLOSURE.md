# Disclosure

## Original work

All code, data processing and design in this repository were written in November 2026 for NovaStark Hacks
2026 by Team NovaNex. No code was carried over from an earlier project.

## Third-party sources

| What | Source | Licence | How it is used |
|---|---|---|---|
| Question text (data/bank.json, data/decoys.json) | JEEBench, Daman Arora et al., <https://github.com/dair-iitd/jeebench> | MIT | 515 JEE Advanced questions (2016–2023); 485 kept after removing near-duplicates. Used as the item bank and as decoys. |
| TF-IDF definition | scikit-learn `TfidfVectorizer` | BSD-3-Clause | Our engine (`bulkhead/textsim.py`) is a fresh implementation of the same formula; `tests/test_parity.py` compares the two. scikit-learn is optional and only used by the eval and the parity test. |
| Typefaces | Spectral (Production Type), Atkinson Hyperlegible (Braille Institute), from google/fonts, self-hosted in `public/fonts/` | SIL Open Font License (texts included) | Web app typography. |
| OCR engine | Tesseract.js 7 and tesseract.js-core, self-hosted in `public/vendor/tesseract/` | Apache-2.0 (texts included) | Reads photos in the browser. |
| OCR model | `eng.traineddata` from tesseract-ocr/tessdata_fast | Apache-2.0 (text included) | English model for the OCR engine. |
| Handwriting-style font | Kalam (Indian Type Foundry), from google/fonts | SIL Open Font License | Used only by `eval/ocr_eval.py` and `scripts/make_sample_photo.py` to render test pages; not shipped. |
| Tesseract 5 (command line) | tesseract-ocr | Apache-2.0 | OCR in `eval/ocr_eval.py`. |
| Percentile formula | National Testing Agency's published normalisation method for multi-shift exams | Public method | `bulkhead/response.py`: percentile within a group. |

## AI assistance

The team used an AI assistant (Claude, by Anthropic) to help research the problem, write code, run the
evaluation and draft documents. The team chose the problem and the idea, reviewed the code and checked every
number in the README against `results/eval.json`.

## What is real, simulated, assumed or planned

- **Real:** question text; the matcher's measured recall and false-match rates on held-out real questions.
- **Simulated:** every leak copy in the eval and the demo (real questions plus code-generated copying errors),
  including the sample photo.
- **Assumed:** the demo exam design (60 questions per form, 8 lines, 4 presses), the noise rates, and the
  illustrative 22 lakh candidates in the web app.
- **Real OCR on synthetic pages:** `eval/ocr_eval.py` renders real questions as page images in fonts and reads
  them with Tesseract; the pages were not written by a person.
- **Planned:** a test on real handwritten copies (`docs/REAL_COPY_PROTOCOL.md`) and a handwriting OCR model.
