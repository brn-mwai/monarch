"""Build the Monarch defence deck as an editable .pptx.

Diagrams are native shapes rather than images so the presenter can move or retype
anything on the day. Figures that come from the analysis stay as images, because
they are evidence and must not be redrawn by hand.
"""

import os
import random

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ICON_SRC = os.path.join(HERE, "assets", "icons")
ICONS = os.path.join(HERE, "assets", "icons_dark")
REPO = r"C:\Users\Windows\Downloads\monarch"
FIG = os.path.join(REPO, "services", "inference", "data", "figures")
REPORT = os.path.join(REPO, "services", "inference", "data", "final", "report")
PAPER1 = os.path.join(REPO, "services", "inference", "data", "paper1")
OUT = os.path.join(REPO, "docs", "defence", "Monarch_Defence.pptx")

BG = RGBColor(0x0A, 0x16, 0x28)
SURFACE = RGBColor(0x12, 0x22, 0x3C)
GHOST = RGBColor(0x17, 0x2A, 0x4A)
NAVY = RGBColor(0x7C, 0xC4, 0xFF)
MIDBLUE = RGBColor(0x3E, 0x8E, 0xDE)
EMBER = RGBColor(0xFF, 0x7A, 0x59)
GOLD = RGBColor(0xF5, 0xB8, 0x3D)
SLATE = RGBColor(0x9A, 0xAB, 0xC4)
MIST = RGBColor(0x2A, 0x3D, 0x5E)
BLACK = RGBColor(0xEE, 0xF3, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SECTIONS = ["The problem", "The instrument", "The measurement", "The physics",
            "Standing"]

FONT = "Calibri"
W, H = 13.333, 7.5
M = 0.75          # slide margin
TITLE_TOP = 0.42
BODY_TOP = 1.42

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


def recolour_icons():
    os.makedirs(ICONS, exist_ok=True)
    tints = {"x-circle": EMBER, "warning": EMBER}
    for name in os.listdir(ICON_SRC):
        stem = os.path.splitext(name)[0]
        tint = tints.get(stem, NAVY)
        img = Image.open(os.path.join(ICON_SRC, name)).convert("RGBA")
        alpha = img.getchannel("A")
        solid = Image.new("RGBA", img.size, (tint[0], tint[1], tint[2], 255))
        solid.putalpha(alpha)
        solid.save(os.path.join(ICONS, name))


recolour_icons()


def set_alpha(shp, opacity):
    clr = shp.fill._xPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    node = OxmlElement("a:alpha")
    node.set("val", str(int(opacity * 100000)))
    clr.append(node)


def plain(shp, colour, opacity=None):
    shp.fill.solid()
    shp.fill.fore_color.rgb = colour
    shp.line.fill.background()
    shp.shadow.inherit = False
    if opacity is not None:
        set_alpha(shp, opacity)
    return shp


def glow(s, cx, cy, d, colour, opacity):
    """A radial glow: colour at the centre fading to nothing at the edge."""
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2),
                             Inches(cy - d / 2), Inches(d), Inches(d))
    shp.line.fill.background()
    shp.shadow.inherit = False
    spPr = shp.fill._xPr
    grad = OxmlElement("a:gradFill")
    grad.set("rotWithShape", "1")
    stops = OxmlElement("a:gsLst")
    for pos, a in [(0, opacity), (100000, 0.0)]:
        gs = OxmlElement("a:gs")
        gs.set("pos", str(pos))
        clr = OxmlElement("a:srgbClr")
        clr.set("val", str(colour))
        al = OxmlElement("a:alpha")
        al.set("val", str(int(a * 100000)))
        clr.append(al)
        gs.append(clr)
        stops.append(gs)
    grad.append(stops)
    path = OxmlElement("a:path")
    path.set("path", "circle")
    rect = OxmlElement("a:fillToRect")
    for side in ("l", "t", "r", "b"):
        rect.set(side, "50000")
    path.append(rect)
    grad.append(path)
    geom = spPr.find(qn("a:prstGeom"))
    geom.addnext(grad)
    return shp


def lattice(s, x, y, cols, rows, cell, seed, bias=0.62, fade=True):
    """An Ising spin lattice: up spins in blue, down spins in ember, with a
    field bias toward up. Decorative only; it carries no data."""
    rng = random.Random(seed)
    for r in range(rows):
        for c in range(cols):
            up = rng.random() < bias
            size = cell * 0.46
            px = x + c * cell + (cell - size * 0.62) / 2
            py = y + r * cell + (cell - size) / 2
            kind = MSO_SHAPE.UP_ARROW if up else MSO_SHAPE.DOWN_ARROW
            shp = s.shapes.add_shape(kind, Inches(px), Inches(py),
                                     Inches(size * 0.62), Inches(size))
            opacity = 0.9
            if fade:
                opacity = 0.18 + 0.72 * (c / max(cols - 1, 1))
            plain(shp, NAVY if up else EMBER, opacity)


def slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    glow(s, W - 0.6, -0.4, 7.5, MIDBLUE, 0.28)
    glow(s, -0.8, H + 0.6, 6.0, EMBER, 0.10)
    return s


def textbox(s, x, y, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf


def para(tf, text, size=20, bold=False, colour=BLACK, space_after=8,
         first=False, align=None, italic=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align is not None:
        p.alignment = align
    p.space_after = Pt(space_after)
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = colour
    run.font.name = FONT
    return p


def rich(tf, parts, size=20, space_after=8, first=False, align=None):
    """One paragraph, several runs: parts is a list of (text, bold, colour)."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align is not None:
        p.alignment = align
    p.space_after = Pt(space_after)
    for text, bold, colour in parts:
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = colour
        run.font.name = FONT
    return p


def formula(tf, parts, size=30, colour=NAVY, first=False, align=PP_ALIGN.CENTER):
    """A display formula. Parts are (text, level) with level 0 normal,
    -1 subscript, +1 superscript, so a subscript is set rather than faked with
    an underscore."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(0)
    for text, level in parts:
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = True
        run.font.color.rgb = colour
        run.font.name = FONT
        if level < 0:
            run.font._rPr.set("baseline", "-25000")
        elif level > 0:
            run.font._rPr.set("baseline", "30000")
    return p


def action_title(s, text, icon=None):
    x = M
    if icon:
        s.shapes.add_picture(os.path.join(ICONS, icon + ".png"),
                             Inches(M), Inches(TITLE_TOP - 0.02),
                             height=Inches(0.46))
        x = M + 0.66
    tf = textbox(s, x, TITLE_TOP - 0.08, W - x - M, 0.9)
    para(tf, text, size=26, bold=True, colour=NAVY, first=True, space_after=0)


def footer(s, section, number):
    tf = textbox(s, M, H - 0.62, 5.0, 0.35)
    para(tf, section.upper(), size=10, bold=True, colour=SLATE, first=True,
         space_after=0)
    active = SECTIONS.index(section)
    seg, gap = 0.55, 0.08
    x0 = W / 2 - (len(SECTIONS) * seg + (len(SECTIONS) - 1) * gap) / 2
    for i in range(len(SECTIONS)):
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(x0 + i * (seg + gap)),
                                 Inches(H - 0.47), Inches(seg), Pt(3))
        plain(bar, NAVY if i == active else MIST,
              None if i <= active else 0.8)
    tf = textbox(s, W - M - 1.0, H - 0.62, 1.0, 0.35, align=PP_ALIGN.RIGHT)
    para(tf, "%02d" % number, size=11, bold=True, colour=SLATE, first=True,
         space_after=0)


def figure(s, path, x, y, w=None, h=None, pad=0.14):
    """Analysis figures keep their white ground, so each sits on a paper card."""
    iw, ih = Image.open(path).size
    if w is None:
        assert h is not None
        w = h * iw / ih
    else:
        h = w * ih / iw
    paper = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                               Inches(x - pad), Inches(y - pad),
                               Inches(w + 2 * pad), Inches(h + 2 * pad))
    paper.adjustments[0] = 0.04
    plain(paper, WHITE)
    s.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w),
                         height=Inches(h))
    return w, h


def source(s, text, y=None):
    tf = textbox(s, M, y if y else H - 1.05, W - 2 * M, 0.42)
    para(tf, text, size=11, colour=SLATE, first=True, space_after=0)


def card(s, x, y, w, h, line=MIST, fill=SURFACE, width=1.25):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                             Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = 0.06
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line
    shp.line.width = Pt(width)
    shp.shadow.inherit = False
    shp.text_frame.word_wrap = True
    return shp


def rule(s, x, y, w, colour=MIST, thickness=1.5):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Pt(thickness))
    shp.fill.solid()
    shp.fill.fore_color.rgb = colour
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def arrow(s, x, y, w, h=0.16, colour=SLATE):
    shp = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = colour
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def divider(s, num, title, sub, icon):
    tf = textbox(s, 0.55, 0.35, 7.5, 5.0)
    para(tf, num, size=260, bold=True, colour=GHOST, first=True, space_after=0)
    s.shapes.add_picture(os.path.join(ICONS, icon + ".png"),
                         Inches(1.3), Inches(2.35), height=Inches(0.72))
    tf = textbox(s, 1.3, 3.25, 6.8, 2.0)
    para(tf, num, size=40, bold=True, colour=MIDBLUE, first=True, space_after=2)
    para(tf, title, size=36, bold=True, colour=BLACK, space_after=8)
    para(tf, sub, size=18, colour=SLATE)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.3), Inches(5.55),
                             Inches(1.2), Pt(4))
    plain(bar, EMBER)
    lattice(s, 8.4, 1.25, 7, 8, 0.62, seed=int(num), bias=0.5 + 0.06 * int(num))


