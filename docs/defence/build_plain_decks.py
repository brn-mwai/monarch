"""Build the defence deck twice from one source.

Monarch_Defence_Deck.pptx         16 slides, no speaker notes.
Monarch_Defence_Deck_Script.pptx  the same 16 slides; each slide's speaker
                                  notes hold the script, every number on the
                                  slide with its meaning, and likely questions.
"""

import math as pymath
import os

from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from deck_theme import (BLUE, EMBER, GOLD, GREEN, HERE, LINE, M, MIDBLUE,
                        MUTED, TEXT, W, arrow, bar, card,
                        footer, header, icon, lattice, math, new_deck,
                        para, plain, rich, scale_bars, slide, textbox)

SECTIONS = ["The idea", "The method", "The results", "The physics",
            "What's next"]
DELTA_X = 0.1241
INSTRUMENT_URL = "https://monarch-4iy.pages.dev"
CORPUS_URL = INSTRUMENT_URL + "/corpus"
SCREENSHOT = os.path.join(HERE, "assets", "instrument_article.png")

GROUP_MEANS = [("Fear-activating", -0.0018, EMBER),
               ("Reward hook", -0.0128, MIDBLUE),
               ("High outrage", -0.0185, GOLD),
               ("Neutral", -0.0191, MUTED)]

SLIDES = [
    ("Title", None, 0.5,
     "Good morning. I'm Brian Mwai, and my dissertation is called Measuring "
     "the External Field. The question behind it is simple: can we measure "
     "how hard a news article pushes on what people think? I'll start with "
     "the physics idea behind that question.",
     [], []),
    ("The idea", "The idea", 1,
     "Physics can model opinion the way it models a magnet. Each person is a "
     "spin, pointing for or against. m, the magnetisation, is the group's "
     "average opinion, from minus one to plus one. J, the coupling, is how "
     "much people copy those around them. Beta, the inverse temperature, is "
     "how firmly they follow that pull instead of acting at random. And h, "
     "the external field, is media's push on everyone at once. In the studies "
     "I read, h is always chosen by hand. Nobody measures it. So my question "
     "was: can h be measured from the content itself? Testing the tools to "
     "answer that changed the plan, so that comes next.",
     ["m: average opinion, -1 (all against) to +1 (all for)",
      "h: a general external field, media's push; not magnetic or electric"],
     [16]),
    ("Plan vs reality", "The idea", 1,
     "Five things changed once I tested the tools. I planned to measure the "
     "amygdala, but the model only predicts the brain's surface. I planned a "
     "ratio score, but it was undefined for 69 of the 400 articles, so I used "
     "a difference, which works for all 400. I expected outrage to stand out, "
     "and fear did instead. I planned to measure alpha, media's strength, but "
     "the data can't pin it down, so I derived its minimum. And word counting "
     "sorted the articles better than my score, 0.98 against 0.63, so the "
     "score is a measurement, not a detector. All five are in the approved "
     "amendment. Here is how the measurement works.",
     ["69 of 400: articles where the ratio was undefined (say 69, not 49)",
      "0.98 vs 0.63: word counting vs our score, AUC, 0.5 = coin toss"],
     [7, 17]),
    ("Tools and process", "The method", 1.5,
     "One article becomes one number in five steps. A text-to-speech voice "
     "reads it aloud, because the brain model was trained on people watching "
     "and listening. A timing tool marks when each word is spoken. TRIBE v2, "
     "a published model from Meta, predicts activity at 20,484 points on the "
     "brain's surface. A standard brain map picks 1,030 points in emotional "
     "areas and 851 in deliberate, reasoning areas. The score, X, is the "
     "emotional average minus the deliberate average. Above zero, emotion "
     "leads. Below zero, reasoning leads. The numbers have no physical unit: "
     "they are the model's standardised activity. Nobody was scanned; every "
     "value is a prediction. The article on the left scores plus 0.054, the "
     "highest of all 400. So which 400 articles?",
     ["20,484: points on the brain surface the model predicts",
      "1,030: points in emotional areas; 851: points in deliberate areas",
      "+0.109 emotional, +0.055 deliberate, score +0.054 (0.109 - 0.055)",
      "Units: standardised activity, no physical unit"],
     [3, 6, 12]),
    ("The articles", "The method", 1,
     "I used four public collections, 100 articles each: fear-activating fake "
     "news, high-outrage partisan news, reward-hook clickbait, and neutral "
     "writing from medical abstracts and real news. The group averages sit "
     "between 162 and 167 words, so length can't explain a difference. "
     "Before scanning, I calculated that 400 articles can detect an eta "
     "squared of 0.027 or more, and I scanned every article twice. All 400 "
     "are on the corpus page, so here is how to read it.",
     ["4 x 100 = 400 articles",
      "162 to 167: range of the four group averages, in words",
      "0.027: smallest eta squared 400 articles detect (80% power, p < 0.05)",
      "x 2: every article scanned twice"],
     [11, 13]),
    ("Reading the corpus", "The method", 1.5,
     "This is what each column on the corpus page means. Emotional is the "
     "average predicted activity across the 1,030 emotional points. "
     "Deliberate is the same across the 851 reasoning points. Score is "
     "emotional minus deliberate: that's X. Pre-scan label is the label the "
     "article already had in its source collection. Across all 400, scores "
     "run from minus 0.070 to plus 0.054, a spread of 0.124. On the right are "
     "the four group averages. All four are below zero, so the reasoning "
     "areas respond more in every group. The groups differ in how far below "
     "zero they sit: fear is closest, at minus 0.002, and neutral is "
     "furthest, at minus 0.019. I'll show you the page now. [SHOW CORPUS] "
     "The question is whether those differences are real.",
     ["-0.070 to +0.054: lowest and highest score of the 400",
      "0.124: spread = highest minus lowest; used in the physics later",
      "-0.002 fear, -0.013 reward hook, -0.018 outrage, -0.019 neutral",
      "Below zero = deliberate areas respond more than emotional areas"],
     [18]),
    ("Result 1", "The results", 1,
     "To test that, I used a one-way ANOVA. It compares the spread between "
     "the four group averages with the spread inside each group. F is "
     "15.779. Eta squared is the share of all the variation in the score "
     "that the group accounts for: 0.107, so 10.7 percent. The other 89 "
     "percent is article to article. The p-value is 1 times 10 to the minus "
     "9: the probability of an F this large if all four groups had the same "
     "average. The second run gave 0.089. Both are above the 0.027 the study "
     "could detect. So the groups differ. Which group drives it?",
     ["F = 15.779: between-group spread over within-group spread",
      "eta squared 0.107 = 10.7% of the variation is due to group",
      "p = 1.0 x 10^-9 first run; second run 0.089, p = 4.9 x 10^-8",
      "0.027: smallest eta squared the design could detect"],
     [14, 15]),
    ("Result 2", "The results", 1,
     "Fear does. Cohen's d measures how far a group's average sits from "
     "neutral, in standard deviations. Fear is 0.94, clickbait 0.32, outrage "
     "0.03. For scale, 0.2, 0.5 and 0.8 are the usual reference marks. So why "
     "is outrage near zero? Split the score into its two parts. Fear raises "
     "the emotional areas by 0.61 and the deliberate areas by minus 0.10, so "
     "the score moves. Outrage raises both, by 0.51 and 0.49, so the "
     "difference stays near zero. Outrage has an effect, on both sides "
     "equally. Next: can we trust these scores?",
     ["d: distance from neutral in standard deviations",
      "Fear 0.94, reward hook 0.32, outrage 0.03 (p = 0.832)",
      "Fear: emotional +0.61, deliberate -0.10",
      "Outrage: emotional +0.51, deliberate +0.49"],
     []),
    ("Result 3", "The results", 1,
     "I ran all 400 articles twice on the GPU. The ICC, the agreement "
     "between the two runs, is 0.8725, where 1 means identical and 0 means "
     "no agreement. 51 of the 400 changed sign between runs. Measurement "
     "noise alone predicts 55, with a 95 percent range of 44 to 67, so 51 is "
     "what noise predicts. Those articles sit near zero: their average size "
     "is 0.003, against 0.022 for the rest. So I report group averages and "
     "never a verdict on one article. Now the most important check.",
     ["ICC 0.8725: agreement of two runs, 1 = identical, 0 = none",
      "51 of 400 = 12.8% changed sign between runs",
      "55.3 expected from noise, 95% range 44 to 67",
      "Flipped items: average size 0.003 vs 0.022 for the rest"],
     []),
    ("Honest check", "The results", 1,
     "Does the score detect manipulation? AUC is the probability that a "
     "randomly chosen manipulative article scores above a randomly chosen "
     "neutral one. 0.5 is a coin toss, and 1 is perfect. A sentiment tool "
     "gets 0.54. My score gets 0.63. Plain word counting gets 0.98. Why so "
     "high? Each group came from one source, and the words identify the "
     "source for 66 percent of articles, against 25 percent by chance. So "
     "the difference can't be put down to writing style alone, because "
     "source is mixed in. My score is a measurement for the physics, not a "
     "manipulation detector. That raises the next question: does the brain "
     "model match real brains?",
     ["AUC: chance a manipulative article outscores a neutral one",
      "0.54 sentiment (VADER), 0.63 our score, 0.98 word counting (TF-IDF)",
      "66%: articles whose source the words identify; chance 25%"],
     [5]),
    ("Real brains", "The results", 1,
     "I tested it on public brain scans of four people watching Friends. The "
     "correlation, r, measures how closely two signals rise and fall "
     "together. Real people match each other at 0.152 over the full episode; "
     "that's the ceiling. On the 2-minute clip I ran, the ceiling is 0.096 "
     "and the model reaches 0.028, which is 30 percent of the ceiling. The "
     "p-value is 0.048, under the 0.05 cut-off. The sign is positive, so it "
     "does not reproduce the negative value a published audit reported. I "
     "also found and fixed three bugs in the pipeline. The full-episode run "
     "is the next step, in Paper 3. Now to the physics.",
     ["r: correlation, 0 = no match, 1 = perfect",
      "0.152: people vs each other, full episode (ceiling)",
      "0.096: ceiling on the 2-minute clip; 0.028: the model",
      "30% = 0.028 / 0.096; p = 0.048 against 61 time-shifted copies"],
     []),
    ("The minimum push", "The physics", 1.5,
     "Here is how the score connects to the model. The field h equals alpha "
     "times X. Alpha is the coupling constant: how much push per unit of "
     "score. I can't measure alpha, so I asked how big it must be to flip a "
     "majority. The critical field, h c, is the smallest push that does "
     "that, and it depends on beta J, the reduced coupling: how strongly "
     "people copy each other. At beta J of 2, h c is 0.533. Divide by the "
     "spread of scores, 0.124, and alpha must be at least 4.29. The curve "
     "shows that minimum for every beta J. It is a bar any claim must clear, "
     "not a claim that media flips opinion, and it holds within the "
     "mean-field model. So what could this be used for?",
     ["h = alpha x X: field = coupling constant x score",
      "beta J = 2: say 'beta J', not 'beta'",
      "h_c(2) = 0.533: smallest push that flips the majority at beta J = 2",
      "0.533 / 0.124 = 4.29: minimum alpha"],
     [9, 10, 16]),
    ("Children's content", "What's next", 1,
     "At my proposal I was asked whether this could analyse any content, "
     "even what children watch. It takes video and audio, so it could score "
     "a cartoon. But the model learned from adult brains, so it can't say how "
     "a child reacts. I only tested news text, and 1 in 8 single scores flip "
     "between runs. Children would need child brain data and ethics approval "
     "first. Each of these limits points to a next study.",
     ["1 in 8: 51 of 400 single scores flip between runs"],
     [1, 2, 8, 19]),
    ("Limits", "What's next", 0.5,
     "Five limits, each with the study that fixes it. Predictions need "
     "checking against more real brain data. Group and source need "
     "separating with a new article set. Deep brain areas need a model that "
     "predicts them. Alpha needs real opinion data. And the brain check needs "
     "the full episode. That leads to where the work goes next.",
     ["5 limits, each stated in the thesis"], []),
    ("Taking it further", "What's next", 0.75,
     "Three directions. Publishing: three papers, with preprints first. "
     "Extending the science: the Kenyan case from the proposal, coverage of "
     "the 2024 Finance Bill, plus video and audio, and measuring alpha "
     "against opinion data. And opportunities: a postgraduate topic, "
     "collaboration with neuroscience and media researchers, and a tool that "
     "is already online. To close, four conclusions.",
     ["Kenya: 2024 Finance Bill coverage, needs GPU funding"],
     [4, 13]),
    ("Conclusions", "What's next", 1,
     "One: a field observable can be measured from content, and it repeats, "
     "with agreement of 0.8725 between runs. Two: it separates the four "
     "groups at eta squared 0.107, with source mixed in, so I report it as a "
     "measurement, not a detector. Three: alpha can't be measured from this "
     "data, so the thesis gives a minimum, 4.29 at beta J of 2. Four: the "
     "brain model correlates positively with real brains, at 0.028, 30 "
     "percent of the ceiling. Three papers follow from this. Thank you. I'm "
     "happy to take your questions.",
     ["0.8725 ICC", "0.107 eta squared", "4.29 minimum alpha at beta J = 2",
      "0.028 = 30% of the 0.096 ceiling"],
     [3, 5, 19]),
]

