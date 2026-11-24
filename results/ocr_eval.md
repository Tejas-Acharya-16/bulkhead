# OCR test (Tesseract on rendered pages, maths removed)

Question text REAL (JEEBench). Pages SYNTHETIC: rendered in a font, with tilt, blur and grain. OCR REAL (tesseract 5.3.4). Every formula is deleted before rendering.

| Font | Scenario | Trials | Source named | Recall of leaked questions |
|---|---|---|---|---|
| handwriting (Kalam) | Line leak C3 | 10 | 1.00 | 0.59 |
| handwriting (Kalam) | Press leak P2 | 10 | 1.00 | 0.55 |
| handwriting (Kalam) | Small leak, 12 questions | 10 | 1.00 | 0.67 |
| handwriting (Kalam) | Null: decoys only | 10 | 1.00 | n/a |
| printed (DejaVu Serif) | Line leak C3 | 10 | 1.00 | 0.86 |
| printed (DejaVu Serif) | Press leak P2 | 10 | 1.00 | 0.88 |
| printed (DejaVu Serif) | Small leak, 12 questions | 10 | 1.00 | 0.87 |
| printed (DejaVu Serif) | Null: decoys only | 10 | 1.00 | n/a |