def hero(s, label, number, lines):
    glow(s, W / 2, 3.2, 6.5, MIDBLUE, 0.35)
    tf = textbox(s, 1.0, 1.35, W - 2.0, 0.6, align=PP_ALIGN.CENTER)
    para(tf, label.upper(), size=15, bold=True, colour=SLATE, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, 1.0, 1.85, W - 2.0, 1.5, align=PP_ALIGN.CENTER)
    para(tf, number, size=88, bold=True, colour=BLACK, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
    tf = textbox(s, 2.0, 3.55, W - 4.0, 1.0, align=PP_ALIGN.CENTER)
    for i, (text, colour) in enumerate(lines):
        para(tf, text, size=18, colour=colour, first=(i == 0),
             align=PP_ALIGN.CENTER, space_after=6)


def scale_bars(s, rows, top, maximum, left=3.6, length=7.2, label_w=2.6):
    """Horizontal bars drawn to scale: rows are (label, value, text, colour)."""
    for i, (label, value, text, colour) in enumerate(rows):
        y = top + i * 0.62
        tf = textbox(s, left - label_w - 0.15, y - 0.07, label_w, 0.45,
                     align=PP_ALIGN.RIGHT)
        para(tf, label, size=15, colour=SLATE, first=True, align=PP_ALIGN.RIGHT,
             space_after=0)
        track = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(y),
                                   Inches(length), Inches(0.3))
        plain(track, MIST, 0.5)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(y),
                                 Inches(max(length * value / maximum, 0.04)),
                                 Inches(0.3))
        plain(bar, colour)
        tf = textbox(s, left + length + 0.15, y - 0.07, 2.0, 0.45)
        para(tf, text, size=15, bold=True, colour=colour, first=True,
             space_after=0)




n = 0


def num():
    global n
    n += 1
    return n


def tile(s, x, y, w, h, value, label, note=None, colour=NAVY, line=MIST,
         size=40):
    shp = card(s, x, y, w, h, line=line, width=2.0 if line != MIST else 1.25)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, value, size=size, bold=True, colour=colour, first=True,
         align=PP_ALIGN.CENTER, space_after=2)
    para(tf, label, size=15, colour=BLACK, align=PP_ALIGN.CENTER, space_after=2)
    if note:
        para(tf, note, size=12, colour=SLATE, align=PP_ALIGN.CENTER,
             space_after=0)
    return shp


def accent_bar(s, x, y, h, colour=EMBER):
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                             Pt(4), Inches(h))
    plain(bar, colour)


# ----------------------------------------------------------------- 1 title
s = slide()
lattice(s, 8.75, 1.15, 7, 9, 0.52, seed=7, bias=0.64)
tf = textbox(s, 8.75, 5.95, 3.64, 0.4, align=PP_ALIGN.CENTER)
para(tf, "m = tanh(βJ m + h),   h = αX", size=14, colour=SLATE, first=True,
     align=PP_ALIGN.CENTER, space_after=0)
tf = textbox(s, M + 0.15, 1.15, 7.6, 0.4)
para(tf, "B.Sc. PHYSICS   ·   NATURAL SCIENCES   ·   CUEA", size=13, bold=True,
     colour=NAVY, first=True, space_after=0)
tf = textbox(s, M + 0.15, 1.65, 7.6, 1.9)
para(tf, "Measuring the", size=50, bold=True, colour=BLACK, first=True,
     space_after=0)
para(tf, "External Field", size=50, bold=True, colour=NAVY, space_after=0)
tf = textbox(s, M + 0.15, 3.55, 7.4, 1.0)
para(tf, "A cortical-proxy content observable and the mean-field bound on "
         "media-driven opinion change", size=19, colour=SLATE, first=True,
     space_after=0)
rule(s, M + 0.15, 4.75, 1.4, colour=EMBER, thickness=4)
tf = textbox(s, M + 0.15, 5.0, 7.4, 1.4)
rich(tf, [("Brian Mwai", True, BLACK), ("   1050555", False, SLATE)],
     size=20, first=True, space_after=4)
para(tf, "Supervisor: Dr. Songa Mutambi", size=15, colour=SLATE, space_after=2)
para(tf, "September 2026", size=15, colour=SLATE, space_after=0)
num()

# ----------------------------------------------------------------- 2 problem
s = slide()
action_title(s, "Media is modelled as a field on opinion. That field is assumed, "
                "never measured", "newspaper")
