# Round 1 submission: hack4hack form, field by field

Closes 10 Dec 2026, 11:59 pm IST. Every link must open for anyone with the link (test each one in a
private browser window, signed out).

**Problem statement**

    Open Innovation · Bulkhead: exam leaks that name their source

**Presentation (PPT / Google Slides / Drive link)**
Export the 7-slide deck (it follows the organisers' template) as PDF. Upload it to Google Drive, then
Share → General access → "Anyone with the link" → Viewer. Paste that link.

**GitHub repository**
https://github.com/Tejas-Acharya-16/bulkhead

**Live demo**
https://bulkhead-pi.vercel.app

**Demo video (YouTube / Drive)**
Already made: `public/demo.mp4` (2 min 37 s, captioned, no voice), served at https://bulkhead-pi.vercel.app/demo.mp4.
Paste that link, or upload the same file to YouTube as Unlisted if the form rejects it.

**Any other link**
The results table: https://github.com/Tejas-Acharya-16/bulkhead/blob/main/results/eval.md

**Notes for the judges** (paste as is; about 150 words)

    No login needed. Open the live demo, click any simulated leak (e.g. "One print line"), then "Find the source". The verdict names the print line, press or setter; the answer key appears only after you run it.

    The idea: the questions are the tracer. A QR code can be cropped and a canary's wording paraphrased; the questions cannot be dropped, because they are what the leak sells.

    What is real: every question is a real JEE Advanced question (JEEBench, MIT licence), and the decoys are real JEE questions not in our bank. What is simulated: the leak copies (copying errors and rewording added by code). What is assumed: the demo exam (60 questions per form, 8 print lines, 4 presses). Photo input is built (in-browser OCR) but tested only on rendered fonts, not real handwriting.

    Results on simulated leaks built from 485 real JEE questions, 14 scenarios x 200 trials: source named in all 200 trials in 13 of them, and 98.5% for a 12-question leak (its misses named no line); zero wrong lines flagged in 2,800 trials. On page images read by real OCR (Tesseract) with every formula removed: 80 of 80 verdicts correct (10 papers per case; pages rendered in fonts, not real handwriting). "Chemistry setters only" reproduces the NEET-UG 2026 pattern; "Try a sample photo" reads a photographed guess paper in the browser. Reproduce: python3 eval/run_eval.py. Run locally: python3 server.py (standard library only). Tests: python3 -m unittest discover -s tests.

    Honest limits, all in the README: a photographed copy from one centre is better traced by a QR code (use both); scoring the unaffected candidates on their own block costs some ranking precision (simulated: 0.976 vs 0.988 agreement with ability at NEET size); real handwriting is not yet tested. A named line starts an investigation; it is not a finding of guilt.
