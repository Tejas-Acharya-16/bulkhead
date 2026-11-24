# Directions explored for "paper leaks in national exams"

Eight directions that differ in kind, each with its closest prior art, compared at desk level on 24 Nov 2026.
"Read" means the source was opened; links are in the README's prior-art table and DISCLOSURE.md.

| # | Direction | Closest prior art (read) | What it can do | Why it is not enough alone | Decision |
|---|---|---|---|---|---|
| 1 | Mark every copy (QR code, serial, watermark) | CBSE since 2018; Telangana 2025 | Names the centre and candidate behind a photo or photocopy | Gone when a paper is retyped or copied by hand; says nothing about who else must re-sit | Complement: keep for photographed leaks |
| 2 | Different wording per recipient (canary trap, or an LLM rewording per centre) | Canary trap / barium meal test | Names the recipient whose wording leaked | A leaker who paraphrases removes the bait; reworded variants change difficulty | Rejected |
| 3 | Different questions per custody node, decoded from the leak's content | CBSE's old region sets; PSI form forensics | Names the line, press or setter from any copy; bounds the re-test | Costs a bigger bank; a setter's full copy still means a full re-test | **Chosen: Bulkhead** |
| 4 | Response forensics after the exam (who answered like the leak) | PSI data forensics; compromised-item detection research | Finds candidates who used the leak, even its wrong answers | Needs the responses, so it runs after the damage; finds users, not the source | Complement: run inside the named line |
| 5 | Computer-based test with a different item draw per candidate | JEE Main multi-shift CBT | Every candidate gets a different paper; a leak is narrow | Needs computer centres for 22 lakh candidates on one day; NEET is pen and paper | Rejected for now (capacity) |
| 6 | Just-in-time encrypted papers, printed at the centre | Encryption and centre-specific codes recommended after the 2018 CBSE leak | Shrinks the window in which a paper can leak | Once printed, a leak is again unattributable and national | Complement |
| 7 | Tamper-evident custody (sealed trunks, GPS, CCTV, access logs) | NTA trunks and CCTV; the 2026 CBI chargesheet cites CCTV gaps | Records who had access | Does not say which access leaked; many people hold the same paper | Complement: Bulkhead's map uses these logs |
| 8 | Watch the leak market (crawl Telegram and WhatsApp for guess papers) | PSI web crawling | Finds a leak sooner | Finding a leak is not knowing where it came from | Complement: feeds Bulkhead's decoder |

Bulkhead (3) is the only direction that both names the source from a retyped copy and limits who re-sits.
Directions 1, 4, 6, 7 and 8 make it stronger rather than compete with it.
