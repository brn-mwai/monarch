"""Build two plain-language decks for the supervisor meeting.

Monarch_Supervisor_Deck.pptx  the 15 slides shown to Dr. Songa, script in notes.
Monarch_Presenter_Script.pptx a script card per slide, likely questions with
                              answers, and a plain-words sheet for every number.
"""

import os

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

from deck_theme import (BLUE, EMBER, FIG, GOLD, GREEN, HERE, LINE, M,
                        MIDBLUE, MUTED, TEXT, W, arrow, bar, card,
                        figure, footer, glow, header, icon, lattice, new_deck,
                        number_card, para, plain, rich, scale_bars, slide,
                        textbox)

SECTIONS = ["The idea", "The method", "The results", "The physics",
            "What's next"]

SCRIPT = [
    ("Title", None,
     "Good morning, Dr. Songa, and thank you for the time. I'll take you through "
     "the dissertation as it stands after your review: what I set out to do, the "
     "tools and steps, what we found, where the proposal turned out wrong, what "
     "the work cannot claim, and the three papers. About fifteen minutes, and I'll "
     "end with what I need from you.",
     ["About 15 minutes in total", "End with the four requests"]),
    ("The question", "The idea",
     "Here is the idea in one picture. Physicists model a group forming an "
     "opinion the same way they model tiny magnets lining up. Each arrow is a "
     "person, and people tend to copy those around them. Media is an outside push "
     "on everyone at once. In every study I read, the size of that push is simply "
     "chosen by the researcher. My question was: can we measure it from the "
     "content itself?",
     ["h = the push from media", "J = how much people copy each other"]),
    ("Plan vs reality", "The idea",
     "Before the results, I want to be upfront about what changed from the "
     "proposal. Five assumptions turned out differently once we tested the tools. "
     "The biggest: we planned to measure the amygdala, the brain's alarm centre, "
     "but the model only predicts the brain's outer surface. So we used "
     "emotion-linked and reasoning-linked areas on the surface instead. All of "
     "this is in the amendment you approved.",
     ["5 changes, all in the approved amendment",
      "Ratio broke for 69 of 400 articles",
      "Two physics coefficients corrected"]),
    ("Tools", "The method",
     "These are the tools. The main one is TRIBE v2, published by Meta's research "
     "lab. It learned from brain scans of adult volunteers watching TV and films, "
     "and it predicts how a typical brain would respond to new content. Because it "
     "was built on people listening, we read each article aloud first. Nobody was "
     "scanned in this project. Every brain value you'll see is a prediction.",
     ["TRIBE v2: Meta, 2025", "About 70 seconds per article on a P100",
      "No person was scanned"]),
    ("Process", "The method",
     "This is the whole process for one article. It's turned into speech, the "
     "timing of each word is marked, and the model predicts activity at 20,484 "
     "points across the brain's surface. We average 1,030 points in areas linked "
     "to emotion and 851 in areas linked to careful reasoning. The score is "
     "emotion minus reasoning. Above zero, emotion leads. Below zero, reasoning "
     "leads.",
     ["20,484 points on the brain surface", "1,030 emotion, 851 reasoning",
      "Score = emotion minus reasoning"]),
    ("The articles", "The method",
     "We scored 400 articles from four public collections, 100 each: fear-driven "
     "fake news, outrage-style partisan news, clickbait, and neutral writing. We "
     "matched their lengths so no group wins by being longer, and we worked out "
     "before scanning that 400 was enough to see a small effect. Then we ran every "
     "article twice.",
     ["4 groups x 100 articles", "About 164 words each",
      "Smallest detectable effect 0.027", "Every article scanned twice"]),
    ("Groups differ", "The results",
     "First result: the four groups really do differ. The number is eta squared, "
     "0.107. In plain terms, about 11 percent of the differences between articles "
     "line up with their group. The rest is article-to-article variation, because "
     "the groups overlap a lot. The chance of this being luck is about one in a "
     "billion, and the second run gave 0.089, so it held.",
     ["0.107 = about 11% explained by group", "p = about 1 in a billion",
      "Second run 0.089"]),
    ("Which group", "The results",
     "Which group drives it? Fear. Compared with neutral articles, fear-driven "
     "ones differ by 0.94, which counts as large. Clickbait is small. Outrage "
     "barely moves, which surprised us, because the proposal expected it to be "
     "strongest. Looking closer, outrage raises both the emotion and the reasoning "
     "areas by about the same amount, so the gap between them stays flat.",
     ["Fear 0.94 (large)", "Clickbait 0.32 (small)",
      "Outrage 0.03: both areas rise, 0.51 and 0.49"]),
    ("Repeatable?", "The results",
     "Can we trust the score? We ran all 400 articles twice. Agreement between "
     "runs is 0.87, where 1 means identical, so it's high. It isn't perfect "
     "because the speech voice and the computer's arithmetic vary slightly. 51 "
     "articles flipped sign. Noise alone predicts about 55, and those articles all "
     "sit near zero. So we only make claims about groups, never one article.",
     ["Agreement 0.87 (1 = identical)",
      "51 flipped, about 55 expected (44 to 67)"]),
    ("Honest check", "The results",
     "Now the most important honest check. Simple word counting sorted "
     "manipulative from neutral articles far better than our score: 0.98 against "
     "0.63, where 0.5 is a coin toss. The reason is that each group came from a "
     "different source, and the words give the source away. So we can't say the "
     "differences come from writing style alone. Our score is a measurement for "
     "the physics, not a manipulation detector.",
     ["Word counting 0.98, ours 0.63, sentiment 0.54", "0.5 = coin toss",
      "Source guessed 66% of the time vs 25% by chance"]),
    ("Real brains", "The results",
     "Does the brain model match real brains at all? A company audit claimed it "
     "was the opposite of real brain data, so we tested it on public scans of "
     "people watching the show Friends. Real people's brains agree with each "
     "other at 0.152, the best any model can reach. On a two-minute clip the model "
     "scored 0.028, against a best possible of 0.096 on that clip. Weak, but "
     "positive. We also found and fixed three hidden bugs. This is Paper 3.",
     ["Best possible 0.152 (full episode)",
      "Model 0.028 vs 0.096 on the 2-minute clip", "p = 0.048",
      "3 bugs found and fixed"]),
    ("The minimum push", "The physics",
     "Here is the physics result. Media's push equals our score times a strength "
     "called alpha. We couldn't measure alpha from the data, so we don't quote "
     "one. Instead we asked: how big must alpha be for media alone to flip a "
     "majority? With our scores spread over 0.124, the answer is at least 4.29 "
     "when people copy each other strongly. Any future claim that content like "
     "this flips opinion has to clear that bar.",
     ["Spread of scores 0.124 (-0.070 to +0.054)", "Alpha at least 4.29 at "
      "copying strength 2", "No value of alpha is claimed"]),
    ("Children's content", "What's next",
     "At my first presentation I was asked whether this could analyse any "
     "content, even what children watch. Technically, yes: the pipeline takes "
     "video and audio, so it could score a cartoon or an advert. But the model "
     "learned from adult brains, and children's brains are still developing, so it "
     "can't say how a child reacts. We also only tested news text. For children, "
     "we'd need child brain data and ethics approval first.",
     ["Can: video and audio, groups of content", "Cannot: adult-trained model, "
      "1 in 8 items flip", "Needs: child data and ethics approval"]),
    ("Limits", "What's next",
     "To be clear about the limits: every brain value is a prediction, not a scan. "
     "Group and source are mixed together in this dataset. The model can't see "
     "deep areas like the amygdala. We couldn't measure alpha. And the check "
     "against real brains used only two minutes of video. Each is stated in the "
     "thesis, and each points to the next piece of work.",
     ["5 limits, each stated in the thesis"]),
    ("Papers and requests", "What's next",
     "Three papers come out of this. Paper 1 is pure physics: the minimum-push "
     "rule, no brain data needed. Paper 2 is the measuring tool and the 400 "
     "articles, including the word-counting comparison. Paper 3 is the check "
     "against real brains. The dissertation comes first. I'd like any corrections "
     "you need, your signature on the declaration page, and clearance for the "
     "library by Thursday. And I'd like to ask about co-authorship on the papers.",
     ["Bound copy to the library by Thu 24 Sep",
      "Graduation clearance by Mon 28 Sep", "Ask about co-authorship"]),
]

