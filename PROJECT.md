# Monarch: Measuring the External Field

B.Sc. Physics dissertation, The Catholic University of Eastern Africa, 2026.
Brian Mwai (1050555). Supervisor: Dr. Songa Mutambi.

Full title: *Measuring the External Field: A Cortical-Proxy Content Observable and the Mean-Field
Bound on Media-Driven Opinion Change.*

- Live tool: https://monarch-4iy.pages.dev
- All 400 articles with their scores: https://monarch-4iy.pages.dev/corpus
- Code and data: https://github.com/brn-mwai/monarch

---

## The question, in one line

When you read a news article, it pushes a little on what you think. **Can we measure how hard
that push is, using only the article itself?**

## The idea

Physics has a model for a group of people making up their minds. It was built for magnets, where
tiny arrows line up with their neighbours. Here, each arrow is a person who is for or against
something.

```
m = tanh(βJ·m + h)
```

| Symbol | Name | Plain meaning |
|---|---|---|
| m | magnetisation | The mood of the room: −1 everyone against, 0 split, +1 everyone for |
| J | coupling | How much people copy those around them |
| β | inverse temperature | How seriously people take that pressure instead of deciding at random |
| βJ | reduced coupling | The two together: how strongly people copy each other |
| h | external field | The outside push on everyone at once. Here, the media |

In the studies this project reviewed, **h is always guessed**. Nobody measures it. This project
measures a candidate for h from the content itself.

## How one article becomes one number

1. **Read aloud.** A computer voice reads the article, because the brain model learned from people
   watching and listening.
2. **Word timings.** A tool marks when each word is spoken.
3. **Brain prediction.** TRIBE v2, a published brain model from Meta (d'Ascoli et al., 2026),
   predicts how a typical adult brain would react at **20,484** spots on the brain's surface.
4. **Two regions.** A standard brain map (Glasser et al., 2016) picks **1,030** spots linked to
   emotion and **851** linked to careful thinking.
5. **The score.**

```
X = (emotion reaction) − (thinking reaction)
```

- Above 0: the emotion areas react more.
- Below 0: the thinking areas react more.
- The numbers have no physical unit. They are the model's standardised activity, so only
  comparisons between articles mean anything.
- **Nobody was scanned.** Every value is a prediction for a typical adult brain. The tool rates
  content, never a person.

## The 400 articles

| Group | Source | Articles |
|---|---|---|
| Fear-activating | ISOT fake news | 100 |
| High outrage | SemEval-2019 Task 4 partisan news | 100 |
| Reward hook (clickbait) | Webis-Clickbait-17 | 100 |
| Neutral | PubMed abstracts + ISOT real news | 100 |

- **162 to 167 words**: the average length of each group, so no group stands out just by being
  longer.
- **0.027**: the smallest effect 400 articles can reliably detect, worked out before scanning
  (η², at 80% power and p < 0.05).
- **× 2**: every article was run twice, to check the results repeat.

### Reading the corpus page

| Column | Meaning |
|---|---|
| Emotional | How strongly the 1,030 emotion spots react |
| Deliberate | How strongly the 851 thinking spots react |
| Score | Emotional minus Deliberate, which is X |
| Pre-scan label | What the original collection called the article, before any scan |
| Words | Article length |

Scores run from **−0.070 to +0.054**, so the spread (ΔX) is **0.124**.

| Group | Average score |
|---|---|
| Fear-activating | −0.002 |
| Reward hook | −0.013 |
| High outrage | −0.018 |
| Neutral | −0.019 |

All four averages are below zero: in every group the thinking areas react more than the emotion
areas. The groups differ in **how far** below zero they sit.

## Results, with what each number means

### 1. The four groups differ

| Number | Meaning |
|---|---|
| η² = 0.107 | 10.7% of the differences between articles come from their group. The other 89.3% comes from the article itself |
| F = 15.779 | The gap between groups is about 16 times what chance alone would give |
| p = 1.0 × 10⁻⁹ | If the four groups were really the same, a result this strong would turn up about once in a billion tries |
| 0.089 | η² on the second run. The result repeats |

Test: one-way ANOVA (one factor, the group, and one number per article, the score).

### 2. Fear drives it, and outrage moves both regions equally

Cohen's d is the distance from the neutral group, counted in typical spreads (standard
deviations). The usual guide marks are 0.2, 0.5 and 0.8.