for x, tag, parts, verdict, colour, line in [
    (M, "WIRE REPORT",
     [("Federal Reserve holds interest rates steady, citing a stable "
       "inflation outlook.", False, BLACK)], "informs", SLATE, MIST),
    (7.1, "THE SAME EVENT",
     [("FED DESTROYS AMERICA. ", True, BLACK),
      ("Your savings are GONE. The collapse they hid from you!", False, BLACK)],
     "provokes", EMBER, EMBER)]:
    shp = card(s, x, 1.6, 5.5, 1.75, line=line,
               width=2.0 if line == EMBER else 1.25)
    tf = shp.text_frame
    tf.margin_left, tf.margin_top = Inches(0.25), Inches(0.18)
    para(tf, tag, size=12, bold=True, colour=SLATE, first=True, space_after=6)
    rich(tf, parts, size=18, space_after=0)
    tf = textbox(s, x, 3.45, 5.5, 0.4, align=PP_ALIGN.CENTER)
    para(tf, verdict, size=17, bold=True, colour=colour, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
tf = textbox(s, M, 4.05, W - 2 * M, 0.6)
para(tf, "Readers notice the difference and cannot quantify it. Sentiment, "
         "readability and stance measure the words, not the response.",
     size=18, colour=SLATE, first=True, space_after=0)
shp = card(s, M, 4.85, W - 2 * M, 1.25, line=MIST)
accent_bar(s, M, 4.85, 1.25, NAVY)
tf = shp.text_frame
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
tf.margin_left = Inches(0.35)
para(tf, "This project measures the field from content itself, applies it to "
         "400 articles, and derives how strong the coupling must be for that "
         "spread to move a population at all.", size=19, bold=True,
     colour=BLACK, first=True, space_after=0)
footer(s, "The problem", num())

# ----------------------------------------------------------------- 3 cascade
s = slide()
action_title(s, "A five-stage cascade turns one article into one number", "brain")
stages = [("Text", "one article"), ("Speech", "synthesised"),
          ("Timings", "per word"), ("Embeddings", "text + audio"),
          ("TRIBE v2", "encoder"), ("20,484", "vertices")]
x0, cw, gap, cy, ch = 0.62, 1.72, 0.34, 1.70, 1.05
for i, (head, sub) in enumerate(stages):
    x = x0 + i * (cw + gap)
    hot = i >= 4
    shp = card(s, x, cy, cw, ch, line=NAVY if hot else MIST,
               width=2.0 if hot else 1.25)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, head, size=15, bold=True, colour=NAVY if hot else BLACK,
         first=True, align=PP_ALIGN.CENTER, space_after=2)
    para(tf, sub, size=12, colour=SLATE, align=PP_ALIGN.CENTER, space_after=0)
    if i < len(stages) - 1:
        arrow(s, x + cw + 0.05, cy + ch / 2 - 0.07, gap - 0.10, 0.14, MIDBLUE)

x_last = x0 + 5 * (cw + gap)
vline = s.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                           Inches(x_last + cw / 2 - 0.01), Inches(cy + ch),
                           Pt(1.5), Inches(0.45))
plain(vline, SLATE)
hline = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.05),
                           Inches(cy + ch + 0.45),
                           Inches(x_last + cw / 2 - 2.05), Pt(1.5))
plain(hline, SLATE)

reduce_y = 3.85
for x, head, sub, colour in [(1.45, "Affective", "1,030 vertices", EMBER),
                             (5.20, "Deliberative", "851 vertices", NAVY)]:
    drop = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x + 1.16),
                              Inches(cy + ch + 0.45), Inches(0.18),
                              Inches(0.42))
    plain(drop, SLATE)
    shp = card(s, x, reduce_y, 2.5, 1.0, line=colour, width=2.0)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, head, size=15, bold=True, colour=colour, first=True,
         align=PP_ALIGN.CENTER, space_after=2)
    para(tf, sub, size=12, colour=SLATE, align=PP_ALIGN.CENTER, space_after=0)

tf = textbox(s, 4.05, reduce_y + 0.22, 1.0, 0.5, align=PP_ALIGN.CENTER)
para(tf, "−", size=30, bold=True, colour=SLATE, first=True,
     align=PP_ALIGN.CENTER, space_after=0)
tf = textbox(s, 7.80, reduce_y + 0.22, 1.0, 0.5, align=PP_ALIGN.CENTER)
para(tf, "=", size=30, bold=True, colour=NAVY, first=True,
     align=PP_ALIGN.CENTER, space_after=0)
shp = card(s, 8.80, reduce_y, 2.9, 1.0, line=NAVY, width=2.0)
tf = shp.text_frame
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
para(tf, "One number", size=17, bold=True, colour=NAVY, first=True,
     align=PP_ALIGN.CENTER, space_after=2)
para(tf, "per article", size=12, colour=SLATE, align=PP_ALIGN.CENTER,
     space_after=0)
source(s, "Encoder: TRIBE v2, d'Ascoli et al., Meta FAIR (2025), "
          "arXiv:2507.22229.  Regions from HCP MMP1.0, Glasser et al. (2016).  "
          "Instrument at monarch-4iy.pages.dev", y=5.55)
footer(s, "The instrument", num())

# ----------------------------------------------------------------- 4 regions + observable
s = slide()
action_title(s, "The index contrasts two cortical networks, 1,030 vertices "
                "against 851", "brain")