QUESTIONS = [
    ("Can this analyse any content, even what children watch?",
     "Technically it can score video and audio, not only text. But the model "
     "learned from adult brains, so it can't tell us how a child reacts, and we "
     "only tested news text. It would need child brain data and ethics approval "
     "first."),
    ("Could a parent or a regulator use it to rate one show?",
     "Not yet. About 1 in 8 items flip between runs, so a single score isn't "
     "reliable. It's only trustworthy for comparing groups of content, and not for "
     "children until it has been tested on them."),
    ("Was anyone scanned? Is it reading people's minds?",
     "No. Nobody was scanned. The scores are predictions from a published model "
     "of a typical adult brain. The tool rates content, not people, and knows "
     "nothing about any individual."),
    ("Could someone use it to make content more manipulative?",
     "That's a real risk with any measurement of content. That's why it's framed "
     "as a research measurement, reports only group results, and the model's "
     "licence allows non-commercial research only."),
    ("If word counting does better, why not use that?",
     "Word counting answers a different question: it mostly learns which source "
     "an article came from. Our score is meant to be the push in the opinion "
     "model. The comparison is there to be honest about what the score is not."),
    ("Why read the articles aloud?",
     "The model was trained on people watching and listening, so it expects "
     "speech with word timings. Reading aloud puts the article in the form the "
     "model understands."),
    ("Why no amygdala, when the proposal named it?",
     "The released model only predicts the brain's outer surface. The amygdala "
     "sits deep inside, so we can't measure it and make no claim about it. We "
     "used surface areas linked to emotion instead."),
    ("What would it take to work for children's media?",
     "Brain scans from children collected with ethics approval and consent, a "
     "test set of children's videos, content where source and type are mixed, and "
     "a longer check against real brains."),
    ("Why is this a physics project?",
     "The opinion model is statistical physics, the same maths as magnets lining "
     "up. The contribution is measuring the push in that model and working out "
     "the minimum strength it needs. The brain model is the measuring tool."),
    ("What does 'alpha at least 4.29' mean in practice?",
     "It's a bar to clear. If someone claims content like this flips a strongly "
     "connected group's opinion, their alpha must be at least 4.29, or the model "
     "says it can't happen. It does not say media does flip opinion."),
    ("Why only 400 articles?",
     "We calculated before scanning that 400 was enough to see an effect as small "
     "as 2.7%. Each article takes about a minute of GPU time, and we ran all of "
     "them twice."),
    ("Is it okay to use Meta's model?",
     "Yes, for research. It's released under a non-commercial licence, it's cited "
     "throughout, and this project makes no money from it."),
]

GLOSSARY = [
    ("η², eta squared", "Share of the differences explained by group. "
                        "0.107 is about 11%."),
    ("p-value", "Chance a result this strong appears by luck. "
                "1 × 10⁻⁹ is about one in a billion."),
    ("d, Cohen's d", "Size of a difference in units of normal spread. "
                     "0.2 small, 0.5 medium, 0.8 large."),
    ("ICC", "Agreement between two runs. 1 identical, 0 none. Ours 0.87."),
    ("AUC", "How well a score sorts two kinds of article. "
            "0.5 coin toss, 1 perfect."),
    ("r, correlation", "How closely two things rise and fall together. "
                       "0 none, 1 perfect."),
    ("Noise ceiling", "Best score any model can reach, given how much real "
                      "brains differ. Ours 0.152."),
    ("α, alpha", "Strength of media's push per unit of our score. Not measured."),
    ("βJ", "How strongly people copy each other. Above 1, a group settles on a "
           "majority by itself."),
    ("ΔX", "Spread of our scores, lowest to highest: 0.124."),
    ("h with small c", "The critical push: what it takes to flip a majority."),
]