| Group | d from neutral |
|---|---|
| Fear-activating | 0.94 |
| Reward hook | 0.32 |
| High outrage | 0.03 (p = 0.832) |

Why outrage sits near zero:

| | Emotion areas | Thinking areas | Score |
|---|---|---|---|
| Fear | +0.61 | −0.10 | moves |
| Outrage | +0.51 | +0.49 | stays flat |

Outrage does affect the brain, but on both sides equally, so the difference stays near zero.

### 3. Scores repeat for groups, not for single articles

| Number | Meaning |
|---|---|
| ICC = 0.8725 | Agreement between the two runs. 1 = identical, 0 = no agreement |
| 51 of 400 | Articles whose score changed sign between runs (about 1 in 8) |
| 55 (44 to 67) | How many flips random noise alone would cause. 51 is inside that range |
| 0.003 vs 0.022 | The average distance from zero of flipped articles vs the rest. Flipped ones sit on the edge |

So the project reports group averages and never gives a verdict on a single article.

### 4. Honest check: word counting beats the score

AUC: pick one manipulative and one neutral article at random. Out of 100 such pairs, how often
does the method rank the manipulative one higher? 50 = coin toss, 100 = perfect.

| Method | AUC |
|---|---|
| Sentiment tool (VADER) | 0.54 |
| This project's score | 0.63 |
| Word counting (TF-IDF + logistic regression) | 0.98 |

Word counting wins because each group came from one source, and the words give the source away:
they identify the source **66%** of the time against **25%** by guessing. Source is mixed in with
group, so the differences cannot be put down to writing style alone. **The score is a
measurement for the physics, not a fake-news detector.**

### 5. Does the brain model match real brains?

Tested on public brain scans of 4 people watching the TV show *Friends* (Algonauts 2025 /
CNeuroMod). r measures how closely two signals move together: 0 = no match, 1 = perfect.

| Number | Meaning |
|---|---|
| 0.152 | Real people against each other over the full episode: the best any model could hope for |
| 0.096 | The best possible on the 2-minute clip tested |
| 0.028 | The model on that clip: 30% of the best possible |
| p = 0.048 | Tested against 61 time-shifted copies; just under the usual 0.05 line |

The match is positive: the model moves in the same direction as real brains, and does not
reproduce the negative value an outside audit had reported. Three pipeline bugs were found and
fixed along the way. A full-episode run is the next step (Paper 3).

## The physics result: the minimum push

The media push is written as h = α·X, where **α** (the coupling constant) is how much push you get
per unit of score. The data cannot measure α, so the thesis asks how big α must be for the media
to flip the majority:

```
α ≥ h_c(βJ) / ΔX
```

| Symbol | Meaning | Value |
|---|---|---|
| h_c(βJ) | Critical field: the smallest push that flips the majority | 0.533 at βJ = 2 |
| ΔX | Spread of scores, highest minus lowest | 0.124 |
| α | Minimum media strength | **≥ 4.29 at βJ = 2** |

In plain words: anyone claiming these articles flip opinion in a group that copies at strength 2
must assume a media strength of at least 4.29, or the model says it cannot happen. This is a bar
any claim has to clear, not a claim that media flips opinion. It holds within the mean-field
model. When βJ > 1, the model's quadratic coefficient a = (1 − βJ)/2 is negative, and two stable
opinions exist. That is why a push of a certain size is needed to flip between them.

## Equations used, and how