QUESTIONS = [
    ("Can this analyse any content, even what children watch?",
     "It can score video and audio. But the model learned from adult brains, "
     "so it can't say how a child reacts, and I only tested news text. It "
     "would need child brain data and ethics approval first."),
    ("Could a parent or a regulator use it to rate one show?",
     "Not yet. 51 of 400 single scores flip between runs, so one score isn't "
     "reliable. It is for comparing groups of content."),
    ("Was anyone scanned? Is it reading minds?",
     "No. Nobody was scanned. The scores are predictions for a typical adult "
     "brain. The tool rates content, not people."),
    ("Could someone use it to make content more manipulative?",
     "It's a real risk for any content measure. That's why it reports group "
     "results only, for research, and the model's licence is non-commercial."),
    ("If word counting does better, why not use that?",
     "Word counting mostly learns the source: 66% against 25% chance. My "
     "score is meant to be the push h in the opinion model. The comparison is "
     "there to be honest about what the score is."),
    ("Why read the articles aloud?",
     "The model was trained on people watching and listening, so it expects "
     "speech with word timings."),
    ("Why no amygdala?",
     "The released model only predicts the brain's surface. The amygdala is "
     "deep inside, so I make no claim about it."),
    ("What would it take for children's media?",
     "Child brain scans with ethics approval and consent, a children's video "
     "test set, and content where source and type are mixed."),
    ("Why is this physics?",
     "The opinion model is statistical physics, the maths of magnets lining "
     "up. The contribution is measuring the push and deriving its minimum."),
    ("What does alpha >= 4.29 mean in practice?",
     "It's a bar. Alpha turns the score into a push. Any claim that such "
     "content flips a group with beta J = 2 must use an alpha of at least "
     "4.29, or the model says it can't happen."),
    ("Why only 400 articles?",
     "I calculated before scanning that 400 detects an eta squared of 0.027. "
     "Each article takes about 70 seconds of GPU time, and I ran them twice."),
    ("Is it okay to use Meta's model?",
     "Yes, for research. It's under a non-commercial licence, cited "
     "throughout, and this project makes no money from it."),
    ("Why didn't you use Kenyan media?",
     "Cost. 400 articles scanned twice used about 16 GPU hours of the free "
     "Kaggle allowance. A Kenyan set would also need hand-labelling by paid "
     "annotators, because no labelled set exists. The 2024 Finance Bill case "
     "is the first extension once there is funding."),
    ("What is eta squared, physically?",
     "It is not a physical quantity. It is a dimensionless share, between 0 "
     "and 1: the between-group sum of squares divided by the total sum of "
     "squares. 0.107 means the group accounts for 10.7% of the variation in "
     "the score."),
    ("Why a one-way ANOVA?",
     "One factor, the group, with four levels, and one measured value per "
     "article. That is the one-way design. I also checked each group against "
     "neutral with Welch's t-test, which doesn't assume equal spreads."),
    ("What does beta J mean, and why must a be negative?",
     "Beta J is the reduced coupling: how strongly people copy each other "
     "compared with acting at random. In the free energy, a = (1 - beta J)/2. "
     "When beta J is above 1, a is negative and two stable opinions exist, "
     "so a push is needed to flip from one to the other. Alpha itself is "
     "positive."),
    ("Why a difference, not a ratio?",
     "The model outputs standardised activity, so a region's average is "
     "negative about as often as positive. Dividing by it breaks: the ratio "
     "was undefined for 69 of 400 articles. The difference works for all 400."),
    ("Is the difference between groups just writing style?",
     "It can't be put down to style alone, because each group came from one "
     "source. The words identify the source for 66% of articles. A crossed "
     "set, every source with every type, would separate them."),
    ("What about ethics?",
     "No new data was collected from any person. The brain model was trained "
     "by Meta on public, consented scans, and I use only public articles and "
     "public scans. The tool rates content, never a viewer."),
]