def body(s, index):
    section = SCRIPT[index][1]
    footer(s, SECTIONS, section, index + 1)


def build_supervisor():
    prs = new_deck()

    def page(i):
        return slide(prs, notes=SCRIPT[i][2])

    # 1 title
    s = page(0)
    lattice(s, 8.75, 1.15, 7, 9, 0.52, seed=7, bias=0.64)
    tf = textbox(s, 8.75, 5.95, 3.64, 0.5, align=PP_ALIGN.CENTER)
    para(tf, "each arrow is one person's opinion", size=13, colour=MUTED,
         first=True, align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, M + 0.15, 1.15, 7.6, 0.4)
    para(tf, "B.Sc. PHYSICS   ·   CUEA   ·   SUPERVISOR MEETING", size=13,
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
    para(tf, "21 September 2026", size=15, colour=MUTED, space_after=0)

    # 2 the question
    s = page(1)
    header(s, "The idea", "Physics treats media as a push on opinion. Nobody "
                          "measures how big that push is", "waveform")
    lattice(s, 8.9, 1.75, 6, 6, 0.55, seed=3, bias=0.66)
    arrow_up = s.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(12.45),
                                  Inches(2.3), Inches(0.35), Inches(2.2))
    plain(arrow_up, GOLD)
    tf = textbox(s, 8.6, 5.15, 4.3, 0.8, align=PP_ALIGN.CENTER)
    para(tf, "Arrows are people. Gold arrow is media, pushing everyone the "
             "same way.", size=13, colour=MUTED, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, M, 1.65, 7.4, 2.4)
    for i, (lead, rest) in enumerate([
            ("Each person holds one of two opinions. ",
             "Like a magnet pointing up or down."),
            ("People copy those around them. ",
             "Physicists call this the coupling, J."),
            ("Media pushes everyone the same way. ",
             "This is the field, h. Same maths as magnets lining up.")]):
        rich(tf, [("%d   " % (i + 1), True, EMBER), (lead, True, TEXT),
                  (rest, False, MUTED)], size=17, first=(i == 0),
             space_after=12)
    shp = card(s, M, 4.15, 7.4, 0.85)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, "Every study we found picks the size of h by hand.", size=17,
         colour=TEXT, first=True, space_after=0)
    shp = card(s, M, 5.2, 7.4, 0.95, line=EMBER)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [("Our question: ", True, EMBER),
              ("can h be measured from the content itself?", True, TEXT)],
         size=19, first=True, space_after=0)
    body(s, 1)

    # 3 plan vs reality
    s = page(2)
    header(s, "The idea", "What the proposal assumed, and what testing "
                          "the tools showed", "magnifying-glass")
    cols = [(M, 3.75, "THE PROPOSAL ASSUMED", MUTED),
            (4.65, 4.05, "WHAT WE FOUND", EMBER),
            (8.85, 3.73, "WHAT WE DID", BLUE)]
    for x, w, label, colour in cols:
        tf = textbox(s, x, 1.45, w, 0.35)
        para(tf, label, size=11, bold=True, colour=colour, first=True,
             space_after=0)
    rows = [
        ("We would measure the amygdala, the brain's alarm centre.",
         "The model only predicts the brain's outer surface.",
         "Used emotion-linked and reasoning-linked surface areas."),
        ("The score would be a ratio of the two areas.",
         "Averages sit near zero, so the ratio broke for 69 of 400 articles.",
         "Used a simple difference: emotion minus reasoning."),
        ("Outrage articles would stand out the most.",
         "Outrage raised both areas by the same amount.",
         "Reported it; fear is what stands out."),
        ("We would measure alpha, the strength of media's push.",
         "The data could not pin it down.",
         "Worked out the minimum alpha instead."),
        ("The score would detect manipulative articles.",
         "Simple word counting did better.",
         "Presented it as a measurement, not a detector."),
    ]
    for i, row in enumerate(rows):
        y = 1.85 + i * 0.8
        for (x, w, _, colour), text in zip(cols, row):
            shp = card(s, x, y, w, 0.7, line=LINE)
            tf = shp.text_frame
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            para(tf, text, size=13, colour=TEXT if colour != MUTED else MUTED,
                 first=True, space_after=0)
    tf = textbox(s, M, 5.95, W - 2 * M, 0.4)
    para(tf, "We also corrected two coefficients in the proposal's physics "
             "equation. All changes are in the approved amendment.", size=13,
         colour=MUTED, first=True, space_after=0)
    body(s, 2)

    # 4 tools
    s = page(3)
    header(s, "The method", "The tools we used, and why each one", "books")
    tools = [
        ("TRIBE v2", "Meta research, 2025",
         "An AI model that predicts brain activity from text, sound and video. "
         "It learned from brain scans of adult volunteers watching TV and films."),
        ("Text-to-speech", "reads each article aloud",
         "The model was built on people listening, not reading, so every "
         "article is spoken first."),
        ("Word timing tool", "forced alignment",
         "Marks the moment each word is spoken, so the words and the sound "
         "line up for the model."),
        ("Brain area map", "Glasser et al., 2016",
         "A standard map that names areas of the brain's surface. We used it to "
         "pick emotion and reasoning areas."),
        ("400 public articles", "four published collections",
         "Anyone can download the same articles and check every number."),
        ("Cloud GPU + Python", "free Kaggle Tesla P100",
         "About 70 seconds per article. All code and results are public on "
         "GitHub."),
    ]
    cw, ch = 3.75, 1.85
    for i, (name, tag, what) in enumerate(tools):
        x = M + (i % 3) * (cw + 0.29)
        y = 1.55 + (i // 3) * (ch + 0.2)
        shp = card(s, x, y, cw, ch, line=BLUE if i == 0 else LINE)
        tf = shp.text_frame
        tf.margin_top = Inches(0.16)
        para(tf, name, size=18, bold=True, colour=BLUE, first=True,
             space_after=0)
        para(tf, tag, size=12, colour=MUTED, space_after=6)
        para(tf, what, size=13, colour=TEXT, space_after=0)
    shp = card(s, M, 5.65, W - 2 * M, 0.6, line=EMBER)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [("No person was scanned. ", True, EMBER),
              ("Every brain value in this work is a prediction from the model.",
               False, TEXT)], size=16, first=True, space_after=0)
    body(s, 3)

    # 5 process
    s = page(4)
    header(s, "The method", "How one article becomes one number", "brain")
    steps = [("1", "Article", "about 164 words"),
             ("2", "Spoken aloud", "text-to-speech"),
             ("3", "Word timings", "when each word is said"),
             ("4", "Brain prediction", "20,484 points"),
             ("5", "Two averages", "emotion and reasoning")]
    sw, gap = 2.12, 0.31
    for i, (n_, head, sub) in enumerate(steps):
        x = M + i * (sw + gap)
        shp = card(s, x, 1.5, sw, 1.05, line=BLUE if i == 3 else LINE)
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        rich(tf, [(n_ + "  ", True, EMBER), (head, True, TEXT)], size=15,
             first=True, align=PP_ALIGN.CENTER, space_after=2)
        para(tf, sub, size=12, colour=MUTED, align=PP_ALIGN.CENTER,
             space_after=0)
        if i < len(steps) - 1:
            arrow(s, x + sw + 0.05, 1.95, gap - 0.1, 0.15)
    figure(s, os.path.join(FIG, "B1_roi_definition.png"), M + 0.12, 3.0,
           w=5.9)
    tf = textbox(s, M, 5.8, 6.2, 0.5)
    para(tf, "Orange: 1,030 emotion-linked points. Blue: 851 reasoning-linked "
             "points.", size=13, colour=MUTED, first=True, space_after=0)
    shp = card(s, 7.35, 2.95, 5.23, 3.2, line=BLUE)
    tf = shp.text_frame
    tf.margin_top = Inches(0.18)
    para(tf, "THE SCORE, X", size=12, bold=True, colour=MUTED, first=True,
         space_after=6)
    rich(tf, [("X = ", True, TEXT), ("emotion", True, EMBER),
              (" − ", True, TEXT), ("reasoning", True, BLUE)], size=28,
         space_after=10)
    rich(tf, [("Above 0: ", True, EMBER),
              ("emotion areas predicted more active.", False, TEXT)], size=15,
         space_after=4)
    rich(tf, [("Below 0: ", True, BLUE),
              ("reasoning areas predicted more active.", False, TEXT)],
         size=15, space_after=10)
    rich(tf, [("20,484 ", True, BLUE),
              ("= points on a standard model of the brain's surface, where the "
               "prediction is made.", False, MUTED)], size=13, space_after=0)
    body(s, 4)

    # 6 the articles
    s = page(5)
    header(s, "The method", "400 articles in four groups, matched in length",
           "newspaper")
    groups = [("Fear-driven", "fake news collection (ISOT)", EMBER),
              ("Outrage", "hyperpartisan news (SemEval-2019)", GOLD),
              ("Clickbait", "clickbait headlines (Webis-17)", MIDBLUE),
              ("Neutral", "medical abstracts + real news", MUTED)]
    gw = 2.72
    for i, (name, src, colour) in enumerate(groups):
        x = M + i * (gw + 0.317)
        shp = card(s, x, 1.55, gw, 1.55)
        bar(s, x, 1.55, 0.06, 1.55, colour)
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(tf, "100", size=32, bold=True, colour=colour, first=True,
             align=PP_ALIGN.CENTER, space_after=0)
        para(tf, name, size=16, bold=True, colour=TEXT, align=PP_ALIGN.CENTER,
             space_after=2)
        para(tf, src, size=11, colour=MUTED, align=PP_ALIGN.CENTER,
             space_after=0)
    nw = 3.75
    for i, (value, name, means, why) in enumerate([
            ("≈ 164", "words per article, on average",
             "All four groups are within 5 words of each other.",
             "So a longer article can't score differently just by being longer."),
            ("0.027", "smallest effect the study could see",
             "We sized the study before scanning a single article.",
             "400 articles is enough to catch a difference as small as 2.7%."),
            ("× 2", "every article scanned twice",
             "Two separate runs on the GPU.",
             "Lets us measure how repeatable the score is.")]):
        number_card(s, M + i * (nw + 0.29), 3.4, nw, 2.75, value, name, means,
                    why)
    body(s, 5)

    # 7 groups differ
    s = page(6)
    header(s, "The results", "Result 1: the four groups really do differ",
           "chart-bar")
    glow(s, 3.4, 2.5, 4.5, MIDBLUE, 0.3)
    tf = textbox(s, M, 1.5, 5.8, 0.35)
    para(tf, "HOW MUCH THE GROUPS DIFFER (η²)", size=12, bold=True,
         colour=MUTED, first=True, space_after=0)
    tf = textbox(s, M, 1.85, 5.8, 1.4)
    para(tf, "0.107", size=80, bold=True, colour=TEXT, first=True,
         space_after=0)
    scale_bars(s, [("first run", 0.1068, "0.107", BLUE),
                   ("second run", 0.0888, "0.089", MIDBLUE),
                   ("smallest we could see", 0.0268, "0.027", MUTED)],
               top=3.75, maximum=0.12, left=2.85, length=2.9, label_w=2.1,
               step=0.6, size=14)
    tf = textbox(s, M, 5.65, 6.0, 0.5)
    para(tf, "The second run repeats the result. Both are far above what we "
             "could detect.", size=13, colour=MUTED, first=True, space_after=0)
    number_card(s, 7.0, 1.5, 5.58, 2.2, "≈ 11%",
                "η² = 0.107: share of the differences explained by group",
                "Knowing an article's group explains about 11% of why its score "
                "differs from the others.",
                "The groups overlap a lot; most variation is from one article "
                "to the next.")
    number_card(s, 7.0, 3.95, 5.58, 2.2, "1 in a billion",
                "p = 1.0 × 10⁻⁹: the chance this is luck",
                "If the groups were truly the same, a pattern this strong would "
                "appear by chance about once in a billion tries.",
                "400 articles and a consistent difference between groups.",
                colour=GREEN)
    body(s, 6)

    # 8 which group
    s = page(7)
    header(s, "The results", "Fear drives the difference; outrage barely "
                             "moves the score", "chart-bar")
    tf = textbox(s, M, 1.5, 8, 0.35)
    para(tf, "DIFFERENCE FROM NEUTRAL ARTICLES (COHEN'S d)", size=12,
         bold=True, colour=MUTED, first=True, space_after=0)
    left, length = 3.3, 6.2
    for mark, label in [(0.2, "small"), (0.5, "medium"), (0.8, "large")]:
        x = left + length * mark
        bar(s, x, 2.05, 0.015, 1.75, LINE)
        tf = textbox(s, x - 0.6, 1.8, 1.2, 0.3, align=PP_ALIGN.CENTER)
        para(tf, "%s %.1f" % (label, mark), size=11, colour=MUTED, first=True,
             align=PP_ALIGN.CENTER, space_after=0)
    scale_bars(s, [("fear-driven", 0.939, "0.94  large", EMBER),
                   ("clickbait", 0.319, "0.32  small", MIDBLUE),
                   ("outrage", 0.030, "0.03  none", GOLD)],
               top=2.2, maximum=1.0, left=left, length=length, label_w=2.3)
    number_card(s, M, 4.2, 5.75, 1.95, "d",
                "Cohen's d: how big a difference is",
                "Measured in units of the normal spread of scores. 0.2 is small, "
                "0.5 medium, 0.8 large.",
                "Fear articles sit almost one full spread away from neutral.",
                value_size=24)
    shp = card(s, 6.83, 4.2, 5.75, 1.95, line=GOLD)
    tf = shp.text_frame
    tf.margin_top = Inches(0.16)
    para(tf, "WHY OUTRAGE STAYS FLAT", size=12, bold=True, colour=GOLD,
         first=True, space_after=6)
    rich(tf, [("Outrage raised emotion areas by 0.51 and reasoning areas by "
               "0.49. ", True, TEXT),
              ("The score is the gap between them, so it barely moves. Fear "
               "raised emotion areas only (0.61 vs −0.10).", False, TEXT)],
         size=14, space_after=0)
    body(s, 7)

    # 9 repeatable
    s = page(8)
    header(s, "The results", "The score repeats well for groups, not for "
                             "single articles", "arrows-clockwise")
    number_card(s, M, 1.5, 5.75, 2.35, "0.87",
                "Agreement between the two runs (ICC = 0.8725)",
                "1 means identical, 0 means no agreement. 0.87 is high.",
                "The speech voice and the computer's arithmetic vary a little "
                "between runs.", value_size=40)
    number_card(s, 6.83, 1.5, 5.75, 2.35, "51 of 400",
                "Articles whose score flipped sign (12.8%)",
                "Noise alone predicts about 55. The ones that flipped all sit "
                "near zero.",
                "A score near zero tips either way with a tiny wobble, so we "
                "never judge one article.", colour=EMBER, value_size=40)
    tf = textbox(s, M, 4.15, W - 2 * M, 0.35)
    para(tf, "FLIPPED ARTICLES: WHAT WE SAW AGAINST WHAT NOISE ALONE PREDICTS",
         size=12, bold=True, colour=MUTED, first=True, space_after=0)
    lo, hi, ax0, axw, ay = 40, 70, 2.2, 8.9, 5.2

    def at(v):
        return ax0 + (v - lo) / (hi - lo) * axw

    bar(s, ax0, ay, axw, 0.02, LINE)
    bar(s, at(44), ay - 0.16, at(67) - at(44), 0.34, MIDBLUE, 0.35)
    bar(s, at(55.3) - 0.02, ay - 0.3, 0.04, 0.62, BLUE)
    plain(s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(at(51) - 0.13),
                             Inches(ay - 0.12), Inches(0.26), Inches(0.26)),
          EMBER)
    for v in (40, 50, 60, 70):
        tf = textbox(s, at(v) - 0.4, ay + 0.3, 0.8, 0.3, align=PP_ALIGN.CENTER)
        para(tf, str(v), size=11, colour=MUTED, first=True,
             align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, at(55.3) - 2.0, ay - 0.72, 4.0, 0.4, align=PP_ALIGN.CENTER)
    para(tf, "noise predicts about 55 (shaded: 44 to 67)", size=13, bold=True,
         colour=BLUE, first=True, align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, at(51) - 1.2, ay + 0.55, 2.4, 0.4, align=PP_ALIGN.CENTER)
    para(tf, "we saw 51", size=13, bold=True, colour=EMBER, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    body(s, 8)

    # 10 honest check
    s = page(9)
    header(s, "The results", "Honest check: simple word counting sorts "
                             "articles better than our score", "warning")
    tf = textbox(s, M, 1.45, W - 2 * M, 0.5)
    rich(tf, [("AUC ", True, BLUE),
              ("= how well a score sorts manipulative from neutral articles. "
               "0.5 is a coin toss, 1.0 is perfect.", False, TEXT)], size=15,
         first=True, space_after=0)
    lo, hi, ax0, axw, ay = 0.5, 1.0, 1.4, 10.5, 3.0

    def au(v):
        return ax0 + (v - lo) / (hi - lo) * axw

    bar(s, ax0, ay, axw, 0.06, LINE)
    for v, label in [(0.5, "0.5 coin toss"), (0.75, "0.75"),
                     (1.0, "1.0 perfect")]:
        tf = textbox(s, au(v) - 0.9, ay + 0.2, 1.8, 0.3,
                     align=PP_ALIGN.CENTER)
        para(tf, label, size=11, colour=MUTED, first=True,
             align=PP_ALIGN.CENTER, space_after=0)
    for v, label, colour, above in [
            (0.5392, "sentiment tool 0.54", MUTED, False),
            (0.6274, "our score 0.63", BLUE, True),
            (0.9758, "word counting 0.98", EMBER, True)]:
        plain(s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(au(v) - 0.15),
                                 Inches(ay - 0.12), Inches(0.3), Inches(0.3)),
              colour)
        ty = ay - 0.62 if above else ay + 0.5
        tf = textbox(s, au(v) - 1.3, ty, 2.6, 0.4, align=PP_ALIGN.CENTER)
        para(tf, label, size=15, bold=True, colour=colour, first=True,
             align=PP_ALIGN.CENTER, space_after=0)
    for x, colour, head, text in [
            (M, EMBER, "WHY WORD COUNTING WINS",
             "Each group came from a different source. From the words alone, a "
             "computer guesses the source 66% of the time, against 25% by "
             "chance. So it is partly spotting the source, not the style."),
            (6.83, BLUE, "WHAT THIS MEANS FOR US",
             "We cannot say the group differences come from writing style "
             "alone. Our score is offered as a measurement for the physics "
             "model, not as a manipulation detector.")]:
        shp = card(s, x, 4.1, 5.75, 2.05, line=colour)
        tf = shp.text_frame
        tf.margin_top = Inches(0.16)
        para(tf, head, size=12, bold=True, colour=colour, first=True,
             space_after=6)
        para(tf, text, size=15, colour=TEXT, space_after=0)
    body(s, 9)

    # 11 real brains
    s = page(10)
    header(s, "The results", "Does the brain model match real brains? Weakly, "
                             "but yes", "target")
    tf = textbox(s, M, 1.45, W - 2 * M, 0.5)
    para(tf, "A company audit claimed this model is the opposite of real brains. "
             "We tested it on public brain scans of people watching the TV show "
             "Friends.", size=15, colour=MUTED, first=True, space_after=0)
    cw = 3.75
    for i, (value, name, means, why, colour) in enumerate([
            ("0.152", "Best possible score (noise ceiling)",
             "How closely real people's brains agree with each other watching "
             "the same episode.",
             "Brains differ and scanners are noisy, so even a perfect model "
             "can't score higher.", BLUE),
            ("0.028", "Model vs real brains (r), 2-minute clip",
             "The model's predictions rise and fall with real brain activity, "
             "weakly.",
             "The best possible on that same clip is 0.096, so the model gets "
             "under a third of the way.", GREEN),
            ("p = 0.048", "Chance the match is luck",
             "Just under the usual 5% cut-off.",
             "Two minutes of video is short. A longer run is needed to settle "
             "it.", GOLD)]):
        number_card(s, M + i * (cw + 0.29), 2.15, cw, 3.05, value, name, means,
                    why, colour=colour)
    shp = card(s, M, 5.45, W - 2 * M, 0.7, line=EMBER)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [("Along the way we found and fixed three hidden bugs: ", True,
               EMBER),
              ("the wrong episode loaded, a table read sideways, and two clocks "
               "out of step.", False, TEXT)], size=15, first=True,
         space_after=0)
    body(s, 10)

    # 12 the minimum push
    s = page(11)
    header(s, "The physics", "The physics result: the minimum push media "
                             "would need", "ruler")
    tf = textbox(s, M, 1.5, 6.0, 1.6)
    for i, text in enumerate([
            "Media's push  =  α  ×  our score.",
            "The data can't pin down α, so no value is quoted.",
            "So we asked: how big must α be for media alone to flip a "
            "majority?"]):
        rich(tf, [("%d   " % (i + 1), True, EMBER), (text, False, TEXT)],
             size=16, first=(i == 0), space_after=8)
    shp = card(s, M, 3.25, 6.0, 2.9, line=BLUE)
    tf = shp.text_frame
    tf.margin_top = Inches(0.16)
    rich(tf, [("α  ≥  h", True, TEXT), ("c", True, TEXT),
              ("  ÷  ΔX", True, TEXT)], size=30, first=True,
         align=PP_ALIGN.CENTER, space_after=10)
    tf.paragraphs[0].runs[1].font._rPr.set("baseline", "-25000")
    for sym, text in [
            ("h, small c", "the push needed to flip a majority, from the physics model"),
            ("ΔX = 0.124", "spread of our scores, from −0.070 to +0.054"),
            ("βJ", "how strongly people copy each other. Above 1, a group "
                   "settles on a majority by itself; 2 is strongly connected")]:
        rich(tf, [(sym + "   ", True, BLUE), (text, False, TEXT)], size=13,
             space_after=6)
    number_card(s, 7.0, 1.5, 5.58, 2.55, "α ≥ 4.29",
                "Minimum strength when copying is strong (βJ = 2)",
                "Any study saying content like this flips opinion must use an α "
                "of at least 4.29, or the maths says it can't happen.",
                "Our scores cover a narrow range (0.124), so each unit of score "
                "must push hard.", colour=EMBER, value_size=40)
    shp = card(s, 7.0, 4.3, 5.58, 1.85, line=GOLD)
    tf = shp.text_frame
    tf.margin_top = Inches(0.16)
    para(tf, "WHAT IT DOES NOT SAY", size=12, bold=True, colour=GOLD,
         first=True, space_after=6)
    para(tf, "It does not claim that media flips opinion. It is a bar any such "
             "claim has to clear. The more strongly people copy each other, the "
             "higher the bar.", size=14, colour=TEXT, space_after=0)
    body(s, 11)

    # 13 children's content
    s = page(12)
    header(s, "What's next", "Can it analyse any content, even what children "
                             "watch?", "target")
    cw = 3.75
    for i, (head, colour, icon_name, items) in enumerate([
            ("WHAT IT CAN DO", GREEN, "check-circle", [
                "Take video and sound as well as text, so a cartoon or an "
                "advert can be scored.",
                "Compare groups of content, like two channels or two kinds of "
                "programme.",
                "Score the content, never the viewer. Nobody is scanned."]),
            ("WHAT IT CANNOT DO YET", EMBER, "x-circle", [
                "Say how a child reacts. The model learned from adult brains, "
                "and children's brains are still developing.",
                "Speak for video: only news text read aloud was tested here.",
                "Rate one show: about 1 in 8 items flip between runs."]),
            ("WHAT IT WOULD TAKE", BLUE, "flag-banner", [
                "Brain scans from children, collected with ethics approval and "
                "consent.",
                "A test set of children's videos.",
                "Content where source and type are mixed.",
                "Safeguards so it is never used to target children."])]):
        x = M + i * (cw + 0.29)
        card(s, x, 1.55, cw, 4.2, line=colour)
        icon(s, icon_name, x + 0.22, 1.72, h=0.34)
        tf = textbox(s, x + 0.65, 1.7, cw - 0.8, 0.4)
        para(tf, head, size=13, bold=True, colour=colour, first=True,
             space_after=0)
        tf = textbox(s, x + 0.22, 2.25, cw - 0.4, 3.4)
        for j, text in enumerate(items):
            para(tf, "•  " + text, size=14, colour=TEXT, first=(j == 0),
                 space_after=10)
    shp = card(s, M, 5.9, W - 2 * M, 0.5, line=GOLD)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [("Short answer: ", True, GOLD),
              ("technically possible, but not yet valid for children.", False,
               TEXT)], size=15, first=True, space_after=0)
    body(s, 12)

    # 14 limits
    s = page(13)
    header(s, "What's next", "What this work cannot claim yet", "x-circle")
    cols = [(M, 4.1, "LIMIT", EMBER), (5.0, 4.0, "WHY IT MATTERS", MUTED),
            (9.15, 3.43, "NEXT STEP", BLUE)]
    for x, w, label, colour in cols:
        tf = textbox(s, x, 1.45, w, 0.35)
        para(tf, label, size=11, bold=True, colour=colour, first=True,
             space_after=0)
    rows = [
        ("Predictions, not brain scans", "Nobody was scanned; the model could "
         "be wrong.", "The real-brain check (Paper 3)."),
        ("Group is mixed up with source", "Each group came from one "
         "collection.", "A new set where every source has every type."),
        ("Brain surface only", "No amygdala or other deep areas.",
         "A model that predicts deep areas."),
        ("Strength of the push (α) unknown", "The data can't pin it down.",
         "Use the minimum rule instead."),
        ("The real-brain check is short", "Only 2 minutes of video so far.",
         "Longer clips, run one at a time."),
    ]
    for i, row in enumerate(rows):
        y = 1.85 + i * 0.83
        for j, ((x, w, _, colour), text) in enumerate(zip(cols, row)):
            shp = card(s, x, y, w, 0.72)
            tf = shp.text_frame
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            para(tf, text, size=14, bold=(j == 0),
                 colour=TEXT if j != 1 else MUTED, first=True, space_after=0)
    body(s, 13)

    # 15 papers and requests
    s = page(14)
    header(s, "What's next", "Three papers, and what I need from you today",
           "books")
    cw = 3.75
    for i, (tag, name, what, status, colour) in enumerate([
            ("PAPER 1 · Physica A", "The minimum push",
             "How strong media would have to be to flip a majority. Pure "
             "physics; needs no brain data.", "12 pages, ready", BLUE),
            ("PAPER 2 · Physica A", "The measuring tool",
             "The process, the 400 articles, the results, and the "
             "word-counting comparison.", "16 pages, ready", BLUE),
            ("PAPER 3 · Imaging Neuroscience", "Does the model match real "
             "brains?", "The best-possible score, the three bugs, and the "
             "first check.", "8 pages, one longer run to go", GOLD)]):
        x = M + i * (cw + 0.29)
        shp = card(s, x, 1.5, cw, 2.45, line=colour)
        tf = shp.text_frame
        tf.margin_top = Inches(0.16)
        para(tf, tag, size=11, bold=True, colour=colour, first=True,
             space_after=4)
        para(tf, name, size=18, bold=True, colour=TEXT, space_after=6)
        para(tf, what, size=13, colour=MUTED, space_after=6)
        para(tf, status, size=13, bold=True, colour=colour, space_after=0)
    shp = card(s, M, 4.2, W - 2 * M, 1.95, line=EMBER)
    tf = shp.text_frame
    tf.margin_top = Inches(0.16)
    para(tf, "TODAY I AM ASKING FOR", size=12, bold=True, colour=EMBER,
         first=True, space_after=8)
    for i, text in enumerate([
            "Any corrections you need before the thesis is final.",
            "Your signature on the declaration page (page iii).",
            "Clearance to deposit with the library (bound copy by Thursday "
            "24 September).",
            "Your view on co-authorship of the three papers."]):
        rich(tf, [("%d   " % (i + 1), True, EMBER), (text, False, TEXT)],
             size=15, space_after=3)
    body(s, 14)

    out = os.path.join(HERE, "Monarch_Supervisor_Deck.pptx")
    prs.save(out)
    return out, len(prs.slides)