figure(s, os.path.join(FIG, "B1_roi_definition.png"), 0.95, 1.65, w=7.2)
shp = card(s, 8.65, 1.51, 3.95, 3.52, line=NAVY, width=2.0)
tf = shp.text_frame
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
tf.margin_left = tf.margin_right = Inches(0.2)
para(tf, "THE OBSERVABLE", size=12, bold=True, colour=SLATE, first=True,
     align=PP_ALIGN.CENTER, space_after=10)
formula(tf, [("NAA", 0), ("signed", -1)], size=30)
formula(tf, [("= A", 0), ("aff", -1), ("  −  A", 0), ("del", -1)], size=30)
para(tf, " ", size=8, space_after=6)
rich(tf, [("> 0   ", True, EMBER), ("emotion leads", False, BLACK)], size=17,
     align=PP_ALIGN.CENTER, space_after=4)
rich(tf, [("< 0   ", True, NAVY), ("reasoning leads", False, BLACK)], size=17,
     align=PP_ALIGN.CENTER, space_after=0)
tf = textbox(s, M, 5.35, W - 2 * M, 0.9)
rich(tf, [("A cortical proxy: ", True, BLACK),
          ("it rates content, never a person, and is never called the "
           "amygdala. Regions resolved once and cached, so all 400 items "
           "average over identical vertices.", False, SLATE)], size=16,
     first=True, space_after=0)
source(s, "Regions on HCP MMP1.0 (Glasser et al., 2016); fsaverage5 surfaces.",
       y=6.2)
footer(s, "The instrument", num())

# ----------------------------------------------------------------- 5 checkpoint
s = slide()
action_title(s, "Inspecting the checkpoint changed what the project could claim",
             "magnifying-glass")
findings = [
    ("01", "Cortical only", "No subcortical output.",
     "No amygdala, so the proposal's equation cannot be computed.", True),
    ("02", "Averaged over subjects", "The loader forces it.",
     "It predicts a typical viewer, which Paper 3 tests.", False),
    ("03", "Standardised output", "Means sit near zero, so a ratio breaks.",
     "Undefined for 69 of 400 items; the difference replaces it.", False),
]
cw = 3.75
for i, (idx, head, body, tail, alert) in enumerate(findings):
    x = M + i * (cw + 0.42)
    shp = card(s, x, 1.6, cw, 3.45, line=EMBER if alert else MIST,
               width=2.0 if alert else 1.25)
    tf = shp.text_frame
    tf.margin_left = tf.margin_right = Inches(0.28)
    tf.margin_top = Inches(0.25)
    para(tf, idx, size=34, bold=True, colour=EMBER if alert else MIDBLUE,
         first=True, space_after=6)
    para(tf, head, size=20, bold=True, colour=BLACK, space_after=10)
    para(tf, body, size=16, colour=SLATE, space_after=10)
    para(tf, tail, size=16, bold=alert, colour=EMBER if alert else BLACK,
         space_after=0)
tf = textbox(s, M, 5.4, W - 2 * M, 0.6)
para(tf, "All three were found by testing the checkpoint, before any result.",
     size=17, colour=SLATE, first=True, space_after=0)
footer(s, "The instrument", num())

# ----------------------------------------------------------------- 6 corpus
s = slide()
action_title(s, "The corpus is length-matched and was powered before the scan",
             "books")
cats = [("fear-activating", "ISOT-fake", EMBER),
        ("high outrage", "SemEval-2019 T4", GOLD),
        ("reward hook", "Webis-Clickbait-17", MIDBLUE),
        ("neutral informational", "PubMed + ISOT-true", SLATE)]
cw = 2.72
for i, (name, src, colour) in enumerate(cats):
    x = M + i * (cw + 0.317)
    shp = card(s, x, 1.6, cw, 1.75)
    accent_bar(s, x, 1.6, 1.75, colour)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, "100", size=34, bold=True, colour=colour, first=True,
         align=PP_ALIGN.CENTER, space_after=2)
    para(tf, name, size=16, bold=True, colour=BLACK, align=PP_ALIGN.CENTER,
         space_after=4)
    para(tf, src, size=12, colour=SLATE, align=PP_ALIGN.CENTER, space_after=0)
tile(s, M, 3.7, 5.75, 1.6, "≈ 164 words", "length-matched",
     "means 167.4, 163.5, 163.7, 162.2; sd near 11", size=30)
tile(s, 6.83, 3.7, 5.75, 1.6, "η² ≥ 0.0268",
     "detectable, fixed before the scan", "smallest detectable AUC = 0.5916",
     size=30)
source(s, "Corpora: Ahmed et al. (ISOT, 2017); Kiesel et al. (SemEval-2019 "
          "Task 4); Potthast et al. (Webis-Clickbait-17); PubMed open "
          "abstracts.", y=5.75)
footer(s, "The measurement", num())