KEY_POINTS = [
    "Media's push on opinion is always guessed. This work measures a "
    "candidate for it and derives the minimum strength any claim must use.",
    "In the opinion model, the external field h is an input nobody measures. "
    "That gap is the project.",
    "Testing the tools changed the plan. All five changes are in the approved "
    "amendment.",
    "One article becomes one number, X = emotional minus deliberate. Every "
    "value is a prediction; nobody was scanned.",
    "The article set was fixed before scanning: 4 x 100, length-matched, "
    "powered to detect 0.027.",
    "Each corpus column is defined. All four group averages are below zero.",
    "The groups differ: eta squared 0.107 (10.7%), p = 1.0 x 10^-9, repeated "
    "at 0.089.",
    "Fear drives it at d = 0.94. Outrage lifts both regions equally, so its "
    "score stays at d = 0.03.",
    "Agreement between runs is 0.8725. 51 flips match the 55 noise predicts, "
    "so only group averages are reported.",
    "Word counting scores 0.98 against our 0.63 because source is mixed in. "
    "The score is a measurement, not a detector.",
    "The brain model correlates positively with real brains: r = 0.028, 30% "
    "of the 0.096 ceiling, p = 0.048.",
    "The measured spread sets a minimum: alpha >= 4.29 at beta J = 2.",
    "It can score any video, audio or text, but it is not valid for children "
    "without child brain data.",
    "Every limit points to a specific next study.",
    "Three directions: publishing, extending the science, and further "
    "research.",
    "Four conclusions, each with its number, then questions.",
]

SO_WHAT = (
    "Opinion models treat media as a push, but everyone guesses how big it "
    "is. I built a way to measure a candidate for that push from the content "
    "itself. It separates the four groups at 10.7%, with source mixed in, so "
    "I don't claim it detects manipulation. And even without knowing the "
    "exact strength, the measured spread gives a floor: media would need a "
    "coupling of at least 4.29 to flip a group with beta J = 2. That turns a "
    "guessed number into a testable one.")
SO_WHAT_SLIDES = {0, 11, 15}

DEFINITIONS = {
    0: [("Sociophysics", "using the tools of statistical physics to model how "
                         "groups of people behave")],
    1: [("Ising model", "a model of magnets where each spin points up or "
                        "down and prefers to match its neighbours; used here "
                        "for two-sided opinions"),
        ("Mean field", "each person feels the average of the whole group, "
                       "not particular neighbours; it makes the maths "
                       "solvable"),
        ("tanh", "a smooth S-shaped function that keeps m between -1 and "
                 "+1")],
    2: [("Amygdala", "a small structure deep in the brain linked to fear"),
        ("Cortex", "the brain's outer surface, where the model predicts"),
        ("Amendment", "the approved change to the proposal's scope and "
                      "title")],
    3: [("TRIBE v2", "Meta's published brain model: it predicts fMRI "
                     "responses from text, audio and video"),
        ("fMRI", "brain scanning that tracks blood flow as a stand-in for "
                 "activity"),
        ("fsaverage5", "a standard brain surface with 20,484 points"),
        ("Glasser 2016 atlas", "a standard map dividing the cortex into "
                               "named areas"),
        ("Standardised activity", "the model's output, scaled so it has no "
                                  "physical unit")],
    4: [("Power analysis", "working out in advance how big a study must be "
                           "to detect an effect of a given size")],
    5: [("Pre-scan label", "the label an article carried in its source "
                           "collection before anything was scanned")],
    6: [("One-way ANOVA", "compares the averages of several groups defined "
                          "by one factor"),
        ("F", "spread between group averages divided by spread within "
              "groups"),
        ("eta squared", "between-group sum of squares over total sum of "
                        "squares; a share from 0 to 1"),
        ("p-value", "the probability of a result at least this large if "
                    "there were no real difference")],
    7: [("Cohen's d", "difference between two group averages divided by the "
                      "typical spread (standard deviation)")],
    8: [("ICC", "intraclass correlation: agreement between repeated "
                "measurements of the same items; 1 is identical"),
        ("Sign reversal", "a score positive on one run and negative on the "
                          "other")],
    9: [("AUC", "area under the ROC curve: chance a random manipulative "
                "article outscores a random neutral one"),
        ("TF-IDF", "word counting that weights words by how distinctive "
                   "they are"),
        ("VADER", "a standard sentiment tool"),
        ("Confound", "a second factor, here source, that moves with the one "
                     "studied")],
    10: [("Noise ceiling", "how well real brains predict each other; the "
                           "best any model can do"),
         ("r", "Pearson correlation: how closely two signals rise and fall "
               "together"),
         ("Circular-shift test", "shift one signal in time 61 times to see "
                                 "how often chance gives a match this good")],
    11: [("Critical field", "the smallest field that flips the majority"),
         ("Lower bound", "a minimum: alpha can't be smaller than this")],
    12: [("Ethics approval", "formal permission from a review board, "
                             "required for research with children")],
    13: [("Crossed design", "every source contributes every type of "
                            "article")],
    14: [("Preprint", "a paper shared publicly before peer review, e.g. on "
                      "arXiv")],
}


def notes_for(index):
    title, _, minutes, script, cues, questions = SLIDES[index]
    lines = ["KEY POINT: " + KEY_POINTS[index], "",
             "SCRIPT (about %g min)" % minutes, script]
    if cues:
        lines += ["", "NUMBERS ON THIS SLIDE"]
        lines += ["- " + cue for cue in cues]
    if index in DEFINITIONS:
        lines += ["", "DEFINITIONS (if asked)"]
        lines += ["- %s: %s." % pair for pair in DEFINITIONS[index]]
    if index in SO_WHAT_SLIDES:
        lines += ["", "IF ASKED \"SO WHAT?\"", SO_WHAT]
    if questions:
        lines += ["", "IF ASKED"]
        for q in questions:
            question, answer = QUESTIONS[q - 1]
            lines += ["Q: " + question, "A: " + answer, ""]
    return "\n".join(lines).rstrip()