def build_presenter():
    prs = new_deck()

    s = slide(prs)
    tf = textbox(s, M, 0.5, W - 2 * M, 0.4)
    para(tf, "PRESENTER SCRIPT  ·  FOR BRIAN ONLY", size=13, bold=True,
         colour=EMBER, first=True, space_after=0)
    tf = textbox(s, M, 0.9, W - 2 * M, 0.9)
    para(tf, "Meeting with Dr. Songa, 21 September 2026", size=30, bold=True,
         colour=BLUE, first=True, space_after=0)
    tf = textbox(s, M, 1.65, W - 2 * M, 0.5)
    para(tf, "One card per slide. Read the script in your own words; the right "
             "column is the numbers to say out loud. Likely questions and a "
             "plain-words sheet follow.", size=15, colour=MUTED, first=True,
         space_after=0)
    minutes = [1, 1, 1.5, 1, 1, 1, 1, 1, 1, 1.5, 1, 1, 1, 0.5, 1.5]
    for i, ((title, section, _, _), mins) in enumerate(zip(SCRIPT, minutes)):
        col, row = divmod(i, 8)
        x = M + col * 6.0
        y = 2.4 + row * 0.5
        shp = card(s, x, y, 5.7, 0.42)
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        rich(tf, [("%02d   " % (i + 1), True, EMBER), (title, True, TEXT),
                  ("   %s min" % ("%g" % mins), False, MUTED)], size=13,
             first=True, space_after=0)
    tf = textbox(s, 6.75, 6.05, 5.8, 0.4)
    para(tf, "Total about %g minutes" % sum(minutes), size=14, bold=True,
         colour=GOLD, first=True, space_after=0)

    for i, (title, section, script, cues) in enumerate(SCRIPT):
        s = slide(prs)
        tf = textbox(s, M, 0.3, W - 2 * M, 0.35)
        para(tf, "SLIDE %02d%s" % (i + 1, "  ·  " + section.upper()
                                   if section else ""),
             size=12, bold=True, colour=EMBER, first=True, space_after=0)
        tf = textbox(s, M, 0.62, W - 2 * M, 0.7)
        para(tf, title, size=28, bold=True, colour=BLUE, first=True,
             space_after=0)
        shp = card(s, M, 1.45, 8.1, 5.1, line=BLUE)
        tf = shp.text_frame
        tf.margin_left = tf.margin_right = Inches(0.35)
        tf.margin_top = Inches(0.3)
        para(tf, "SAY", size=11, bold=True, colour=MUTED, first=True,
             space_after=8)
        para(tf, script, size=19, colour=TEXT, space_after=0)
        shp = card(s, 9.1, 1.45, 3.48, 5.1, line=GOLD)
        tf = shp.text_frame
        tf.margin_top = Inches(0.3)
        para(tf, "NUMBERS TO SAY", size=11, bold=True, colour=GOLD, first=True,
             space_after=10)
        for cue in cues:
            para(tf, "•  " + cue, size=15, colour=TEXT, space_after=10)
        s.notes_slide.notes_text_frame.text = script

    for start in range(0, len(QUESTIONS), 2):
        s = slide(prs)
        tf = textbox(s, M, 0.3, W - 2 * M, 0.35)
        para(tf, "LIKELY QUESTIONS  %d of %d" % (start // 2 + 1,
                                                (len(QUESTIONS) + 1) // 2),
             size=12, bold=True, colour=EMBER, first=True, space_after=0)
        tf = textbox(s, M, 0.62, W - 2 * M, 0.7)
        para(tf, "Many of these grow out of the first presentation's question "
                 "about children's content", size=22, bold=True, colour=BLUE,
             first=True, space_after=0)
        for j, (q, a) in enumerate(QUESTIONS[start:start + 2]):
            y = 1.55 + j * 2.55
            shp = card(s, M, y, W - 2 * M, 2.35, line=GOLD if j == 0 else BLUE)
            tf = shp.text_frame
            tf.margin_left = tf.margin_right = Inches(0.35)
            tf.margin_top = Inches(0.22)
            rich(tf, [("Q%d   " % (start + j + 1), True, EMBER),
                      (q, True, TEXT)], size=20, first=True, space_after=10)
            rich(tf, [("A   ", True, GREEN), (a, False, TEXT)], size=17,
                 space_after=0)

    s = slide(prs)
    tf = textbox(s, M, 0.3, W - 2 * M, 0.35)
    para(tf, "PLAIN WORDS FOR EVERY NUMBER", size=12, bold=True, colour=EMBER,
         first=True, space_after=0)
    tf = textbox(s, M, 0.62, W - 2 * M, 0.7)
    para(tf, "If a symbol comes up, say it like this", size=26, bold=True,
         colour=BLUE, first=True, space_after=0)
    for i, (term, meaning) in enumerate(GLOSSARY):
        col, row = divmod(i, 6)
        x = M + col * 6.0
        y = 1.45 + row * 0.85
        shp = card(s, x, y, 5.8, 0.75)
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        rich(tf, [(term + "   ", True, GOLD), (meaning, False, TEXT)], size=13,
             first=True, space_after=0)

    out = os.path.join(HERE, "Monarch_Presenter_Script.pptx")
    prs.save(out)
    return out, len(prs.slides)


if __name__ == "__main__":
    for path, count in (build_supervisor(), build_presenter()):
        print("wrote", path, count, "slides")
