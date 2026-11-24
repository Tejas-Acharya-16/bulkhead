# Real-copy test (planned)

Purpose: replace SIMULATED copying noise with real handwritten copies. About 2 hours for the team.

1. Fix the expected results before starting, in `results/real_copies.md`: for each copy, write which node
   it came from. Commit that file first, so the result cannot be fitted afterwards.
2. Export three sources:
   `python3 scripts/export_form.py C2 > c2.txt`, `python3 scripts/export_form.py C5 > c5.txt`,
   `python3 scripts/export_form.py P3 > p3.txt`.
3. Each teammate takes one source and copies 15 to 25 questions by hand the way a leaker would: in a hurry,
   with shortcuts, skipping figures and options. Mix in 20 or more questions from a real coaching "guess
   paper" or past papers that are not in the bank.
4. Photograph each page. Turn the photos into text with any OCR app (write down which one) and paste the
   text into the deployed app. Save each pasted text in `results/real_copies/`.
5. Record for each copy: questions read, matches, the verdict, and whether it matches the expected node.
6. Report everything, including misses. A miss that comes back "not found" is the safe failure; a wrong
   line named is a real failure and goes to the top of the README.

Label in every document: REAL copies, OCR by a named third-party app, team members as copyists (not
independent leakers).