def banner(s, y, lead, text, colour=GOLD, h=0.62, size=16):
    shp = card(s, M, y, W - 2 * M, h, line=colour)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [(lead + "  ", True, colour), (text, False, TEXT)], size=size,
         first=True, space_after=0)


def chip(s, x, y, w, h, text, colour=TEXT, line=LINE, size=15, bold=False,
         align=PP_ALIGN.LEFT, icon_name=None):
    shp = card(s, x, y, w, h, line=line)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    if icon_name:
        icon(s, icon_name, x + 0.18, y + (h - 0.3) / 2, h=0.3)
        tf.margin_left = Inches(0.6)
    para(tf, text, size=size, bold=bold, colour=colour, first=True,
         align=align, space_after=0)
    return shp


def stat(s, x, y, w, h, value, label, colour=BLUE, size=36, line=None,
         label_size=13):
    shp = card(s, x, y, w, h, line=line or colour)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, value, size=size, bold=True, colour=colour, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    para(tf, label, size=label_size, colour=TEXT, align=PP_ALIGN.CENTER,
         space_after=0)


def style_chart_text(chart, size=12):
    chart.font.size = Pt(size)
    chart.font.color.rgb = MUTED
    chart.font.name = "Calibri"


def donut(s, x, y, d, share, colour):
    data = CategoryChartData()
    data.categories = ["group", "rest"]
    data.add_series("share", (share, 1 - share))
    frame = s.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Inches(x), Inches(y),
                               Inches(d), Inches(d), data)
    chart = frame.chart
    chart.has_legend = False
    chart.has_title = False
    plot = chart.plots[0]
    for pt, fill in zip(plot.series[0].points, (colour, LINE)):
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = fill
        pt.format.line.fill.background()
    hole = plot._element.find(qn("c:holeSize"))
    if hole is None:
        hole = OxmlElement("c:holeSize")
        plot._element.append(hole)
    hole.set("val", "70")


def critical_field(k):
    if k <= 1:
        return 0.0
    m = pymath.sqrt(1 - 1 / k)
    return abs(pymath.atanh(m) - k * m)


def alpha_curve(s, x, y, w, h):
    data = XyChartData()
    curve = data.add_series("alpha required")
    k = 1.0
    while k <= 2.5001:
        curve.add_data_point(round(k, 3), critical_field(k) / DELTA_X)
        k += 0.05
    point = data.add_series("our case")
    point.add_data_point(2.0, critical_field(2.0) / DELTA_X)
    frame = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS,
                               Inches(x), Inches(y), Inches(w), Inches(h), data)
    chart = frame.chart
    chart.has_legend = False
    style_chart_text(chart)
    line_series, dot_series = chart.plots[0].series
    line_series.format.line.color.rgb = BLUE
    line_series.format.line.width = Pt(3)
    line_series.smooth = True
    dot_series.format.line.fill.background()
    dot_series.marker.style = XL_MARKER_STYLE.CIRCLE
    dot_series.marker.size = 12
    dot_series.marker.format.fill.solid()
    dot_series.marker.format.fill.fore_color.rgb = EMBER
    dot_series.marker.format.line.fill.background()
    for axis, lo, hi, unit in ((chart.category_axis, 1.0, 2.5, 0.5),
                               (chart.value_axis, 0, 8, 2)):
        axis.minimum_scale, axis.maximum_scale = lo, hi
        axis.major_unit = unit
        axis.format.line.color.rgb = LINE
        axis.has_major_gridlines = axis is chart.value_axis
    chart.value_axis.major_gridlines.format.line.color.rgb = LINE


def next_line(s, text):
    tf = textbox(s, W - M - 6.0, 6.62, 6.0, 0.3, align=PP_ALIGN.RIGHT)
    para(tf, "Next: " + text + "  →", size=12, bold=True, colour=GOLD,
         first=True, align=PP_ALIGN.RIGHT, space_after=0)


