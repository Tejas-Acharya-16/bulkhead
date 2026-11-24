# BULKHEAD evaluation (200 trials per scenario, engine: scikit-learn)

Question text REAL (JEEBench, MIT). Leak copies SIMULATED. Noise and design ASSUMED.

tau 0.5756 | recall on noisy bank items 0.999 | false matches per held-out decoy: clean 0.0000, noisy 0.0000, rewritten 0.0000 (decoder assumes at most 0.00467)

| Scenario | Source named | False compartments | Re-tested | Leaked yet scored (worst) | Recall | Questions |
|---|---|---|---|---|---|---|
| Line leak: 75% of one form, 2:1 decoys | 1.000 | 0.000 | 0.125 | 0 | 0.998 | 153 |
| Press leak: both lines of one press | 1.000 | 0.000 | 0.250 | 0 | 1.000 | 176 |
| Small leak: 12 questions | 0.985 | 0.000 | 0.125 | 2 | 0.998 | 120 |
| Heavy noise: 20% char errors, 60% copied | 1.000 | 0.000 | 0.125 | 0 | 0.448 | 153 |
| Rewritten: 50% of words dropped, shuffled | 1.000 | 0.000 | 0.125 | 0 | 0.922 | 153 |
| Rewritten: 70% of words dropped, shuffled | 1.000 | 0.000 | 0.125 | 0 | 0.512 | 153 |
| Two leakers, different presses | 1.000 | 0.000 | 0.250 | 0 | 0.999 | 168 |
| Setter leak: master copy | 1.000 | 0.000 | 1.000 | 0 | 1.000 | 310 |
| Setter side: one subject panel (chemistry) | 1.000 | 0.000 | 1.000 | 0 | 0.999 | 176 |
| Shared block only | 1.000 | 0.000 | 0.000 | 0 | 0.999 | 132 |
| Null: real decoys only | 1.000 | 0.000 | 0.000 | 0 | n/a | 108 |
| Null, rewritten decoys (70% dropped) | 1.000 | 0.000 | 0.000 | 0 | n/a | 108 |
| Flood: line leak inside 1,080 decoys | 1.000 | 0.000 | 0.125 | 0 | 0.999 | 1125 |
| Flood null: 1,080 decoys, no leak | 1.000 | 0.000 | 0.000 | 0 | n/a | 1080 |