# ----------------------------------------------------------------- 7 hero
s = slide()
hero(s, "the four categories separate at", "η² = 0.1068",
     [("F = 15.779    p = 1.03 × 10⁻⁹    n = 400", BLACK)])
scale_bars(s, [("first session", 0.1068, "0.1068", NAVY),
               ("second session", 0.0888, "0.0888", MIDBLUE),
               ("powered to detect", 0.0268, "0.0268", SLATE)],
           top=4.55, maximum=0.12, left=4.1, length=6.0)
footer(s, "The measurement", num())

# ----------------------------------------------------------------- 8 violin
s = slide()
action_title(s, "Categories shift against each other, but the distributions "
                "overlap", "chart-bar")
violin = os.path.join(REPORT, "fig_violin.png")
vw, vh = Image.open(violin).size
figure(s, violin, (W - 3.9 * vw / vh) / 2, 1.55, h=3.9)
tf = textbox(s, M, 5.8, W - 2 * M, 0.8, align=PP_ALIGN.CENTER)
para(tf, "Every category mean is negative: the deliberative network leads "
         "throughout, and the categories differ in how far below zero they "
         "sit.", size=15, colour=SLATE, first=True, align=PP_ALIGN.CENTER,
     space_after=0)
footer(s, "The measurement", num())

# ----------------------------------------------------------------- 9 effect sizes
s = slide()
action_title(s, "Fear-activating content carries the effect; outrage moves "
                "both networks equally", "chart-bar")
tf = textbox(s, M, 1.45, 6, 0.4)
para(tf, "COHEN'S d AGAINST THE NEUTRAL BASELINE", size=12, bold=True,
     colour=SLATE, first=True, space_after=0)
scale_bars(s, [("fear-activating", 0.939, "d = 0.939", EMBER),
               ("reward hook", 0.319, "d = 0.319", MIDBLUE),
               ("high outrage", 0.030, "d = 0.030  (p = 0.832)", GOLD)],
           top=2.0, maximum=1.0, left=3.4, length=6.6)
shp = card(s, M, 4.15, W - 2 * M, 1.85, line=GOLD, width=2.0)
tf = shp.text_frame
tf.margin_left = tf.margin_right = Inches(0.35)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
para(tf, "OUTRAGE, TAKEN APART", size=12, bold=True, colour=GOLD, first=True,
     space_after=6)
rich(tf, [("Affective d = +0.507, deliberative d = +0.491. ", True, BLACK),
          ("A flat index here is a symmetric response, not an absent one. "
           "Fear raises one network only (d = +0.613 and −0.098).", False,
           BLACK)], size=18, space_after=0)
footer(s, "The measurement", num())

# ----------------------------------------------------------------- 10 confound + baseline
s = slide()
action_title(s, "Category is confounded with source, and a bag of words beats "
                "the index", "warning")
pairs = [("fear-activating", "ISOT-fake"), ("high outrage", "SemEval-2019 T4"),
         ("reward hook", "Webis-Clickbait-17"),
         ("neutral", "PubMed + ISOT-true")]
for x, label in [(M, "CATEGORY"), (3.95, "SOURCE DATASET")]:
    tf = textbox(s, x, 1.45, 2.45, 0.35, align=PP_ALIGN.CENTER)
    para(tf, label, size=11, bold=True, colour=SLATE, first=True,
         align=PP_ALIGN.CENTER, space_after=0)
for i, (cat, src) in enumerate(pairs):
    y = 1.9 + i * 0.7
    for x, text in [(M, cat), (3.95, src)]:
        shp = card(s, x, y, 2.45, 0.55)
        tf = shp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(tf, text, size=14, colour=BLACK, first=True,
             align=PP_ALIGN.CENTER, space_after=0)
    arrow(s, 3.28, y + 0.2, 0.6, 0.14, EMBER)
tile(s, 7.1, 1.55, 2.65, 1.85, "0.6274", "AUC, the index", "nothing fitted",
     colour=SLATE)
tile(s, 9.95, 1.55, 2.65, 1.85, "0.9758", "AUC, TF-IDF", "logistic, 5-fold",
     colour=EMBER, line=EMBER)
tf = textbox(s, 7.1, 3.55, 5.5, 1.2)
para(tf, "Same 400 rows, same label. VADER sits at chance, 0.5392. The same "
         "words guess the source 66% of the time against 25%, so much of the "
         "lexical win is provenance.", size=14, colour=SLATE, first=True,
     space_after=0)
shp = card(s, M, 4.95, W - 2 * M, 1.05)
accent_bar(s, M, 4.95, 1.05)
tf = shp.text_frame
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
tf.margin_left = Inches(0.35)
rich(tf, [("Length is controlled; provenance is not.  ", False, BLACK),
          ("The index is a field observable for the physics, not a detector.",
           True, EMBER)], size=18, first=True, space_after=0)
