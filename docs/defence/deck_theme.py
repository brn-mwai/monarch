"""Dark theme shared by the plain-language decks: palette, text helpers, cards,
glows, bars and the spin-lattice motif. Every helper draws native shapes so the
presenter can retype anything in PowerPoint."""

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

BG = RGBColor(0x0A, 0x16, 0x28)
SURFACE = RGBColor(0x12, 0x22, 0x3C)
BLUE = RGBColor(0x7C, 0xC4, 0xFF)
MIDBLUE = RGBColor(0x3E, 0x8E, 0xDE)
EMBER = RGBColor(0xFF, 0x7A, 0x59)
GOLD = RGBColor(0xF5, 0xB8, 0x3D)
GREEN = RGBColor(0x5F, 0xD0, 0x9A)
MUTED = RGBColor(0x9A, 0xAB, 0xC4)
LINE = RGBColor(0x2A, 0x3D, 0x5E)
TEXT = RGBColor(0xEE, 0xF3, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Calibri"
W, H = 13.333, 7.5
M = 0.75


def recolour_icons():
    os.makedirs(ICONS, exist_ok=True)
    tints = {"x-circle": EMBER, "warning": EMBER}
    for name in os.listdir(ICON_SRC):
        tint = tints.get(os.path.splitext(name)[0], BLUE)
        img = Image.open(os.path.join(ICON_SRC, name)).convert("RGBA")
        solid = Image.new("RGBA", img.size, (tint[0], tint[1], tint[2], 255))
        solid.putalpha(img.getchannel("A"))
        solid.save(os.path.join(ICONS, name))


def new_deck():
    recolour_icons()
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    return prs


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
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2),
                             Inches(cy - d / 2), Inches(d), Inches(d))
    shp.line.fill.background()
    shp.shadow.inherit = False
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
    shp.fill._xPr.find(qn("a:prstGeom")).addnext(grad)
    return shp


def lattice(s, x, y, cols, rows, cell, seed, bias=0.62):
    """Decorative Ising spin lattice; it carries no data."""
    rng = random.Random(seed)
    for r in range(rows):
        for c in range(cols):
            up = rng.random() < bias
            size = cell * 0.46
            shp = s.shapes.add_shape(
                MSO_SHAPE.UP_ARROW if up else MSO_SHAPE.DOWN_ARROW,
                Inches(x + c * cell + (cell - size * 0.62) / 2),
                Inches(y + r * cell + (cell - size) / 2),
                Inches(size * 0.62), Inches(size))
            plain(shp, BLUE if up else EMBER,
                  0.18 + 0.72 * (c / max(cols - 1, 1)))


def slide(prs, notes=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    glow(s, W - 0.6, -0.4, 7.5, MIDBLUE, 0.28)
    glow(s, -0.8, H + 0.6, 6.0, EMBER, 0.10)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def textbox(s, x, y, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w),
                              Inches(h)).text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf


def para(tf, text, size=18, bold=False, colour=TEXT, space_after=6,
         first=False, align=None, italic=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align is None and not first:
        align = tf.paragraphs[0].alignment
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


def rich(tf, parts, size=18, space_after=6, first=False, align=None):
    """One paragraph of several runs; parts are (text, bold, colour)."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align is None and not first:
        align = tf.paragraphs[0].alignment
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


def card(s, x, y, w, h, line=LINE, fill=SURFACE, width=None):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                             Inches(w), Inches(h))
    shp.adjustments[0] = 0.06
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line
    shp.line.width = Pt(width or (1.25 if line == LINE else 2.0))
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.paragraphs[0].alignment = PP_ALIGN.LEFT
    tf.margin_left = tf.margin_right = Inches(0.22)
    tf.margin_top = tf.margin_bottom = Inches(0.12)
    return shp


def bar(s, x, y, w, h, colour, opacity=None):
    return plain(s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                    Inches(w), Inches(h)), colour, opacity)


def arrow(s, x, y, w, h=0.16, colour=MIDBLUE):
    return plain(s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y),
                                    Inches(w), Inches(h)), colour)


def icon(s, name, x, y, h=0.46):
    s.shapes.add_picture(os.path.join(ICONS, name + ".png"), Inches(x),
                         Inches(y), height=Inches(h))


def header(s, kicker, title, icon_name=None):
    x = M
    if icon_name:
        icon(s, icon_name, M, 0.5)
        x = M + 0.66
    tf = textbox(s, x, 0.22, W - x - M, 0.35)
    para(tf, kicker.upper(), size=12, bold=True, colour=EMBER, first=True,
         space_after=0)
    tf = textbox(s, x, 0.46, W - x - M, 0.9)
    para(tf, title, size=26, bold=True, colour=BLUE, first=True, space_after=0)


def footer(s, sections, section, number):
    tf = textbox(s, M, H - 0.55, 5.0, 0.35)
    para(tf, section.upper(), size=10, bold=True, colour=MUTED, first=True,
         space_after=0)
    active = sections.index(section)
    seg, gap = 0.55, 0.08
    x0 = W / 2 - (len(sections) * seg + (len(sections) - 1) * gap) / 2
    for i in range(len(sections)):
        bar(s, x0 + i * (seg + gap), H - 0.42, seg, 0.04,
            BLUE if i == active else LINE, None if i <= active else 0.8)
    tf = textbox(s, W - M - 1.0, H - 0.55, 1.0, 0.35, align=PP_ALIGN.RIGHT)
    para(tf, "%02d" % number, size=11, bold=True, colour=MUTED, first=True,
         space_after=0)


def figure(s, path, x, y, w=None, h=None, pad=0.12):
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


def number_card(s, x, y, w, h, value, name, means, why=None, colour=BLUE,
                value_size=34):
    """A number with its plain name, what it means, and why it has that value."""
    shp = card(s, x, y, w, h, line=colour)
    tf = shp.text_frame
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_top = Inches(0.16)
    para(tf, value, size=value_size, bold=True, colour=colour, first=True,
         space_after=0)
    para(tf, name, size=14, bold=True, colour=TEXT, space_after=6)
    rich(tf, [("What it means: ", True, MUTED), (means, False, TEXT)], size=13,
         space_after=4)
    if why:
        rich(tf, [("Why this value: ", True, MUTED), (why, False, TEXT)],
             size=13, space_after=0)
    return shp


def scale_bars(s, rows, top, maximum, left=3.6, length=7.2, label_w=2.6,
               step=0.62, size=15):
    """Horizontal bars drawn to scale: rows are (label, value, text, colour)."""
    for i, (label, value, text, colour) in enumerate(rows):
        y = top + i * step
        tf = textbox(s, left - label_w - 0.15, y - 0.07, label_w, 0.45,
                     align=PP_ALIGN.RIGHT)
        para(tf, label, size=size, colour=MUTED, first=True,
             align=PP_ALIGN.RIGHT, space_after=0)
        bar(s, left, y, length, 0.3, LINE, 0.5)
        bar(s, left, y, max(length * value / maximum, 0.04), 0.3, colour)
        tf = textbox(s, left + length + 0.15, y - 0.07, 3.2, 0.45)
        para(tf, text, size=size, bold=True, colour=colour, first=True,
             space_after=0)