| Law or equation | How it is used here |
|---|---|
| Ising energy: E = −J Σ sᵢsⱼ − h Σ sᵢ | Each person sᵢ is +1 or −1. Agreeing with neighbours lowers the energy, and h rewards pointing the media's way |
| Mean-field equation: m = tanh(βJ·m + h) | Each person feels the room's average m instead of each neighbour. Solving it gives the room's mood |
| Landau free energy: F(m) = a m² + b m⁴ − h m, a = (1 − βJ)/2, b = 1/12 | When βJ > 1, a < 0 and two stable opinions (two valleys) appear. These coefficients correct the proposal's version |
| Critical field: h = atanh(m) − βJ·m, turning point where dh/dm = 0 | The valley vanishes at m*² = 1 − 1/βJ, giving h_c = \|atanh(m*) − βJ·m*\| = 0.533 at βJ = 2 |
| The bound: α·ΔX ≥ h_c | The strongest push the articles give is α·ΔX. To flip the room it must reach h_c, so α ≥ 0.533 / 0.124 = 4.29 |
| Score: X = A_emotional − A_deliberate | A difference, not a ratio, because A is often near zero or negative |
| η² = SS_between / SS_total | Share of all variation explained by group (0.107) |
| F = between-group variance / within-group variance | One-way ANOVA test statistic (15.779) |
| Cohen's d = (group mean − neutral mean) / pooled SD | The gap from neutral in units of typical spread |
| ICC = between-article variance / (between + run-to-run variance) | Agreement between the two runs (0.8725) |
| Noise σ = sd(run1 − run2) / √2 = 0.0073 | Simulating this noise predicts 55 sign flips (44 to 67) |
| AUC = P(X_manipulative > X_neutral) | Chance a random manipulative article outscores a random neutral one |
| Pearson r = cov(prediction, brain) / (sd · sd) | How closely the model's prediction and real brain activity move together |

## What the work supports, and what it does not

| Supported | Not supported |
|---|---|
| A content score that can be measured, with its repeatability stated (0.8725) | That the score detects manipulation (source is mixed in; word counting scores 0.98) |
| It separates the four groups at η² = 0.107 | Anything about the amygdala (the model predicts the surface only) |
| A minimum media strength, α ≥ 4.29 at βJ = 2 | A measured value of α |
| A positive first check against real brains, 30% of the best possible | A verdict on any single article |

## Changes from the proposal (approved amendment)

1. The amygdala was dropped, because the model predicts the brain's surface only.
2. The ratio score was replaced by a difference, because the ratio was undefined for 69 of 400
   articles.
3. Fear, not outrage, stands out.
4. α could not be measured, so a minimum was derived instead.
5. The score is a measurement, not a detector.

## Limits and the next study for each

| Limit | Next study |
|---|---|
| Predictions, not brain scans | Check against more real brain data |
| Group mixed up with source | A new set where every source has every type |
| Brain surface only | A model that predicts deep brain areas |
| α not measured | Compare scores with real opinion polls |
| Brain check is 2 minutes long | The full episode |

## Where it goes next

- **Papers:** Paper 1 (the minimum push) and Paper 2 (the measuring tool) for *Physica A*, and
  Paper 3 (matching real brains) for *Imaging Neuroscience*. Preprints first, on arXiv.
- **Kenya:** news coverage of the 2024 Finance Bill, once there is funding for GPU time and paid
  labelling.
- **Beyond text:** video and audio content. Children's media only with children's brain data and
  ethics approval.

## Ethics

No data was collected from any person. The brain model was trained by Meta on public scans of
volunteers who consented. This project uses only public articles and public scans, and rates
content, never a viewer. TRIBE v2 is licensed CC-BY-NC-4.0, so it is used for research only and
the project makes no money.

## Repository map

| Path | What it holds |
|---|---|
| `apps/web/` | The live tool and the corpus page (Next.js) |
| `services/inference/` | The brain-model server and analysis scripts |
| `services/inference/scripts/` | One script per reported number, e.g. `baselines.py`, `outrage_split.py`, `reversal_diagnosis.py`, `field_bound.py`, `paper3_noise_ceiling.py` |
| `docs/thesis/` | The dissertation (LaTeX, 81 pages) |
| `docs/paper1/`, `paper2/`, `paper3/` | The three papers |
| `docs/defence/` | The defence deck, script and build script |
| `CITATIONS.md` | Every model, dataset and reference, with licences |

## Key references

- d'Ascoli et al. (2026). A foundation model of vision, audition, and language for in-silico neuroscience (TRIBE v2). arXiv:2605.04326.
- d'Ascoli et al. (2025). TRIBE: TRImodal Brain Encoder (v1). arXiv:2507.22229.
- Glasser et al. (2016). A multi-modal parcellation of human cerebral cortex. *Nature*.
- Ahmed et al. (2017), ISOT; Kiesel et al. (2019), SemEval-2019 Task 4; Potthast et al. (2018),
  Webis-Clickbait-17.

See [CITATIONS.md](CITATIONS.md) for the full list.