source(s, "Hutto & Gilbert (2014), VADER.  One source per category, so the "
          "separation cannot be attributed to framing.", y=6.15)
footer(s, "The measurement", num())

# ----------------------------------------------------------------- 11 reliability
s = slide()
action_title(s, "Group-level claims hold at this precision; per-item claims do "
                "not", "arrows-clockwise")
tile(s, M, 1.55, 5.6, 1.9, "0.8725", "ICC between two GPU sessions",
     "separation replicates: η² = 0.0888 against 0.1068", colour=NAVY,
     line=NAVY, size=48)
tile(s, 7.0, 1.55, 5.6, 1.9, "12.8%", "of items reverse direction",
     "51 of 400; no verdict on one article is ever made", colour=EMBER,
     size=48)
tf = textbox(s, M, 3.85, W - 2 * M, 0.4)
para(tf, "REVERSALS: OBSERVED AGAINST WHAT MEASURED NOISE ALONE PREDICTS",
     size=12, bold=True, colour=SLATE, first=True, space_after=0)
lo, hi, ax0, axw, ay = 40, 70, 2.2, 8.9, 4.95


def at(v):
    return ax0 + (v - lo) / (hi - lo) * axw


axis_line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(ax0), Inches(ay),
                               Inches(axw), Pt(1.5))
plain(axis_line, MIST)
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(at(44)),
                          Inches(ay - 0.16), Inches(at(67) - at(44)),
                          Inches(0.34))
plain(band, MIDBLUE, 0.35)
tick = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(at(55.3) - 0.015),
                          Inches(ay - 0.3), Pt(3), Inches(0.62))
plain(tick, NAVY)
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(at(51) - 0.13),
                         Inches(ay - 0.12), Inches(0.26), Inches(0.26))
plain(dot, EMBER)
for v in (40, 50, 60, 70):
    tf = textbox(s, at(v) - 0.4, ay + 0.3, 0.8, 0.3, align=PP_ALIGN.CENTER)
    para(tf, str(v), size=11, colour=SLATE, first=True, align=PP_ALIGN.CENTER,
         space_after=0)
tf = textbox(s, at(55.3) - 1.5, ay - 0.75, 3.0, 0.4, align=PP_ALIGN.CENTER)
para(tf, "noise predicts 55.3, 95% [44, 67]", size=13, bold=True, colour=NAVY,
     first=True, align=PP_ALIGN.CENTER, space_after=0)
tf = textbox(s, at(51) - 1.2, ay + 0.6, 2.4, 0.4, align=PP_ALIGN.CENTER)
para(tf, "observed 51", size=13, bold=True, colour=EMBER, first=True,
     align=PP_ALIGN.CENTER, space_after=0)
footer(s, "The measurement", num())

# ----------------------------------------------------------------- 12 mean field + alpha
s = slide()
action_title(s, "Media enters as a field h = αX, and the corpus cannot pin "
                "down α", "atom")
shp = card(s, M, 1.55, 6.05, 3.95, line=NAVY, width=2.0)
tf = shp.text_frame
tf.margin_left = tf.margin_right = Inches(0.3)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
para(tf, "THE MODEL", size=12, bold=True, colour=SLATE, first=True,
     space_after=8)
para(tf, "Opinions ±1, pulled toward neighbours by J, pushed by media with "
         "field h = αX.", size=16, colour=BLACK, space_after=14)
para(tf, "m = tanh(βJ m + h)", size=24, bold=True, colour=NAVY,
     align=PP_ALIGN.CENTER, space_after=10)
para(tf, "F(m) = a m² + b m⁴ − h m", size=24, bold=True, colour=NAVY,
     align=PP_ALIGN.CENTER, space_after=6)
para(tf, "a = (1 − βJ)/2,   b = 1/12", size=18, bold=True, colour=NAVY,
     align=PP_ALIGN.CENTER, space_after=14)
para(tf, "Coefficients derived, correcting the proposal's a and b.", size=14,
     colour=SLATE, space_after=0)
shp = card(s, 7.1, 1.55, 5.5, 3.95)
tf = shp.text_frame
tf.margin_left = tf.margin_right = Inches(0.3)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
para(tf, "THE COUPLING", size=12, bold=True, colour=SLATE, first=True,
     space_after=8)
rich(tf, [("Tried. ", True, BLACK),
          ("Fit the outcome to the index and read off α.", False, BLACK)],
     size=17, space_after=12)
rich(tf, [("Result. ", True, BLACK),
          ("Out of sample the fit does worse than the average, and the "
           "estimate depends on βJ, which nothing here measures.", False,
           BLACK)], size=17, space_after=14)
para(tf, "So no value of α is quoted anywhere.", size=19, bold=True,
     colour=EMBER, space_after=0)
tf = textbox(s, M, 5.8, W - 2 * M, 0.5)
para(tf, "What replaces it needs no fit at all: the bound.", size=17,
     colour=SLATE, first=True, space_after=0)
