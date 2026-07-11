# Monarch — AMD Developer Hackathon: ACT II submission (Track 3, Unicorn)

Deadline: **Jul 11, 7:00 PM East Africa Time.** Submit on lablab.ai.
Judging: Creativity/Originality · Product/Market Potential · Completeness · Use of AMD Platforms.

---

## lablab.ai fields (copy-paste)

### Project Title
Monarch — a neural processing scanner for media

### Short Description (one line)
Monarch predicts whether media is built to trigger your emotions or your reasoning, shows it on a 3D brain, and models how it could move a crowd's opinion.

### Long Description
Media is increasingly engineered to trigger emotion before reasoning — and there is no objective way to measure it. Two stories can report the same fact: one to inform, one to enrage. That difference is invisible to the reader and drives polarization, misinformation, and over-stimulation, especially for children.

Monarch makes it measurable. Give it a headline, post, or video and it runs the content through an AI model of the human brain (Meta's TRIBE v2) on an AMD Instinct MI300X, predicts the cortical activation, and shows it lighting up a real 3D cortical surface. It computes the Neural Arousal Asymmetry (NAA) — the ratio of predicted activation in emotional versus reasoning brain systems — and then goes one step further with physics: a Landau/Ising mean-field model of how that emotional pull could shift collective opinion. Finally, Google's Gemma (hosted on AMD hardware via Fireworks AI) writes a plain-language audit anyone can read.

Use cases: flagging when content is too stimulating for an audience such as children, giving researchers and journalists an objective measure of how framing provokes rather than informs, and giving platforms a signal for emotional manipulation that word-level sentiment tools miss.

Monarch is honest about its boundaries: it predicts an average brain's response to content — it never scans a real person — and it presents the opinion-dynamics layer as a proposed, calibratable model rather than a proven result. That honesty is what makes the claim defensible.

### Technology / Category Tags
AI Agents, Neuroscience, AMD MI300X, ROCm, Gemma, Fireworks AI, Media Integrity, Three.js, Physics, Next.js

### Public GitHub Repository
https://github.com/brn-mwai/monarch

### Application URL
(Deploy `apps/web` to Vercel — runs in synthetic-demo mode with no keys — and paste the URL.)

---

## How each judging criterion is met

- **Creativity / Originality** — nobody else predicts *brain-response-to-media* and layers a *physics model of opinion* on top. The field is full of routers, captioners, and dashboards; Monarch is a genuinely novel instrument.
- **Product / Market Potential** — a measurable signal for emotional manipulation: parental/child over-stimulation controls, platform content moderation, media-integrity research. Word-level sentiment/toxicity tools cannot see this.
- **Completeness** — full front-to-back experience: scan → 3D brain (pial/fiducial/white surfaces, inflation, activation) → physics → Gemma audit → export. Runs end-to-end today (synthetic without a GPU, real with the inference service).
- **Use of AMD Platforms** — TRIBE v2 inference on MI300X + ROCm; Gemma audit reports via Fireworks AI on AMD hardware. Two independent AMD-compute paths.

---

## Video presentation script (~2.5 min)

1. **Hook (0:00–0:20)** — "Two headlines, same fact. One informs you, one is built to make you angry. You can't see the difference — but your brain can. Monarch measures it."
2. **The scan (0:20–1:00)** — paste a neutral headline, then the outrage version. Show the 3D brain lighting up differently; show NAA jump from ~0.8 to ~3.7. *(Show the MI300X pod / ROCm running the inference here — required proof of AMD use.)*
3. **The physics (1:00–1:30)** — the Landau curve and susceptibility: how the emotional pull could move collective opinion. State clearly it's a proposed model.
4. **The audit (1:30–2:00)** — the Gemma-written report (Summary / Key findings / Caveats). Note "Gemma via Fireworks on AMD."
5. **The pitch (2:00–2:30)** — use cases (kids/over-stimulation, moderation, research) + the honest caveat (average brain, not a real person). "Monarch makes the manipulation that's designed to stay invisible, visible and measurable."

## Slide deck outline (map to the 4 criteria)

1. Title + one-line pitch.
2. The problem (the two-headlines example).
3. How it works (TRIBE → NAA → Landau → Gemma), one diagram.
4. Demo screenshots (3D brain + report).
5. **Use of AMD** (MI300X + ROCm + Gemma/Fireworks) — call this out explicitly.
6. Market / use cases (kids, moderation, research).
7. Honesty slide (validated instrument vs proposed physics; average brain not a person).
8. What's next (calibrate α̂ on real corpora; validation).

---

## Submission checklist

Done (in repo):
- [x] Public GitHub repo + README with setup/usage.
- [x] Containerized: `apps/web/Dockerfile` + `services/inference/Dockerfile` (both `linux/amd64`).
- [x] Runnable via instructions (synthetic mode needs no keys).
- [x] Gemma integration (Fireworks) + AMD/ROCm inference path.
- [x] Honesty framing (defensible claims).

Only Brian can do (before Jul 11, 7 PM EAT):
- [ ] Confirm the lablab **team** is registered (required even solo — gates the MI300X pod).
- [ ] Sign up for the **AMD AI Developer Program** (credits + pod).
- [ ] Deploy `apps/web` to **Vercel**; paste the Application URL.
- [ ] Record the **video** (use the script above) — must show MI300X/ROCm in use.
- [ ] Make the **slide deck** (outline above) + a **cover image**.
- [ ] Run the smoke test on the pod (`services/inference/scripts/smoke_test.py`) so the demo uses real TRIBE, and set `FIREWORKS_API_KEY` so the report shows real Gemma.
- [ ] Submit all fields on **lablab.ai** before the deadline.
