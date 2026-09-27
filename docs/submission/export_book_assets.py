"""Export the dissertation as assets for the 3D book on the Monarch site.

Only the preview pages are exported. Every other page is never written to the site, so it
cannot be downloaded however the front end is altered; the book shows those pages as locked.

Writes to apps/web/public/research/book/:
  pages/p001.webp ... one image per preview page, A4 aspect, readable when zoomed
  cover_front.png, cover_back.png, spine.png  maroon bookcloth with gold foil lettering
  book.json  page count, aspect, page labels, preview and blank page lists, and the outline
"""

import json
import os

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
THESIS = os.path.join(HERE, "..", "thesis", "dissertation.pdf")
OUT = os.path.join(HERE, "..", "..", "apps", "web", "public", "research", "book")
PAGE_WIDTH = 1240
PREVIEW_PAGES = {1, 5, 6, 9, 11, 12, 13, 14, 21, 22, 23, 40, 41}
COVER_WIDTH = 1240
SPINE_WIDTH = 160
MAROON = (107, 28, 42)
GOLD_LIGHT = (242, 214, 142)
GOLD_DARK = (176, 132, 52)
SERIF = r"C:\Windows\Fonts\times.ttf"
SERIF_BOLD = r"C:\Windows\Fonts\timesbd.ttf"

COVER_LINES = [
    ("THE CATHOLIC UNIVERSITY OF EASTERN AFRICA", 0.100, 30, True),
    ("FACULTY OF SCIENCE", 0.140, 28, True),
    ("DEPARTMENT OF NATURAL SCIENCES", 0.180, 28, True),
    ("MEASURING THE EXTERNAL FIELD: A CORTICAL-PROXY CONTENT", 0.300, 28, True),
    ("OBSERVABLE AND THE MEAN-FIELD BOUND ON", 0.335, 28, True),
    ("MEDIA-DRIVEN OPINION CHANGE", 0.370, 28, True),
    ("BY", 0.470, 28, True),
    ("BRIAN MWAI", 0.510, 28, True),
    ("REG. NO. 1050555", 0.550, 28, True),
    ("A Research Project Submitted in Partial Fulfilment of the", 0.680, 27, False),
    ("Requirements for the Award of Bachelor of Science Degree", 0.715, 27, False),
    ("in Physics (B.Sc. Physics)", 0.750, 27, False),
    ("SEPTEMBER, 2026", 0.880, 28, True),
]
SPINE_TEXT = "B. MWAI      MEASURING THE EXTERNAL FIELD      B.Sc. PHYSICS 2026"


def is_blank(page):
    return not page.get_text().strip() and not page.get_images() and not page.get_drawings()


def export_pages(doc):
    folder = os.path.join(OUT, "pages")
    os.makedirs(folder, exist_ok=True)
    for index, page in enumerate(doc, start=1):
        if index not in PREVIEW_PAGES:
            continue
        zoom = PAGE_WIDTH / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        image.save(os.path.join(folder, "p%03d.webp" % index), quality=82, method=6)


def cloth(width, height, seed):
    rng = np.random.default_rng(seed)
    base = np.ones((height, width, 3), np.float32) * np.array(MAROON, np.float32)
    rows = (np.sin(np.arange(height) * 1.9) * 0.5 + 0.5)[:, None]
    cols = (np.sin(np.arange(width) * 1.7) * 0.5 + 0.5)[None, :]
    weave = 0.93 + 0.07 * (rows * 0.5 + cols * 0.5)
    speckle = rng.normal(1.0, 0.035, (height, width))
    blotch = Image.fromarray((rng.random((height // 16, width // 16)) * 255).astype(np.uint8))
    blotch = blotch.resize((width, height), Image.Resampling.BICUBIC)
    blotch = np.asarray(blotch.filter(ImageFilter.GaussianBlur(24)), np.float32) / 255
    shade = weave * speckle * (0.94 + 0.08 * blotch)
    pixels = np.clip(base * shade[:, :, None], 0, 255).astype(np.uint8)
    return Image.fromarray(pixels)


def gold_text(canvas, text, centre_x, centre_y, size, bold, angle=0):
    font = ImageFont.truetype(SERIF_BOLD if bold else SERIF, size)
    box = font.getbbox(text)
    width, height = box[2] - box[0] + 8, box[3] - box[1] + 8
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).text((4 - box[0], 4 - box[1]), text, font=font, fill=255)
    ramp = np.linspace(0, 1, height)[:, None] * np.ones((1, width))
    colour = np.zeros((height, width, 3), np.float32)
    for channel in range(3):
        colour[:, :, channel] = GOLD_LIGHT[channel] * (1 - ramp) + GOLD_DARK[channel] * ramp
    foil = Image.fromarray(colour.astype(np.uint8))
    shadow = Image.new("RGB", (width, height), (40, 8, 14))
    if angle:
        mask, foil, shadow = (image.rotate(angle, expand=True) for image in (mask, foil, shadow))
    left = int(centre_x - mask.width / 2)
    top = int(centre_y - mask.height / 2)
    canvas.paste(shadow, (left + 2, top + 2), mask.filter(ImageFilter.GaussianBlur(1.5)))
    canvas.paste(foil, (left, top), mask)


def make_covers(aspect):
    height = round(COVER_WIDTH * aspect)
    front = cloth(COVER_WIDTH, height, 1)
    for text, y, size, bold in COVER_LINES:
        gold_text(front, text, COVER_WIDTH / 2, y * height, size, bold)
    front.save(os.path.join(OUT, "cover_front.png"), optimize=True)
    cloth(COVER_WIDTH, height, 2).save(os.path.join(OUT, "cover_back.png"), optimize=True)
    spine = cloth(SPINE_WIDTH, height, 3)
    gold_text(spine, SPINE_TEXT, SPINE_WIDTH / 2, height / 2, 34, True, angle=-90)
    spine.save(os.path.join(OUT, "spine.png"), optimize=True)


def outline(doc):
    entries = []
    for level, title, page in doc.get_toc(simple=True):
        if level <= 2 and page > 0:
            entries.append({"level": level, "title": title.strip(), "page": page})
    contents_page = next(
        (index for index, page in enumerate(doc, start=1) if page.get_text().lstrip().startswith("Contents")),
        None,
    )
    if contents_page and not any(entry["title"] == "Contents" for entry in entries):
        entries.append({"level": 1, "title": "Contents", "page": contents_page})
        entries.sort(key=lambda entry: entry["page"])
    return entries


def main():
    os.makedirs(OUT, exist_ok=True)
    doc = fitz.open(THESIS)
    first = doc[0].rect
    aspect = first.height / first.width
    export_pages(doc)
    make_covers(aspect)
    meta = {
        "pages": len(doc),
        "aspect": round(aspect, 5),
        "labels": [page.get_label() or str(index) for index, page in enumerate(doc, start=1)],
        "preview": sorted(PREVIEW_PAGES),
        "blank": [index for index, page in enumerate(doc, start=1) if is_blank(page)],
        "outline": outline(doc),
    }
    with open(os.path.join(OUT, "book.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=1)
    print("pages", len(doc), "aspect", round(aspect, 4), "outline", len(meta["outline"]))


if __name__ == "__main__":
    main()
