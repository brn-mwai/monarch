"""Build the supervisor deck twice from one source.

Monarch_Supervisor_Deck.pptx         15 slides, no speaker notes.
Monarch_Supervisor_Deck_Script.pptx  the same 15 slides; each slide's speaker
                                     notes hold the script, the numbers to say
                                     and the questions likely on that slide.
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

from deck_theme import (BLUE, EMBER, FIG, GOLD, GREEN, HERE, LINE, M, MIDBLUE,
                        MUTED, TEXT, W, arrow, bar, card, figure,
                        footer, header, icon, lattice, math, new_deck,
                        para, plain, rich, scale_bars, slide, textbox)

SECTIONS = ["The idea", "The method", "The results", "The physics",
            "What's next"]
DELTA_X = 0.1241

SLIDES = [
    ("Title", None, 1,
     "Good morning, Dr. Songa, and thank you for the time. I'll go through what "
     "I set out to do, how I did it, what I found, what the work cannot claim, "
     "where it can go next, and the three papers. About fifteen minutes, and I'll "
     "end with what I need from you.",
     ["About 15 minutes", "End with the four requests"], []),
    ("The idea", "The idea", 1,
     "Physicists model a group forming an opinion the same way they model tiny "
     "magnets lining up. The equation is m equals tanh of beta J m plus h. m is "
     "the group's average opinion, from minus one, everyone against, to plus "
     "one, everyone for. J is how strongly each person is pulled toward the "
     "people around them. Beta is how firmly they follow that pull instead of "
     "acting at random. And h is the push from media, the same on everyone. In "
     "every study I read, h is chosen by hand. My question: can we measure h "
     "from the content itself?",
     ["m: average opinion, -1 to +1", "J: pull toward neighbours",
      "beta: how firmly people follow the pull", "h: media's push"], []),
    ("Plan vs reality", "The idea", 1.5,
     "Before the results, here is what changed from the proposal once we tested "
     "the tools. Five things. We planned to measure the amygdala, but the model "
     "only sees the brain's surface. The ratio score broke, so we used a "
     "difference. Outrage didn't stand out; fear did. We couldn't measure alpha, "
     "so we derived the minimum instead. And the score turned out to be a "
     "measurement, not a detector. All of this is in the amendment you approved.",
     ["5 changes, all in the approved amendment", "Ratio broke on 69 of 400"],
     [7]),
    ("Tools and process", "The method", 1.5,
     "This is how one article becomes one number. The article is read aloud by "
     "a text-to-speech voice, because the brain model was built on people "
     "listening. A timing tool marks when each word is said. Then TRIBE v2, a "
     "model from Meta's research lab trained on brain scans of adult volunteers "
     "watching TV, predicts activity at 20,484 points on the brain's surface. A "
     "standard brain map picks 1,030 points linked to emotion and 851 linked to "
     "reasoning. The score X is the emotion average minus the reasoning average. "
     "Nobody was scanned: every value is a prediction.",
     ["20,484 points on the brain surface", "1,030 emotion, 851 reasoning",
      "About 70 seconds per article on a free Kaggle GPU"], [3, 6, 12]),
    ("The articles", "The method", 1,
     "We scored 400 articles from four public collections, 100 each: fear-driven "
     "fake news, outrage-style partisan news, clickbait, and neutral writing. "
     "Lengths are matched so no group wins by being longer. We worked out before "
     "scanning that 400 could detect an effect as small as 0.027, and we scanned "
     "every article twice.",
     ["4 groups x 100", "About 164 words each", "Smallest detectable 0.027",
      "Scanned twice"], [11]),
    ("Result 1", "The results", 1,
     "First result: the groups really differ. The measure is eta squared, 0.107. "
     "The ring shows what that means: about 11 percent of the differences "
     "between articles come from which group they are in, and the rest is "
     "article to article. The chance this is luck is about one in a billion, and "
     "the second run gave 0.089, both far above the 0.027 we could detect.",
     ["0.107 = 11% explained by group", "p about 1 in a billion",
      "Second run 0.089"], []),
    ("Result 2", "The results", 1,
     "Which group drives it? Fear. Measured against neutral articles, fear sits "
     "0.94 spreads away, which is large. Clickbait is small and outrage is almost "
     "zero. The two small charts show why. Fear raises the emotion areas and "
     "leaves reasoning flat, so the gap, our score, moves. Outrage raises both "
     "by the same amount, so the gap stays flat. The proposal expected outrage to "
     "be strongest, and this is why it isn't.",
     ["Fear 0.94 large, clickbait 0.32 small, outrage 0.03",
      "Outrage: emotion +0.51, reasoning +0.49",
      "Fear: emotion +0.61, reasoning -0.10"], []),
    ("Result 3", "The results", 1,
     "Can we trust the score? Running all 400 articles twice gives agreement of "
     "0.87, where 1 means identical. That is high. 51 articles flipped sign "
     "between runs, but noise alone predicts about 55, and they all sit near "
     "zero where a tiny wobble tips them. So group averages are trustworthy, and "
     "we never judge a single article.",
     ["Agreement 0.87 (1 = identical)", "51 flipped, 55 expected (44 to 67)"],
     []),
    ("Honest check", "The results", 1.5,
     "The most important honest check. Plain word counting sorts manipulative "
     "from neutral articles far better than our score: 0.98 against 0.63, where "
     "0.5 is a coin toss. That's because each group came from a different "
     "source, and the words give the source away. So we cannot say the "
     "difference comes from writing style alone. Our score is a measurement for "
     "the physics, not a manipulation detector.",
     ["Word counting 0.98, ours 0.63, sentiment tool 0.54",
      "Words guess the source 66% vs 25% chance"], [5]),
    ("Real brains", "The results", 1,
     "Does the brain model match real brains? A company audit claimed it was "
     "the opposite, so we tested it on public brain scans of people watching "
     "Friends. Real people agree with each other at 0.152 over the episode; "
     "that's the ceiling. On a two-minute clip, the best possible is 0.096 and "
     "the model reaches 0.028, about 30 percent of the way, with p of 0.048. "
     "Weak but positive. We also found and fixed three hidden bugs. This is "
     "Paper 3.",
     ["Ceiling 0.152 (full episode)", "Clip: model 0.028 vs best 0.096",
      "p = 0.048", "3 bugs fixed"], []),
    ("The minimum push", "The physics", 1.5,
     "The physics result. We link our score to the model with h equals alpha X: "
     "the push is the score times a strength, alpha. We couldn't measure alpha, "
     "so we asked how big it must be to flip a majority. The model gives h c, "
     "the smallest push that flips it, which grows with the copying strength "
     "beta J. Dividing by the spread of our scores, delta X of 0.124, gives the "
     "curve. At beta J of 2, alpha must be at least 4.29. It is a bar any future "
     "claim must clear, not a claim that media flips opinion.",
     ["h = alpha X", "Delta X = 0.124 (-0.070 to +0.054)",
      "alpha >= 4.29 at beta J = 2"], [9, 10]),
    ("Children's content", "What's next", 1,
     "At my first presentation I was asked whether this could analyse any "
     "content, even what children watch. Technically yes: it takes video and "
     "audio, so it could score a cartoon. But the model learned from adult "
     "brains, so it can't say how a child reacts. We only tested news text, and "
     "one show on its own isn't reliable. For children we'd need child brain "
     "data and ethics approval first.",
     ["Adult-trained model", "1 in 8 items flip between runs"], [1, 2, 8]),
    ("Limits", "What's next", 0.5,
     "Every limit here points to the next study. Predictions need checking "
     "against more real brain data. Group and source need separating with a new "
     "set of articles. Deep brain areas need a model that predicts them. Alpha "
     "needs real opinion data. And the brain check needs longer clips.",
     ["5 limits, each stated in the thesis"], []),
    ("Taking it further", "What's next", 1,
     "Where this can go. First, publishing the three papers, with preprints "
     "first. Second, extending the science: the Kenyan case study from the "
     "proposal, coverage of the 2024 Finance Bill; video and audio content; "
     "measuring alpha against real opinion data; and children's media once the "
     "data and ethics allow. Third, opportunities: this is a natural "
     "postgraduate topic, it invites collaboration with neuroscience and media "
     "researchers, and the tool is already public online.",
     ["Kenya 2024 Finance Bill case", "Tool live: monarch-4iy.pages.dev"],
     [4]),
    ("Papers and requests", "What's next", 1.5,
     "Three papers come out of this. Paper 1 is pure physics, the minimum-push "
     "rule. Paper 2 is the measuring tool and the 400 articles, including the "
     "word-counting comparison. Paper 3 is the check against real brains. The "
     "dissertation comes first. I'm asking for any corrections, your signature "
     "on the declaration page, clearance for the library by Thursday, and your "
     "view on co-authorship.",
     ["Bound copy by Thu 24 Sep", "Clearance by Mon 28 Sep"], []),
]

QUESTIONS = [
    ("Can this analyse any content, even what children watch?",
     "Technically it can score video and audio. But the model learned from "
     "adult brains, so it can't say how a child reacts, and we only tested news "
     "text. It would need child brain data and ethics approval first."),
    ("Could a parent or a regulator use it to rate one show?",
     "Not yet. About 1 in 8 items flip between runs, so single scores aren't "
     "reliable. It is only trustworthy for comparing groups of content."),
    ("Was anyone scanned? Is it reading minds?",
     "No. Nobody was scanned. The scores are predictions of a typical adult "
     "brain. The tool rates content, not people."),
    ("Could someone use it to make content more manipulative?",
     "It's a real risk for any content measure. That's why it reports group "
     "results only, for research, and the model's licence is non-commercial."),
    ("If word counting does better, why not use that?",
     "Word counting mostly learns the source. Our score is meant to be the "
     "push h in the opinion model. The comparison is there to be honest."),
    ("Why read the articles aloud?",
     "The model was trained on people watching and listening, so it expects "
     "speech with word timings."),
    ("Why no amygdala?",
     "The released model only predicts the brain's surface. The amygdala is "
     "deep inside, so we make no claim about it."),
    ("What would it take for children's media?",
     "Child brain scans with ethics approval and consent, a children's video "
     "test set, and content where source and type are mixed."),
    ("Why is this physics?",
     "The opinion model is statistical physics, the maths of magnets lining "
     "up. The contribution is measuring the push and deriving its minimum."),
    ("What does alpha >= 4.29 mean in practice?",
     "It's a bar. Any claim that such content flips a strongly connected "
     "group must use alpha of at least 4.29, or the model says it can't."),
    ("Why only 400 articles?",
     "We calculated before scanning that 400 detects an effect of 0.027. Each "
     "article costs about a minute of GPU time, and we ran them twice."),
    ("Is it okay to use Meta's model?",
     "Yes, for research. It's under a non-commercial licence, cited throughout, "
     "and this project makes no money from it."),
]


def notes_for(index):
    title, _, minutes, script, cues, questions = SLIDES[index]
    lines = ["SCRIPT (about %g min)" % minutes, script, "", "NUMBERS TO SAY"]
    lines += ["- " + cue for cue in cues]
    if questions:
        lines += ["", "IF ASKED"]
        for q in questions:
            question, answer = QUESTIONS[q - 1]
            lines += ["Q: " + question, "A: " + answer, ""]
    return "\n".join(lines).rstrip()


def banner(s, y, lead, text, colour=GOLD, h=0.62):
    shp = card(s, M, y, W - 2 * M, h, line=colour)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [(lead + "  ", True, colour), (text, False, TEXT)], size=16,
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


def stat(s, x, y, w, h, value, label, colour=BLUE, size=36, line=None):
    shp = card(s, x, y, w, h, line=line or colour)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, value, size=size, bold=True, colour=colour, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    para(tf, label, size=13, colour=TEXT, align=PP_ALIGN.CENTER,
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

    # 2 the idea
    s = page(1)
    header(s, "The idea", "Physics treats media as a push, h, on opinion. "
                          "Nobody measures h", "waveform")
    math(s, r"m = \tanh(\beta J\, m + h)", M, 1.65, size=36)
    for i, (sym, text, colour) in enumerate([
            ("m", "average opinion\n−1 all against · +1 all for", BLUE),
            ("J", "pull toward\nthe people around you", BLUE),
            (r"\beta", "how firmly people\nfollow that pull", BLUE),
            ("h", "media's push,\nthe same on everyone", GOLD)]):
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
            ("Measure the amygdala", "Model sees brain surface only, so we "
                                     "used surface areas"),
            ("Score as a ratio", "Ratio broke on 69 of 400, so we used a "
                                 "difference"),
            ("Outrage stands out most", "Fear stands out; outrage lifts both "
                                        "areas equally"),
            ("Measure α, media's strength", "Data can't pin α, so we derived "
                                            "its minimum"),
            ("A manipulation detector", "Word counting wins, so it's a "
                                        "measurement")]):
        y = 1.8 + i * 0.86
        chip(s, M, y, 4.1, 0.72, planned, colour=MUTED, icon_name="x-circle")
        arrow(s, 4.95, y + 0.29, 0.5, 0.16, EMBER)
        chip(s, 5.55, y, 7.03, 0.72, found, line=BLUE, icon_name="check-circle")
    tf = textbox(s, M, 6.15, W - 2 * M, 0.35)
    para(tf, "All five are in the approved amendment.", size=13, colour=MUTED,
         first=True, space_after=0)
    done(s, 2)

    # 4 tools and process
    s = page(3)
    header(s, "The method", "How one article becomes one number", "brain")
    steps = [("newspaper", "Article", "400 news texts"),
             ("waveform", "Read aloud", "text-to-speech"),
             ("text-aa", "Word timings", "timing tool"),
             ("brain", "TRIBE v2", "Meta, 2025"),
             ("target", "Brain map", "Glasser, 2016")]
    sw, gap = 2.12, 0.31
    for i, (icon_name, head, tool) in enumerate(steps):
        x = M + i * (sw + gap)
        card(s, x, 1.45, sw, 1.5, line=BLUE if i == 3 else LINE)
        icon(s, icon_name, x + sw / 2 - 0.22, 1.6, h=0.44)
        tf = textbox(s, x, 2.1, sw, 0.8, align=PP_ALIGN.CENTER)
        para(tf, head, size=15, bold=True, colour=TEXT, first=True,
             space_after=0)
        para(tf, tool, size=12, colour=MUTED, space_after=0)
        if i < len(steps) - 1:
            arrow(s, x + sw + 0.05, 2.12, gap - 0.1, 0.16)
    figure(s, os.path.join(FIG, "B1_roi_definition.png"), M + 0.12, 3.35,
           w=5.6)
    tf = textbox(s, M, 5.95, 6, 0.35)
    rich(tf, [("orange ", True, EMBER), ("1,030 emotion points   ", False, TEXT),
              ("blue ", True, BLUE), ("851 reasoning points", False, TEXT)],
         size=13, first=True, space_after=0)
    card(s, 7.05, 3.25, 5.53, 2.05, line=BLUE)
    tf = textbox(s, 7.25, 3.35, 5, 0.3)
    para(tf, "THE SCORE", size=11, bold=True, colour=MUTED, first=True,
         space_after=0)
    math(s, r"X = \bar{A}_{\mathrm{emotion}} - \bar{A}_{\mathrm{reasoning}}",
         7.05, 3.7, size=24, centre_w=5.53)
    bar(s, 7.35, 4.75, 2.45, 0.1, BLUE)
    bar(s, 9.83, 4.75, 2.45, 0.1, EMBER)
    bar(s, 9.8, 4.62, 0.03, 0.36, TEXT)
    for x, text, colour, al in [(7.35, "reasoning leads", BLUE, PP_ALIGN.LEFT),
                                (9.83, "emotion leads", EMBER, PP_ALIGN.RIGHT)]:
        tf = textbox(s, x, 4.9, 2.45, 0.3, align=al)
        para(tf, text, size=12, bold=True, colour=colour, first=True,
             space_after=0)
    tf = textbox(s, 9.5, 4.9, 0.6, 0.3, align=PP_ALIGN.CENTER)
    para(tf, "0", size=12, colour=TEXT, first=True, space_after=0)
    chip(s, 7.05, 5.5, 5.53, 0.62, "Nobody scanned: every value is predicted",
         colour=EMBER, line=EMBER, size=14, bold=True, icon_name="warning")
    done(s, 3)

    # 5 the articles
    s = page(4)
    header(s, "The method", "400 articles, four groups, matched in length",
           "newspaper")
    for i, (name, src, colour) in enumerate([
            ("Fear-driven", "fake news (ISOT)", EMBER),
            ("Outrage", "partisan news (SemEval)", GOLD),
            ("Clickbait", "headlines (Webis)", MIDBLUE),
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
            ("≈ 164", "words per article,\nall groups within 5 words", BLUE),
            ("0.027", "smallest effect we\ncould detect, set in advance", GREEN),
            ("× 2", "every article\nscanned twice", GOLD)]):
        stat(s, M + i * (3.75 + 0.29), 3.8, 3.75, 1.75, value, label,
             colour=colour, size=40)
    done(s, 4)

    # 6 result 1
    s = page(5)
    header(s, "The results", "Result 1: the four groups really differ",
           "chart-bar")
    donut(s, M, 1.45, 3.7, 0.1068, BLUE)
    tf = textbox(s, M, 2.8, 3.7, 1.0, align=PP_ALIGN.CENTER)
    para(tf, "11%", size=44, bold=True, colour=TEXT, first=True,
         space_after=0)
    tf = textbox(s, M, 5.15, 3.7, 0.9, align=PP_ALIGN.CENTER)
    rich(tf, [("11% ", True, BLUE),
              ("of the differences between articles comes from their group",
               False, TEXT)], size=14, first=True, space_after=0)
    math(s, r"\eta^2 = \frac{\mathrm{between\ groups}}{\mathrm{total}} "
            r"= 0.107", 4.75, 1.6, size=22)
    tf = textbox(s, 4.75, 2.55, 7.8, 0.3)
    para(tf, "η² ON EACH RUN, AGAINST THE SMALLEST WE COULD DETECT", size=11,
         bold=True, colour=MUTED, first=True, space_after=0)
    scale_bars(s, [("first run", 0.1068, "0.107", BLUE),
                   ("second run", 0.0888, "0.089", MIDBLUE),
                   ("detectable", 0.0268, "0.027", MUTED)],
               top=3.0, maximum=0.12, left=6.35, length=4.6, label_w=1.45,
               step=0.55, size=14)
    stat(s, 4.75, 4.75, 3.8, 1.3, "1 in a billion", "chance it is luck "
         "(p = 1×10⁻⁹)", colour=GREEN, size=26)
    stat(s, 8.78, 4.75, 3.8, 1.3, "Repeats", "second run agrees (0.089)",
         colour=MIDBLUE, size=26)
    banner(s, 6.25, "Meaning:", "the groups differ for real, but most "
           "variation is from one article to the next.", h=0.5)
    done(s, 5)

    # 7 result 2
    s = page(6)
    header(s, "The results", "Result 2: fear drives it; outrage lifts both "
                             "sides equally", "chart-bar")
    math(s, r"d = \frac{\bar{X}_{\mathrm{group}} - \bar{X}_{\mathrm{neutral}}}"
            r"{s}", M, 1.45, size=20)
    tf = textbox(s, 3.9, 1.55, 5, 0.5)
    para(tf, "distance from neutral, in spreads (s)", size=12, colour=MUTED,
         first=True, space_after=0)
    left, length = 2.9, 6.6
    for mark, label in [(0.2, "small"), (0.5, "medium"), (0.8, "large")]:
        xm = left + length * mark
        bar(s, xm, 2.3, 0.015, 1.7, LINE)
        tf = textbox(s, xm - 0.6, 2.08, 1.2, 0.25, align=PP_ALIGN.CENTER)
        para(tf, label, size=11, colour=MUTED, first=True, space_after=0)
    scale_bars(s, [("fear-driven", 0.939, "0.94", EMBER),
                   ("clickbait", 0.319, "0.32", MIDBLUE),
                   ("outrage", 0.030, "0.03", GOLD)],
               top=2.45, maximum=1.0, left=left, length=length, label_w=2.0,
               step=0.55)
    for x, name, emo, rea, verdict, colour in [
            (M, "FEAR", 0.613, -0.098, "big gap: score moves", EMBER),
            (6.83, "OUTRAGE", 0.507, 0.491, "no gap: score stays flat", GOLD)]:
        card(s, x, 4.2, 5.75, 2.0, line=colour)
        tf = textbox(s, x + 3.0, 4.45, 2.6, 0.3)
        para(tf, name, size=13, bold=True, colour=colour, first=True,
             space_after=0)
        base = 5.55
        bar(s, x + 0.3, base, 2.4, 0.02, MUTED)
        for j, (val, c, lab) in enumerate([(emo, EMBER, "emotion"),
                                           (rea, BLUE, "reasoning")]):
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
        tf = textbox(s, x + 3.0, 4.85, 2.6, 1.1, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, verdict, size=17, bold=True, colour=colour, first=True,
             space_after=0)
    done(s, 6)

    # 8 result 3
    s = page(7)
    header(s, "The results", "Result 3: scores repeat for groups, not single "
                             "articles", "arrows-clockwise")
    card(s, M, 1.5, 5.75, 3.4, line=BLUE)
    tf = textbox(s, M, 1.65, 5.75, 1.2, align=PP_ALIGN.CENTER)
    para(tf, "0.87", size=54, bold=True, colour=BLUE, first=True,
         space_after=0)
    para(tf, "agreement between two runs (ICC)", size=14, colour=TEXT,
         space_after=0)
    bar(s, M + 0.4, 3.5, 4.95, 0.3, LINE)
    bar(s, M + 0.4, 3.5, 4.95 * 0.8725, 0.3, BLUE)
    for v, label in [(0, "0 none"), (1, "1 identical")]:
        tf = textbox(s, M + 0.4 + 4.95 * v - 0.7, 3.9, 1.4, 0.3,
                     align=PP_ALIGN.CENTER)
        para(tf, label, size=12, colour=MUTED, first=True, space_after=0)
    card(s, 6.83, 1.5, 5.75, 3.4, line=EMBER)
    tf = textbox(s, 6.83, 1.65, 5.75, 1.2, align=PP_ALIGN.CENTER)
    para(tf, "51 of 400", size=54, bold=True, colour=EMBER, first=True,
         space_after=0)
    para(tf, "flipped sign between runs", size=14, colour=TEXT,
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
    rich(tf, [("● saw 51   ", True, EMBER),
              ("▌noise predicts 55 (shaded 44 to 67)", True, BLUE)], size=12,
         first=True, space_after=0)
    banner(s, 5.2, "Meaning:", "trust group averages. Never judge one "
           "article: its score sits near zero and noise can tip it.")
    done(s, 7)

    # 9 honest check
    s = page(8)
    header(s, "The results", "Honest check: word counting beats our score",
           "warning")
    tf = textbox(s, M, 1.45, W - 2 * M, 0.35)
    rich(tf, [("How well each method sorts manipulative from neutral "
               "articles (AUC)", False, MUTED)], size=13, first=True,
         space_after=0)
    lo, hi, ax0, axw, ay = 0.5, 1.0, 1.3, 10.7, 2.75

    def au(v):
        return ax0 + (v - lo) / (hi - lo) * axw

    bar(s, ax0, ay, axw, 0.06, LINE)
    for v, label in [(0.5, "0.5 coin toss"), (1.0, "1.0 perfect")]:
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
                                    ("clickbait", "Webis"),
                                    ("neutral", "PubMed + ISOT")]):
        y = 4.0 + i * 0.5
        chip(s, M, y, 2.1, 0.42, grp, size=13, align=PP_ALIGN.CENTER)
        arrow(s, 2.95, y + 0.14, 0.5, 0.14, EMBER)
        chip(s, 3.55, y, 2.5, 0.42, src, size=13, align=PP_ALIGN.CENTER)
    stat(s, 6.6, 3.7, 2.8, 1.85, "66%", "words guess the source\n(chance: 25%)",
         colour=EMBER, size=36)
    card(s, 9.6, 3.7, 2.98, 1.85, line=BLUE)
    tf = textbox(s, 9.75, 3.8, 2.7, 1.7, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, "So our score is a measurement for the physics, not a detector.",
         size=15, bold=True, colour=BLUE, first=True, space_after=0)
    done(s, 8)

    # 10 real brains
    s = page(9)
    header(s, "The results", "Does the brain model match real brains? "
                             "Weakly, yes", "target")
    tf = textbox(s, M, 1.45, W - 2 * M, 0.35)
    para(tf, "Tested on public brain scans of people watching Friends "
             "(Algonauts 2025). Higher = closer match (r).", size=13,
         colour=MUTED, first=True, space_after=0)
    scale_bars(s, [("people vs each other,\nfull episode", 0.1517, "0.152",
                    MUTED),
                   ("best possible,\n2-minute clip", 0.0959, "0.096", BLUE),
                   ("our model,\n2-minute clip", 0.0283, "0.028", GREEN)],
               top=2.1, maximum=0.17, left=3.6, length=6.8, label_w=2.6,
               step=0.8, size=14)
    stat(s, M, 4.65, 3.75, 1.35, "≈ 30%", "of the best possible on the clip",
         colour=GREEN, size=30)
    stat(s, 4.79, 4.65, 3.75, 1.35, "p = 0.048", "just under the 5% cut-off",
         colour=GOLD, size=30)
    stat(s, 8.83, 4.65, 3.75, 1.35, "3 bugs", "found and fixed along the way",
         colour=EMBER, size=30)
    banner(s, 6.2, "Meaning:", "weak but positive, not the opposite of real "
           "brains. A longer run will settle it (Paper 3).", h=0.5)
    done(s, 9)

    # 11 the minimum push
    s = page(10)
    header(s, "The physics", "The minimum push media would need", "ruler")
    card(s, M, 1.45, 5.7, 4.75, line=BLUE)
    math(s, r"h = \alpha X \;\Rightarrow\; \alpha \geq "
            r"\frac{h_c(\beta J)}{\Delta X}", M, 1.65, size=28, centre_w=5.7)
    for i, (sym, text) in enumerate([
            (r"\alpha", "strength of the push per unit of score"),
            (r"h_c", "smallest push that flips the majority"),
            (r"\beta J", "how strongly people copy each other"),
            (r"\Delta X", "spread of our scores = 0.124")]):
        y = 2.95 + i * 0.75
        math(s, sym, M + 0.2, y + 0.05, size=22, colour=GOLD, centre_w=1.0)
        tf = textbox(s, M + 1.35, y, 4.2, 0.6, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, text, size=15, colour=TEXT, first=True, space_after=0)
    alpha_curve(s, 6.75, 1.4, 5.9, 3.7)
    tf = textbox(s, 6.75, 5.0, 5.9, 0.3, align=PP_ALIGN.CENTER)
    para(tf, "copying strength βJ  →", size=12, colour=MUTED, first=True,
         space_after=0)
    tf = textbox(s, 6.95, 1.35, 3, 0.3)
    para(tf, "α required", size=12, colour=MUTED, first=True, space_after=0)
    stat(s, 6.75, 5.35, 5.83, 0.85, "α ≥ 4.29 at βJ = 2",
         "a bar any claim must clear", colour=EMBER, size=22)
    done(s, 10)

    # 12 children's content
    s = page(11)
    header(s, "What's next", "Can it analyse any content, even what children "
                             "watch?", "target")
    for i, (head, colour, icon_name, items) in enumerate([
            ("CAN DO", GREEN, "check-circle",
             ["Score video, audio and text", "Compare groups of content",
              "Rate content, never the viewer"]),
            ("NOT YET", EMBER, "x-circle",
             ["Model learned from adult brains", "Only news text was tested",
              "One show alone is unreliable"]),
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
    done(s, 11)

    # 13 limits
    s = page(12)
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
            ("Brain check is 2 minutes", "Longer clips, one run each")]):
        y = 1.8 + i * 0.86
        chip(s, M, y, 4.85, 0.72, limit, line=EMBER, bold=True)
        arrow(s, 5.65, y + 0.29, 0.45, 0.16, GREEN)
        chip(s, 6.2, y, 6.38, 0.72, nxt, line=GREEN)
    done(s, 12)

    # 14 taking it further
    s = page(13)
    header(s, "What's next", "Taking it further: where this research can go",
           "flag-banner")
    for i, (head, colour, icon_name, items) in enumerate([
            ("PUBLISH", BLUE, "books",
             ["Paper 1 → Physica A", "Paper 2 → Physica A",
              "Paper 3 → Imaging Neuroscience", "Preprints first (arXiv)"]),
            ("EXTEND THE SCIENCE", GREEN, "atom",
             ["Kenya: 2024 Finance Bill coverage", "Video and audio content",
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
    tf = textbox(s, M, 6.15, W - 2 * M, 0.35)
    para(tf, "Live instrument: monarch-4iy.pages.dev   ·   Code and data: "
             "github.com/brn-mwai/monarch", size=12, colour=MUTED, first=True,
         space_after=0)
    done(s, 13)

    # 15 papers and requests
    s = page(14)
    header(s, "What's next", "Three papers, and what I need from you today",
           "books")
    for i, (tag, name, status, colour) in enumerate([
            ("PAPER 1 · Physica A", "The minimum push", "12 pp · ready", BLUE),
            ("PAPER 2 · Physica A", "The measuring tool", "16 pp · ready",
             BLUE),
            ("PAPER 3 · Imaging Neurosci.", "Matching real brains",
             "8 pp · one longer run", GOLD)]):
        x = M + i * (3.75 + 0.29)
        card(s, x, 1.5, 3.75, 1.7, line=colour)
        tf = textbox(s, x + 0.2, 1.62, 3.4, 1.5)
        para(tf, tag, size=11, bold=True, colour=colour, first=True,
             space_after=4)
        para(tf, name, size=19, bold=True, colour=TEXT, space_after=4)
        para(tf, status, size=13, colour=MUTED, space_after=0)
    tf = textbox(s, M, 3.5, 6, 0.3)
    para(tf, "TODAY I AM ASKING FOR", size=12, bold=True, colour=EMBER,
         first=True, space_after=0)
    for i, (icon_name, text) in enumerate([
            ("magnifying-glass", "Any corrections"),
            ("check-circle", "Signature, page iii"),
            ("books", "Library clearance by Thu 24"),
            ("flag-banner", "Co-authorship view")]):
        x = M + i * (2.72 + 0.317)
        card(s, x, 3.9, 2.72, 1.7, line=EMBER)
        icon(s, icon_name, x + 2.72 / 2 - 0.25, 4.1, h=0.5)
        tf = textbox(s, x + 0.1, 4.75, 2.52, 0.8, align=PP_ALIGN.CENTER)
        rich(tf, [("%d  " % (i + 1), True, EMBER), (text, True, TEXT)],
             size=15, first=True, space_after=0)
    done(s, 14)

    name = "Monarch_Supervisor_Deck_Script.pptx" if with_notes \
        else "Monarch_Supervisor_Deck.pptx"
    out = os.path.join(HERE, name)
    prs.save(out)
    return out, len(prs.slides)


if __name__ == "__main__":
    for path, count in (build_deck(False), build_deck(True)):
        print("wrote", path, count, "slides")
