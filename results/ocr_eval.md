# OCR test (Tesseract on rendered pages, maths removed)

Question text REAL (JEEBench). Pages SYNTHETIC: rendered in a font, with tilt, blur and grain. OCR REAL (tesseract 5.3.4). Every formula is deleted before rendering.

| Font | Scenario | Trials | Source named | Recall of leaked questions |
|---|---|---|---|---|
| handwriting (Kalam) | Line leak C3 | 3 | 1.00 | 0.55 |
| handwriting (Kalam) | Press leak P2 | 3 | 1.00 | 0.55 |
| handwriting (Kalam) | Small leak, 12 questions | 3 | 1.00 | 0.53 |
| handwriting (Kalam) | Null: decoys only | 3 | 1.00 | n/a |
| printed (DejaVu Serif) | Line leak C3 | 3 | 1.00 | 0.84 |
| printed (DejaVu Serif) | Press leak P2 | 3 | 1.00 | 0.88 |
| printed (DejaVu Serif) | Small leak, 12 questions | 3 | 1.00 | 0.94 |
| printed (DejaVu Serif) | Null: decoys only | 3 | 1.00 | n/a |