footer(s, "The physics", num())

# ----------------------------------------------------------------- 13 the bound
s = slide()
action_title(s, "Any content observable must clear a bound to drive a "
                "transition", "ruler")
figure(s, os.path.join(PAPER1, "F6_alpha_required.png"), 0.95, 1.6, h=4.25)
glow(s, 10.1, 2.4, 4.0, MIDBLUE, 0.35)
tf = textbox(s, 7.6, 1.9, 5.0, 0.9, align=PP_ALIGN.CENTER)
formula(tf, [("α  ≥  h", 0), ("c", -1), ("(βJ) / ΔX", 0)], size=36,
        colour=BLACK, first=True)
tf = textbox(s, 7.6, 3.05, 5.0, 1.3)
para(tf, "What α would have to be for media to tip opinion, for any "
         "observable, before any data. Within the mean-field model.", size=17,
     colour=SLATE, first=True, space_after=0)
tile(s, 7.6, 4.3, 5.0, 1.55, "α ≥ 4.29", "at βJ = 2", "measured ΔX = 0.1241",
     colour=EMBER, line=EMBER, size=36)
footer(s, "The physics", num())

# ----------------------------------------------------------------- 14 claims
s = slide()
action_title(s, "Four claims the work supports, and four it does not",
             "check-circle")
for x, icon, head, colour, rows in [
    (M, "check-circle", "SUPPORTED", NAVY, [
        "A content observable that can be measured, with its reliability "
        "stated.",
        "That it separates these four corpora at 0.1068, power attached.",
        "A bound any candidate observable must satisfy, usable before data "
        "exists.",
        "A noise ceiling on public fMRI (0.1517), and a first check of the "
        "encoder against it.",
    ]),
    (6.83, "x-circle", "NOT SUPPORTED", EMBER, [
        "That the index detects manipulation. Source is confounded; TF-IDF "
        "scores 0.9758.",
        "Anything about the amygdala. The checkpoint does not predict it.",
        "Any value of the coupling α. The corpus does not identify it.",
        "Any verdict on one article. 12.8% reverse between sessions.",
    ])]:
    card(s, x, 1.5, 5.75, 4.55, line=colour, width=2.0)
    s.shapes.add_picture(os.path.join(ICONS, icon + ".png"), Inches(x + 0.3),
                         Inches(1.75), height=Inches(0.38))
    tf = textbox(s, x + 0.8, 1.73, 4.5, 0.45)
    para(tf, head, size=17, bold=True, colour=colour, first=True,
         space_after=0)
    tf = textbox(s, x + 0.3, 2.35, 5.2, 3.6)
    for i, text in enumerate(rows):
        para(tf, "•  " + text, size=16, colour=BLACK, first=(i == 0),
             space_after=12)
footer(s, "Standing", num())

# ----------------------------------------------------------------- 15 conclusions
s = slide()
action_title(s, "Conclusions", "flag-banner")
tf = textbox(s, M, 1.4, W - 2 * M, 3.6)
conclusions = [
    ("A field observable can be measured from content. ",
     "The instrument runs, the corpus is complete, and reliability is "
     "measured: ICC = 0.8725."),
    ("It separates four corpora at 0.1068, confounded with source. ",
     "Both halves are reported, the confound first."),
    ("The coupling is unidentified, so the thesis reports a bound. ",
     "With ΔX = 0.1241, α ≥ 4.294 at βJ = 2: a constraint on any future "
     "proposal of this mechanism."),
    ("The encoder is weakly positive against real brains. ",
     "r = +0.028 against a ceiling of 0.096 on the same scans; not yet "
     "decisive."),
]
for i, (head, body) in enumerate(conclusions):
    rich(tf, [("%d.  " % (i + 1), True, EMBER), (head, True, BLACK),
              (body, False, SLATE)], size=17, first=(i == 0), space_after=12)
outputs = [("81 pp", "Dissertation"), ("12 pp", "Paper 1 · Physica A"),
           ("16 pp", "Paper 2 · Physica A"),
           ("8 pp", "Paper 3 · Imaging Neurosci.")]
cw = 2.72
for i, (pages, name) in enumerate(outputs):
    x = M + i * (cw + 0.317)
    shp = card(s, x, 4.95, cw, 0.95, line=NAVY if i == 0 else MIST,
               width=2.0 if i == 0 else 1.25)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rich(tf, [(pages + "   ", True, NAVY), (name, False, BLACK)], size=15,
         first=True, align=PP_ALIGN.CENTER, space_after=0)
tf = textbox(s, M, 6.05, W - 2 * M, 0.4)
para(tf, "Every number comes from a re-runnable script  ·  "
         "github.com/brn-mwai/monarch  ·  monarch-4iy.pages.dev", size=12,
     colour=SLATE, first=True, space_after=0)
footer(s, "Standing", num())

prs.save(OUT)
print("wrote", OUT)
print("slides", len(prs.slides))
