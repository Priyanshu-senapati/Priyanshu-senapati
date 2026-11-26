<div align="center">

<img src="assets/hero.svg" width="100%" alt="A notebook page. Priyanshu Kumar Senapati, B.Tech CSE (AI and ML) at RV University, class of 2028, Bengaluru. 'I build AI that is always right' is crossed out in red and corrected to 'knows when it's wrong'. A sticky note: RescueLens, 94.55% top-1; shown 60 cars it had never seen, it said not sure 58 times instead of guessing. Tally marks: 10 hackathons, 2 made the finale. A sketched car marks where its high voltage runs.">

<a href="https://www.linkedin.com/in/priyanshu-senapati/"><img src="assets/btn-linkedin.svg" height="48" alt="Connect on LinkedIn"></a>&nbsp;<a href="https://priyanshu-senapati--rescuelens-web.us-east.modal.run"><img src="assets/btn-rescuelens.svg" height="48" alt="Try RescueLens live"></a>&nbsp;<a href="https://dor-sandy-two.vercel.app"><img src="assets/btn-dor.svg" height="48" alt="Try Dor live"></a>

</div>

Hi, I'm Priyanshu. I study computer science (AI and ML) at RV University in Bengaluru, with a minor in finance. I like building the whole thing, from training the model to shipping an app people can open. Mostly, I care about what a system does when it *doesn't* know the answer.

## Ask the model

<img src="assets/terminal.svg" width="100%" alt="A terminal. Q: does your AI guess when it isn't sure? A: no. RescueLens refused to guess on 58 of 60 cars it had never seen. Q: is it any good? A: 94.55% top-1 across 196 car classes. Q: and the LLM agent? A: Query2Diagnose: 0% unsafe answers on 300 cases; LLM baselines 43–70%. Q: does any of it have tests? A: 790 across four projects: ULTRON 337, Neralu 287, RescueLens 94, Voyance 72. Q: hackathons? A: 10 so far; 2 finales: Hack4SDG 2026, and Top 30 in Vietnam. Q: what's his best project? A: not certain. refusing to guess. scroll down and judge for yourself.">

## What I'm building right now

<a href="https://github.com/Priyanshu-senapati/Ultron"><img src="assets/ultron.svg" width="100%" alt="Notebook sketch of ULTRON, a personal AI that runs on my laptop: 19 processes, 337 tests. Four Rust processes (input hooks, insight pulse, memory engine, ghost for encrypted LAN sync) and fifteen Python ones (voice, LLM router, tools and agents, privacy router and ten more) share one WebSocket bus that needs a token. If one crashes, the rest keep going. Every event goes into a hash-chained log that rejects edits and deletes. The privacy router sends a cloud model only text with names, paths and secrets stripped; money, health and files never leave the laptop."></a>

Latest: I cut about a second off every LLM request and brought `ultron status` down from 18 s to 2 s. Next, a deep-work mode that holds back interruptions, and a 10-second catch-up brief for when I come back to my desk.

## Things I've built

<p>
<a href="https://github.com/Priyanshu-senapati/Rescuelens"><img src="assets/card-rescuelens.svg" width="49%" alt="Index card. RescueLens: identifies cars at crash sites and shows rescuers where the high voltage runs. 94.55% top-1 across 196 classes. CV Hackathon 2026."></a>
<a href="https://github.com/skypank-coder/Query2Diagnose"><img src="assets/card-query2diagnose.svg" width="49%" alt="Index card. Query2Diagnose: LLM agent research, co-author. Diagnoses appliance faults from code-mixed Kannada/Hindi–English messages. 0% unsafe answers."></a>
</p>
<p>
<a href="https://github.com/Priyanshu-senapati/Neralu"><img src="assets/card-neralu.svg" width="49%" alt="Index card. Neralu (ನೆರಳು): heatwave check-ins for older people. Hack4SDG 2026 finale, 287 tests."></a>
<a href="https://github.com/Priyanshu-senapati/kaavalu"><img src="assets/card-kaavalu.svg" width="49%" alt="Index card. Kaavalu (ಕಾವಲು): an Android app that spots a 'digital arrest' scam while the call is still going, warns the person in their own language and texts their family. No call recording, no blocklists. App Lab, Kalpavikas 2.0."></a>
</p>
<p>
<a href="https://github.com/Priyanshu-senapati/Dor"><img src="assets/card-dor.svg" width="49%" alt="Index card. Dor (डोर): care coordination for families. Lighthouse accessibility score 100."></a>
<a href="https://github.com/Priyanshu-senapati/voyage"><img src="assets/card-voyance.svg" width="49%" alt="Index card. Voyance: hotel inventory planning, 14–24% more expected profit than last year's bookings in simulation. TBO VoyageHack 4.0."></a>
</p>

## More builds

| Project | What it does | Built for |
|---|---|---|
| **[Chaabi](https://github.com/Priyanshu-senapati/UGREEN)** | Privacy-first AI skill that maps a family's assets and nominees from a home NAS | UGREEN AI NAS Hackathon 2026 |
| **[Karigar AI](https://github.com/gd23456/SIH2026)** | Cut photo processing from 30 s to 1 s, with a 9-language UI | Smart India Hackathon 2026 |
| **SETHU (AgroSense)** | Satellite data and XGBoost warn rice farmers of crop stress 10–14 days ahead, by SMS | Asian Hackathon for Green Future, Top 30 |
| **ClaimCourt AI** | Insurance claims argued by defense, prosecution and auditor agents, decided by a rule engine | AI Build Sprint |

## Things I learned building these

- An unreadable photo isn't a safe one. Kaavalu used to score a blurry notice as zero, which looked like an all-clear for something it had never read. Now it says "unreadable".
- Software should hand the big calls to a person. Neralu never phones an ambulance itself: it sends a neighbour or a volunteer to the door, and a human decides.
- Keep the risky parts small. In ULTRON, any process can crash without taking the others down, and nothing writes, deletes or runs a shell command until I approve it.

## Where I've worked

**Quantitative Developer Intern, Opendaddy Fintech** (June to July 2026)<br>
Built on-demand stock ranking for US and Indian markets on an explainable analysis platform, fixed NSE/BSE ticker resolution and a calibration bug that made "Buy" unreachable, and shipped 50 commits through reviewed pull requests.

## What's in my toolbox

<img src="assets/toolbox.svg" width="100%" alt="Sticky notes. Languages: Python, TypeScript, Rust, Kotlin, Java, SQL. ML and AI: PyTorch, scikit-learn, XGBoost, LightGBM, YOLO, OpenCV, ONNX, LLM agents, RAG, Whisper. Backend and web: FastAPI, Flask, Next.js, React, Tailwind, PostgreSQL, SQLite, Firebase, Twilio. Ops and cloud: Docker, GitHub Actions, pytest, Modal, Vercel, Hugging Face. Finance: DCF valuation, backtesting, CVaR, linear programming.">

<div align="center">

I'm looking for AI/ML and software engineering internships for 2027. [Message me on LinkedIn](https://www.linkedin.com/in/priyanshu-senapati/).

</div>