def build_deck(with_notes):
    prs = new_deck()

    def page(i):
        return slide(prs, notes=notes_for(i) if with_notes else None)

    def done(s, i):
        footer(s, SECTIONS, SLIDES[i][1], i + 1)

    # 1 title
    s = page(0)
    lattice(s, 8.75, 1.15, 7, 9, 0.52, seed=7, bias=0.64)
    tf = textbox(s, 8.75, 5.95, 3.64, 0.5, align=PP_ALIGN.CENTER)
    para(tf, "each arrow is one person's opinion", size=13, colour=MUTED,
         first=True, align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, M + 0.15, 1.15, 7.6, 0.4)
    para(tf, "B.Sc. PHYSICS   ·   CUEA   ·   DISSERTATION DEFENCE", size=13,
         bold=True, colour=BLUE, first=True, space_after=0)
    tf = textbox(s, M + 0.15, 1.65, 7.6, 1.9)
    para(tf, "Measuring the", size=50, bold=True, colour=TEXT, first=True,
         space_after=0)
    para(tf, "External Field", size=50, bold=True, colour=BLUE, space_after=0)
    tf = textbox(s, M + 0.15, 3.55, 7.4, 1.0)
    para(tf, "Can we measure how hard a news article pushes on what people "
             "think?", size=21, colour=MUTED, first=True, space_after=0)
    bar(s, M + 0.15, 4.75, 1.4, 0.05, EMBER)
    tf = textbox(s, M + 0.15, 5.0, 7.4, 1.4)
    rich(tf, [("Brian Mwai", True, TEXT), ("   1050555", False, MUTED)],
         size=20, first=True, space_after=4)
    para(tf, "Supervisor: Dr. Songa Mutambi", size=15, colour=MUTED,
         space_after=2)
    para(tf, "25 September 2026", size=15, colour=MUTED, space_after=0)

    # 2 the idea
    s = page(1)
    header(s, "The idea", "Physics treats media as a push, h, on opinion. "
                          "Nobody measures h", "waveform")
    math(s, r"m = \tanh(\beta J\, m + h)", M, 1.65, size=36)
    for i, (sym, text, colour) in enumerate([
            ("m", "magnetisation\n= average opinion, −1 to +1", BLUE),
            ("J", "coupling\n= pull toward neighbours", BLUE),
            (r"\beta", "inverse temperature\n= how firmly people follow",
             BLUE),
            ("h", "external field\n= media's push on everyone", GOLD)]):
        x = M + (i % 2) * 3.85
        y = 2.75 + (i // 2) * 1.12
        card(s, x, y, 3.7, 0.98, line=GOLD if sym == "h" else LINE)
        math(s, sym, x + 0.1, y + 0.2, size=30, colour=colour, centre_w=0.8)
        tf = textbox(s, x + 0.95, y + 0.12, 2.7, 0.8, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, text, size=14, colour=TEXT, first=True, space_after=0)
    lattice(s, 8.9, 1.75, 6, 6, 0.55, seed=3, bias=0.66)
    plain(s.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(12.4), Inches(2.3),
                             Inches(0.4), Inches(2.2)), GOLD)
    math(s, "h", 12.4, 4.6, size=28, colour=GOLD, centre_w=0.4)
    banner(s, 5.2, "Question:", "can h be measured from the content itself?",
           colour=EMBER, h=0.75)
    next_line(s, "what testing the tools changed")
    done(s, 1)

    # 3 plan vs reality
    s = page(2)
    header(s, "The idea", "Testing the tools changed five assumptions",
           "magnifying-glass")
    for x, label, colour in [(M, "WE PLANNED", MUTED), (5.55, "WE FOUND", BLUE)]:
        tf = textbox(s, x, 1.45, 4, 0.3)
        para(tf, label, size=11, bold=True, colour=colour, first=True,
             space_after=0)
    for i, (planned, found) in enumerate([
            ("Measure the amygdala", "Model predicts the brain surface only, "
                                     "so we used surface areas"),
            ("Score as a ratio", "Ratio undefined for 69 of 400, so we used "
                                 "a difference"),
            ("Outrage stands out most", "Fear stands out; outrage lifts both "
                                        "areas equally"),
            ("Measure α, media's strength", "Data can't pin α, so we derived "
                                            "its minimum"),
            ("A manipulation detector", "Word counting 0.98 vs our 0.63, so "
                                        "it's a measurement")]):
        y = 1.8 + i * 0.86
        chip(s, M, y, 4.1, 0.72, planned, colour=MUTED, icon_name="x-circle")
        arrow(s, 4.95, y + 0.29, 0.5, 0.16, EMBER)
        chip(s, 5.55, y, 7.03, 0.72, found, line=BLUE, icon_name="check-circle")
    tf = textbox(s, M, 6.15, 6.0, 0.35)
    para(tf, "All five are in the approved amendment.", size=13, colour=MUTED,
         first=True, space_after=0)
    next_line(s, "how the measurement works")
    done(s, 2)

    # 4 tools and process
    s = page(3)
    header(s, "The method", "How one article becomes one number", "brain")
    steps = [("newspaper", "Article", "400 news texts"),
             ("waveform", "Read aloud", "text-to-speech"),
             ("text-aa", "Word timings", "timing tool"),
             ("brain", "TRIBE v2", "20,484 surface points"),
             ("target", "Brain map", "1,030 + 851 points")]
    sw, gap = 2.12, 0.31
    for i, (icon_name, head, tool) in enumerate(steps):
        x = M + i * (sw + gap)
        card(s, x, 1.45, sw, 1.3, line=BLUE if i == 3 else LINE)
        icon(s, icon_name, x + sw / 2 - 0.2, 1.55, h=0.4)
        tf = textbox(s, x, 1.98, sw, 0.75, align=PP_ALIGN.CENTER)
        para(tf, head, size=15, bold=True, colour=TEXT, first=True,
             space_after=0)
        para(tf, tool, size=12, colour=MUTED, space_after=0)
        if i < len(steps) - 1:
            arrow(s, x + sw + 0.05, 2.02, gap - 0.1, 0.16)
    card(s, M, 2.95, 5.3, 3.15, line=BLUE)
    s.shapes.add_picture(SCREENSHOT, Inches(M + 0.1), Inches(3.03),
                         width=Inches(5.1))
    tf = textbox(s, M, 6.13, 5.4, 0.5)
    rich(tf, [("One article: ", True, TEXT),
              ("emotional +0.109 − deliberate +0.055 = score +0.054, "
               "highest of 400", False, MUTED)], size=11, first=True,
         space_after=0)
    card(s, 6.3, 2.95, 6.28, 1.95, line=BLUE)
    tf = textbox(s, 6.5, 3.03, 5, 0.3)
    para(tf, "THE SCORE, X", size=11, bold=True, colour=MUTED, first=True,
         space_after=0)
    math(s, r"X = \bar{A}_{\mathrm{emotional}} - \bar{A}_{\mathrm{deliberate}}",
         6.3, 3.3, size=22, centre_w=6.28)
    bar(s, 6.6, 4.12, 2.8, 0.1, BLUE)
    bar(s, 9.43, 4.12, 2.8, 0.1, EMBER)
    bar(s, 9.4, 3.99, 0.03, 0.36, TEXT)
    for x, text, colour, al in [(6.6, "X < 0: reasoning leads", BLUE,
                                 PP_ALIGN.LEFT),
                                (9.43, "X > 0: emotion leads", EMBER,
                                 PP_ALIGN.RIGHT)]:
        tf = textbox(s, x, 4.24, 2.8, 0.3, align=al)
        para(tf, text, size=12, bold=True, colour=colour, first=True,
             space_after=0)
    tf = textbox(s, 6.5, 4.52, 5.9, 0.3, align=PP_ALIGN.CENTER)
    para(tf, "Ā = average predicted activity; standardised, no unit  ·  "
             "nobody scanned", size=11, colour=MUTED, first=True,
         space_after=0)
    link_card = card(s, 6.3, 5.05, 6.28, 1.05, line=GOLD)
    link_card.click_action.hyperlink.address = INSTRUMENT_URL
    icon(s, "target", 6.5, 5.33, h=0.46)
    tf = textbox(s, 7.15, 5.1, 5.3, 1.0, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, "TRY THE INSTRUMENT LIVE", size=11, bold=True, colour=GOLD,
         first=True, space_after=0)
    para(tf, INSTRUMENT_URL.replace("https://", ""), size=22, bold=True,
         colour=TEXT, space_after=0)
    para(tf, "code and data: github.com/brn-mwai/monarch", size=11,
         colour=MUTED, space_after=0)
    next_line(s, "the 400 articles")
    done(s, 3)

    # 5 the articles
    s = page(4)
    header(s, "The method", "400 articles, four groups, matched in length",
           "newspaper")
    for i, (name, src, colour) in enumerate([
            ("Fear-activating", "fake news (ISOT)", EMBER),
            ("High outrage", "partisan news (SemEval)", GOLD),
            ("Reward hook", "clickbait (Webis)", MIDBLUE),
            ("Neutral", "medical + real news", MUTED)]):
        x = M + i * (2.72 + 0.317)
        card(s, x, 1.55, 2.72, 1.9)
        bar(s, x, 1.55, 2.72, 0.07, colour)
        tf = textbox(s, x, 1.75, 2.72, 1.6, align=PP_ALIGN.CENTER)
        para(tf, "100", size=40, bold=True, colour=colour, first=True,
             space_after=0)
        para(tf, name, size=17, bold=True, colour=TEXT, space_after=0)
        para(tf, src, size=12, colour=MUTED, space_after=0)
    for i, (value, label, colour) in enumerate([
            ("162–167", "average words per article,\nlowest to highest group",
             BLUE),
            ("0.027", "smallest η² 400 articles can\ndetect, set before "
                      "scanning", GREEN),
            ("× 2", "every article\nscanned twice", GOLD)]):
        stat(s, M + i * (3.75 + 0.29), 3.8, 3.75, 1.75, value, label,
             colour=colour, size=40)
    tf = textbox(s, M, 5.8, W - 2 * M, 0.35)
    rich(tf, [("All 400, with scores:  ", True, TEXT),
              (CORPUS_URL.replace("https://", ""), True, GOLD)], size=14,
         first=True, space_after=0)
    next_line(s, "reading the corpus page")
    done(s, 4)

    # 6 reading the corpus
    s = page(5)
    header(s, "The method", "Reading the corpus page: what each number means",
           "newspaper")
    card(s, M, 1.45, 6.2, 4.6, line=BLUE)
    tf = textbox(s, M + 0.25, 1.55, 5.8, 0.3)
    para(tf, "COLUMN   →   MEANING", size=11, bold=True, colour=MUTED,
         first=True, space_after=0)
    for i, (column, meaning) in enumerate([
            ("Emotional", "average predicted activity, 1,030 emotional "
                          "points"),
            ("Deliberate", "average predicted activity, 851 reasoning "
                           "points"),
            ("Score", "Emotional − Deliberate = X"),
            ("Pre-scan label", "label from its source, given before any "
                               "scan"),
            ("Words", "article length")]):
        y = 1.95 + i * 0.66
        chip(s, M + 0.2, y, 1.9, 0.54, column, colour=GOLD, size=14,
             bold=True, align=PP_ALIGN.CENTER)
        tf = textbox(s, M + 2.25, y, 3.8, 0.54, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, meaning, size=13, colour=TEXT, first=True, space_after=0)
    tf = textbox(s, M + 0.25, 5.3, 5.8, 0.7)
    rich(tf, [("All 400 scores: ", True, TEXT),
              ("−0.070 to +0.054, spread ΔX = 0.124", False, TEXT)], size=13,
         first=True, space_after=2)
    para(tf, "Units: standardised activity, no physical unit", size=11,
         colour=MUTED, space_after=0)
    card(s, 7.2, 1.45, 5.38, 4.6, line=LINE)
    tf = textbox(s, 7.4, 1.55, 5.0, 0.3)
    para(tf, "AVERAGE SCORE X PER GROUP", size=11, bold=True, colour=MUTED,
         first=True, space_after=0)
    zero, scale = 12.1, 0.02 / 3.2
    bar(s, zero, 1.95, 0.02, 3.1, TEXT)
    tf = textbox(s, zero - 0.5, 5.05, 1.0, 0.3, align=PP_ALIGN.CENTER)
    para(tf, "0", size=12, bold=True, colour=TEXT, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    for i, (name, mean, colour) in enumerate(GROUP_MEANS):
        y = 2.05 + i * 0.75
        length = abs(mean) / scale
        bar(s, zero - length, y + 0.3, length, 0.3, colour)
        tf = textbox(s, 7.4, y - 0.02, 3.2, 0.3)
        para(tf, name, size=13, bold=True, colour=TEXT, first=True,
             space_after=0)
        tf = textbox(s, zero - length - 1.25, y + 0.26, 1.2, 0.35,
                     align=PP_ALIGN.RIGHT)
        para(tf, "%+.3f" % mean, size=13, bold=True, colour=colour,
             first=True, align=PP_ALIGN.RIGHT, space_after=0)
    tf = textbox(s, 7.4, 5.35, 5.0, 0.6)
    para(tf, "All four below 0: the deliberate areas respond more in every "
             "group.", size=12, colour=MUTED, first=True, space_after=0)
    tf = textbox(s, M, 6.2, 6.5, 0.35)
    rich(tf, [("Live: ", True, TEXT),
              (CORPUS_URL.replace("https://", ""), True, GOLD)], size=13,
         first=True, space_after=0)
    next_line(s, "are these differences real?")
    done(s, 5)

    # 7 result 1
    s = page(6)
    header(s, "The results", "Result 1: the four groups differ, η² = 0.107",
           "chart-bar")
    donut(s, M, 1.45, 3.7, 0.1068, BLUE)
    tf = textbox(s, M, 2.8, 3.7, 1.0, align=PP_ALIGN.CENTER)
    para(tf, "10.7%", size=40, bold=True, colour=TEXT, first=True,
         space_after=0)
    tf = textbox(s, M, 5.15, 3.7, 0.9, align=PP_ALIGN.CENTER)
    rich(tf, [("10.7% ", True, BLUE),
              ("of the variation in the score is due to the group",
               False, TEXT)], size=14, first=True, space_after=0)
    math(s, r"\eta^2 = \frac{SS_{\mathrm{between\ groups}}}"
            r"{SS_{\mathrm{total}}} = 0.107", 4.75, 1.5, size=22)
    tf = textbox(s, 4.75, 2.55, 7.8, 0.3)
    para(tf, "η² ON EACH RUN (one-way ANOVA), AGAINST THE SMALLEST WE COULD "
             "DETECT", size=11, bold=True, colour=MUTED, first=True,
         space_after=0)
    scale_bars(s, [("first run", 0.1068, "0.107", BLUE),
                   ("second run", 0.0888, "0.089", MIDBLUE),
                   ("detectable", 0.0268, "0.027", MUTED)],
               top=3.0, maximum=0.12, left=6.35, length=4.6, label_w=1.45,
               step=0.55, size=14)
    stat(s, 4.75, 4.75, 3.8, 1.3, "F = 15.779", "between-group spread ÷ "
         "within-group spread", colour=MIDBLUE, size=24, label_size=12)
    stat(s, 8.78, 4.75, 3.8, 1.3, "p = 1.0 × 10⁻⁹", "probability of F this "
         "large if all 4 groups were equal", colour=GREEN, size=24,
         label_size=12)
    tf = textbox(s, M, 6.15, 6.0, 0.35)
    para(tf, "SS = sum of squares. The other 89.3% is article to article.",
         size=12, colour=MUTED, first=True, space_after=0)
    next_line(s, "which group drives it?")
    done(s, 6)

    # 8 result 2
    s = page(7)
    header(s, "The results", "Result 2: fear drives it, d = 0.94; outrage "
                             "lifts both sides equally", "chart-bar")
    math(s, r"d = \frac{\bar{X}_{\mathrm{group}} - \bar{X}_{\mathrm{neutral}}}"
            r"{s}", M, 1.45, size=20)
    tf = textbox(s, 3.9, 1.55, 8.5, 0.5)
    para(tf, "d = distance from neutral in standard deviations (s). "
             "Reference marks 0.2, 0.5, 0.8.", size=12, colour=MUTED,
         first=True, space_after=0)
    left, length = 2.9, 6.6
    for mark in (0.2, 0.5, 0.8):
        xm = left + length * mark
        bar(s, xm, 2.3, 0.015, 1.7, LINE)
        tf = textbox(s, xm - 0.6, 2.08, 1.2, 0.25, align=PP_ALIGN.CENTER)
        para(tf, "%.1f" % mark, size=11, colour=MUTED, first=True,
             space_after=0)
    scale_bars(s, [("fear-activating", 0.939, "0.94", EMBER),
                   ("reward hook", 0.319, "0.32", MIDBLUE),
                   ("high outrage", 0.030, "0.03", GOLD)],
               top=2.45, maximum=1.0, left=left, length=length, label_w=2.0,
               step=0.55)
    for x, name, emo, rea, verdict, colour in [
            (M, "FEAR", 0.613, -0.098, "score moves:\nd = 0.94", EMBER),
            (6.83, "OUTRAGE", 0.507, 0.491, "score flat:\nd = 0.03", GOLD)]:
        card(s, x, 4.2, 5.75, 2.0, line=colour)
        tf = textbox(s, x + 3.0, 4.35, 2.6, 0.3)
        para(tf, name + ", d per region", size=12, bold=True, colour=colour,
             first=True, space_after=0)
        base = 5.55
        bar(s, x + 0.3, base, 2.4, 0.02, MUTED)
        for j, (val, c, lab) in enumerate([(emo, EMBER, "emotional"),
                                           (rea, BLUE, "deliberate")]):
            bx = x + 0.5 + j * 1.05
            hgt = abs(val) * 1.6
            bar(s, bx, base - hgt if val > 0 else base, 0.7, max(hgt, 0.03), c)
            tf = textbox(s, bx - 0.2, base - hgt - 0.3 if val > 0 else base
                         - 0.3, 1.1, 0.3, align=PP_ALIGN.CENTER)
            para(tf, "%+.2f" % val, size=12, bold=True, colour=c, first=True,
                 space_after=0)
            tf = textbox(s, bx - 0.2, base + 0.2, 1.1, 0.3,
                         align=PP_ALIGN.CENTER)
            para(tf, lab, size=11, colour=MUTED, first=True, space_after=0)
        tf = textbox(s, x + 3.0, 4.75, 2.6, 1.2, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, verdict, size=17, bold=True, colour=colour, first=True,
             space_after=0)
    next_line(s, "can we trust the scores?")
    done(s, 7)

    # 9 result 3
    s = page(8)
    header(s, "The results", "Result 3: scores repeat for groups, not single "
                             "articles", "arrows-clockwise")
    card(s, M, 1.5, 5.75, 3.4, line=BLUE)
    tf = textbox(s, M, 1.65, 5.75, 1.2, align=PP_ALIGN.CENTER)
    para(tf, "0.8725", size=54, bold=True, colour=BLUE, first=True,
         space_after=0)
    para(tf, "ICC: agreement between two runs", size=14, colour=TEXT,
         space_after=0)
    bar(s, M + 0.4, 3.5, 4.95, 0.3, LINE)
    bar(s, M + 0.4, 3.5, 4.95 * 0.8725, 0.3, BLUE)
    for v, label in [(0, "0 = none"), (1, "1 = identical")]:
        tf = textbox(s, M + 0.4 + 4.95 * v - 0.2 - 1.0 * v, 3.9, 1.4, 0.3,
                     align=PP_ALIGN.CENTER)
        para(tf, label, size=12, colour=MUTED, first=True, space_after=0)
    card(s, 6.83, 1.5, 5.75, 3.4, line=EMBER)
    tf = textbox(s, 6.83, 1.65, 5.75, 1.2, align=PP_ALIGN.CENTER)
    para(tf, "51 of 400", size=54, bold=True, colour=EMBER, first=True,
         space_after=0)
    para(tf, "changed sign between runs (12.8%)", size=14, colour=TEXT,
         space_after=0)
    lo, hi, ax0, axw, ay = 40, 70, 7.2, 5.0, 3.65

    def at(v):
        return ax0 + (v - lo) / (hi - lo) * axw

    bar(s, ax0, ay, axw, 0.02, MUTED)
    bar(s, at(44), ay - 0.15, at(67) - at(44), 0.32, MIDBLUE, 0.4)
    bar(s, at(55.3) - 0.02, ay - 0.25, 0.04, 0.52, BLUE)
    plain(s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(at(51) - 0.12),
                             Inches(ay - 0.11), Inches(0.24), Inches(0.24)),
          EMBER)
    tf = textbox(s, 6.83, 4.1, 5.75, 0.6, align=PP_ALIGN.CENTER)
    rich(tf, [("● observed 51   ", True, EMBER),
              ("▌noise predicts 55 (95%: 44 to 67)", True, BLUE)], size=12,
         first=True, space_after=0)
    banner(s, 5.2, "Meaning:", "flipped articles average |X| = 0.003 against "
           "0.022 for the rest, so we report group averages only.", size=15)
    next_line(s, "does the score detect manipulation?")
    done(s, 8)

    # 10 honest check
    s = page(9)
    header(s, "The results", "Honest check: word counting beats our score, "
                             "0.98 vs 0.63", "warning")
    tf = textbox(s, M, 1.45, W - 2 * M, 0.35)
    para(tf, "AUC = chance a random manipulative article scores above a "
             "random neutral one", size=13, colour=MUTED, first=True,
         space_after=0)
    lo, hi, ax0, axw, ay = 0.5, 1.0, 1.3, 10.7, 2.75

    def au(v):
        return ax0 + (v - lo) / (hi - lo) * axw

    bar(s, ax0, ay, axw, 0.06, LINE)
    for v, label in [(0.5, "0.5 = coin toss"), (1.0, "1.0 = perfect")]:
        tf = textbox(s, au(v) - 0.9, ay + 0.2, 1.8, 0.3, align=PP_ALIGN.CENTER)
        para(tf, label, size=12, colour=MUTED, first=True, space_after=0)
    for v, label, colour, above in [(0.5392, "sentiment 0.54", MUTED, False),
                                    (0.6274, "our score 0.63", BLUE, True),
                                    (0.9758, "word counting 0.98", EMBER, True)]:
        plain(s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(au(v) - 0.16),
                                 Inches(ay - 0.13), Inches(0.32), Inches(0.32)),
              colour)
        tf = textbox(s, au(v) - 1.3, ay - 0.62 if above else ay + 0.5, 2.6, 0.4,
                     align=PP_ALIGN.CENTER)
        para(tf, label, size=16, bold=True, colour=colour, first=True,
             space_after=0)
    tf = textbox(s, M, 3.65, 5.5, 0.3)
    para(tf, "WHY: EACH GROUP CAME FROM ONE SOURCE", size=11, bold=True,
         colour=MUTED, first=True, space_after=0)
    for i, (grp, src) in enumerate([("fear", "ISOT fake"),
                                    ("outrage", "SemEval"),
                                    ("reward hook", "Webis"),
                                    ("neutral", "PubMed + ISOT")]):
        y = 4.0 + i * 0.5
        chip(s, M, y, 2.1, 0.42, grp, size=13, align=PP_ALIGN.CENTER)
        arrow(s, 2.95, y + 0.14, 0.5, 0.14, EMBER)
        chip(s, 3.55, y, 2.5, 0.42, src, size=13, align=PP_ALIGN.CENTER)
    stat(s, 6.6, 3.7, 2.8, 1.85, "66%", "of articles: words identify\n"
         "the source (chance 25%)", colour=EMBER, size=36)
    card(s, 9.6, 3.7, 2.98, 1.85, line=BLUE)
    tf = textbox(s, 9.75, 3.8, 2.7, 1.7, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, "So our score is a measurement for the physics, not a detector.",
         size=15, bold=True, colour=BLUE, first=True, space_after=0)
    next_line(s, "does the brain model match real brains?")
    done(s, 9)

    # 11 real brains
    s = page(10)
    header(s, "The results", "Does the brain model match real brains? "
                             "r = +0.028, p = 0.048", "target")
    tf = textbox(s, M, 1.45, W - 2 * M, 0.35)
    para(tf, "Public brain scans of 4 people watching Friends (Algonauts "
             "2025).  r = correlation: 0 = no match, 1 = perfect.", size=13,
         colour=MUTED, first=True, space_after=0)
    scale_bars(s, [("people vs each other,\nfull episode", 0.1517, "0.152",
                    MUTED),
                   ("ceiling,\n2-minute clip", 0.0959, "0.096", BLUE),
                   ("our model,\n2-minute clip", 0.0283, "0.028", GREEN)],
               top=2.1, maximum=0.17, left=3.6, length=6.8, label_w=2.6,
               step=0.8, size=14)
    stat(s, M, 4.65, 3.75, 1.35, "30%", "of the clip ceiling\n"
         "(0.028 ÷ 0.096)", colour=GREEN, size=30)
    stat(s, 4.79, 4.65, 3.75, 1.35, "p = 0.048", "against 61 time-shifted "
         "copies;\ncut-off 0.05", colour=GOLD, size=30)
    stat(s, 8.83, 4.65, 3.75, 1.35, "3 bugs", "found and fixed along the "
         "way", colour=EMBER, size=30)
    banner(s, 6.1, "Meaning:", "the sign is positive (+0.028). The "
           "full-episode run is next, in Paper 3.", h=0.5, size=15)
    next_line(s, "the physics")
    done(s, 10)

    # 12 the minimum push
    s = page(11)
    header(s, "The physics", "The minimum push media would need: "
                             "α ≥ 4.29", "ruler")
    card(s, M, 1.45, 5.7, 4.75, line=BLUE)
    math(s, r"h = \alpha X \;\Rightarrow\; \alpha \geq "
            r"\frac{h_c(\beta J)}{\Delta X}", M, 1.65, size=28, centre_w=5.7)
    for i, (sym, name, text) in enumerate([
            ("h", "external field", "media's push on everyone"),
            ("X", "observable", "our score for an article"),
            (r"\alpha", "coupling constant", "push per unit of score"),
            (r"h_c", "critical field", "smallest push that flips the "
                                       "majority"),
            (r"\beta J", "reduced coupling", "how strongly people copy "
                                             "each other"),
            (r"\Delta X", "spread", "highest − lowest score = 0.124")]):
        y = 2.72 + i * 0.57
        math(s, sym, M + 0.15, y + 0.06, size=19, colour=GOLD, centre_w=0.95)
        tf = textbox(s, M + 1.2, y, 4.4, 0.55, anchor=MSO_ANCHOR.MIDDLE)
        rich(tf, [(name + "  ", True, BLUE), ("= " + text, False, TEXT)],
             size=13, first=True, space_after=0)
    alpha_curve(s, 6.75, 1.4, 5.9, 3.7)
    tf = textbox(s, 6.75, 5.0, 5.9, 0.3, align=PP_ALIGN.CENTER)
    para(tf, "reduced coupling βJ  →", size=12, colour=MUTED, first=True,
         space_after=0)
    tf = textbox(s, 6.95, 1.35, 3, 0.3)
    para(tf, "minimum α", size=12, colour=MUTED, first=True, space_after=0)
    stat(s, 6.75, 5.35, 5.83, 0.85, "α ≥ 0.533 ÷ 0.124 = 4.29",
         "at βJ = 2, where the critical field is 0.533", colour=EMBER, size=22)
    next_line(s, "what it could be used for")
    done(s, 11)

    # 13 children's content
    s = page(12)
    header(s, "What's next", "Can it analyse any content, even what children "
                             "watch?", "target")
    for i, (head, colour, icon_name, items) in enumerate([
            ("CAN DO", GREEN, "check-circle",
             ["Score video, audio and text", "Compare groups of content",
              "Rate content, never the viewer"]),
            ("NOT YET", EMBER, "x-circle",
             ["Model learned from adult brains", "Only news text was tested",
              "1 in 8 single scores flip"]),
            ("WOULD TAKE", BLUE, "flag-banner",
             ["Child brain data, with ethics approval",
              "A children's video test set",
              "Safeguards against targeting children"])]):
        x = M + i * (3.75 + 0.29)
        card(s, x, 1.5, 3.75, 3.85, line=colour)
        icon(s, icon_name, x + 3.75 / 2 - 0.3, 1.7, h=0.6)
        tf = textbox(s, x, 2.4, 3.75, 0.4, align=PP_ALIGN.CENTER)
        para(tf, head, size=16, bold=True, colour=colour, first=True,
             space_after=0)
        for j, text in enumerate(items):
            chip(s, x + 0.2, 2.95 + j * 0.78, 3.35, 0.66, text, size=14,
                 align=PP_ALIGN.CENTER)
    banner(s, 5.6, "Short answer:", "technically possible, but not yet valid "
           "for children.", h=0.6)
    next_line(s, "the limits, and what fixes each")
    done(s, 12)

    # 14 limits
    s = page(13)
    header(s, "What's next", "Each limit points to the next study", "x-circle")
    for x, label, colour in [(M, "LIMIT", EMBER), (6.2, "NEXT STUDY", GREEN)]:
        tf = textbox(s, x, 1.45, 4, 0.3)
        para(tf, label, size=11, bold=True, colour=colour, first=True,
             space_after=0)
    for i, (limit, nxt) in enumerate([
            ("Predictions, not brain scans", "Check against more real brain "
                                             "data"),
            ("Group mixed up with source", "New set: every source has every "
                                           "type"),
            ("Brain surface only", "A model that predicts deep areas"),
            ("α not measured", "Link scores to real opinion data (polls)"),
            ("Brain check is 2 minutes", "The full episode")]):
        y = 1.8 + i * 0.86
        chip(s, M, y, 4.85, 0.72, limit, line=EMBER, bold=True)
        arrow(s, 5.65, y + 0.29, 0.45, 0.16, GREEN)
        chip(s, 6.2, y, 6.38, 0.72, nxt, line=GREEN)
    next_line(s, "where the work goes")
    done(s, 13)

    # 15 taking it further
    s = page(14)
    header(s, "What's next", "Taking it further: where this research can go",
           "flag-banner")
    for i, (head, colour, icon_name, items) in enumerate([
            ("PUBLISH", BLUE, "books",
             ["Paper 1 → Physica A", "Paper 2 → Physica A",
              "Paper 3 → Imaging Neuroscience", "Preprints first (arXiv)"]),
            ("EXTEND THE SCIENCE", GREEN, "atom",
             ["Kenya: 2024 Finance Bill (funding)", "Video and audio content",
              "Measure α with opinion data", "Children's media, ethically"]),
            ("OPPORTUNITIES", GOLD, "target",
             ["Postgraduate research topic", "Neuroscience + media "
              "collaborations", "Open tool, already online",
              "Group-level media audits"])]):
        x = M + i * (3.75 + 0.29)
        card(s, x, 1.5, 3.75, 4.55, line=colour)
        icon(s, icon_name, x + 0.25, 1.7, h=0.45)
        tf = textbox(s, x + 0.85, 1.72, 2.8, 0.45)
        para(tf, head, size=15, bold=True, colour=colour, first=True,
             space_after=0)
        for j, text in enumerate(items):
            chip(s, x + 0.2, 2.45 + j * 0.88, 3.35, 0.74, text, size=14)
    next_line(s, "conclusions")
    done(s, 14)

    # 16 conclusions
    s = page(15)
    header(s, "What's next", "Conclusions", "check-circle")
    for i, (value, colour, claim, meaning) in enumerate([
            ("0.8725", BLUE, "A field observable can be measured",
             "ICC: agreement between two runs"),
            ("0.107", GREEN, "It separates the four groups",
             "η²: 10.7% of variation due to group; source mixed in"),
            ("α ≥ 4.29", EMBER, "Media strength has a minimum",
             "at βJ = 2, within the mean-field model"),
            ("r = 0.028", GOLD, "The brain model matches real brains",
             "positive; 30% of the 0.096 ceiling")]):
        x = M + (i % 2) * 6.08
        y = 1.5 + (i // 2) * 1.85
        card(s, x, y, 5.75, 1.65, line=colour)
        tf = textbox(s, x + 0.2, y + 0.1, 0.5, 0.5)
        para(tf, str(i + 1), size=20, bold=True, colour=colour, first=True,
             space_after=0)
        tf = textbox(s, x + 0.7, y + 0.12, 4.9, 1.45)
        para(tf, value, size=30, bold=True, colour=colour, first=True,
             space_after=2)
        para(tf, claim, size=15, bold=True, colour=TEXT, space_after=0)
        para(tf, meaning, size=12, colour=MUTED, space_after=0)
    banner(s, 5.35, "Three papers follow.", "Paper 1 and Paper 2 → Physica A,  "
           "Paper 3 → Imaging Neuroscience.", colour=BLUE, h=0.55, size=14)
    tf = textbox(s, M, 6.05, W - 2 * M, 0.5, align=PP_ALIGN.CENTER)
    para(tf, "Thank you.  Questions welcome.", size=22, bold=True,
         colour=GOLD, first=True, align=PP_ALIGN.CENTER, space_after=0)
    done(s, 15)

    name = "Monarch_Defence_Deck_Script.pptx" if with_notes \
        else "Monarch_Defence_Deck.pptx"
    out = os.path.join(HERE, name)
    prs.save(out)
    return out, len(prs.slides)


def write_script():
    total = sum(entry[2] for entry in SLIDES)
    blocks = ["MONARCH DEFENCE SCRIPT  (about %g min)" % total]
    for i, entry in enumerate(SLIDES):
        blocks.append("=" * 72 + "\nSLIDE %d  %s\n" % (i + 1, entry[0])
                      + notes_for(i))
    out = os.path.join(HERE, "Monarch_Defence_Script.txt")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n\n".join(blocks) + "\n")
    return out


if __name__ == "__main__":
    for path, count in (build_deck(False), build_deck(True)):
        print("wrote", path, count, "slides")
    print("wrote", write_script())
