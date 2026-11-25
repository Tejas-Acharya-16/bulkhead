# Demo video: narrated, about 2 min 50 s

Record the live site, https://bulkhead-pi.vercel.app, and the deck. 1080p, browser zoom 110%.
Before recording, click "Try a sample photo" once so the OCR engine is cached (the first load takes a few
seconds). Upload to YouTube as **Unlisted**. A captioned, silent backup is at `public/demo.mp4`.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Slide 1 | Hi, we're Team NovaNex from RGIPT. This is Bulkhead. It makes a leaked exam paper tell you where it leaked from, so only the students it could have reached have to re-sit. |
| 0:15 | Slide 2 | In May 2026, NEET-UG was cancelled for 22.79 lakh students after a guess paper matched the real questions. Every centre got the same paper, so the leak could not say where it came from, and everyone paid. QR codes don't help, because a leak is retyped or copied by hand. |
| 0:40 | Slide 3 | Our idea: split the exam along its chain of custody. Every form has a shared block, plus questions that only one print line receives. A leak can only contain what its source held. The questions are the tracer, and a leaker can't remove them, because the questions are what they are selling. |
| 1:00 | App: click **One print line**, then **Find the source** | This is our live prototype. This sample hides 45 real JEE questions from line C3 among 108 other real JEE questions, with copying errors. One click. Bulkhead says print line C3, at press 2, and the answer key agrees. |
| 1:20 | Scroll to **What happens now** and **Evidence** | Only line C3 re-sits: 12.5 percent of students instead of everyone. Everyone else is scored on their own questions, which the leak never had. Every match is listed with its original source. |
| 1:35 | Click **Rewritten**, find. Then **No leak**, find. | If the leaker rewrites it and drops 70 percent of the words, it still finds the line. And a paper with no bank questions names nobody: it refuses rather than guesses. |
| 1:55 | Click **Chemistry setters only**, find | This is the 2026 pattern: only chemistry, from every line. Bulkhead points at the chemistry setters, and only that section is re-sat. |
| 2:10 | Click **Try a sample photo** | It also reads a photo of a guess paper, right in the browser. The photo never leaves the device. Line C3 again. |
| 2:25 | Slide 6, or the README results on GitHub | We tested it on 485 real JEE questions: 14 scenarios, 200 trials each, and it never named a wrong line in 2,800 trials. With real OCR on page images, 80 of 80 verdicts were correct. It's open source, and every number can be rerun. |
| 2:45 | Slide 7 | Next: real handwritten copies and a psychometrician's review. Bulkhead: the leaked paper tells you where it left the chain. Thank you. |
