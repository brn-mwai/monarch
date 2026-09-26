"""Place facing dissertation pages into open-book photos so they read as flatbed scans.

Spreads follow the bound book: a verso on the left, the next recto on the right. Each
spread is named by the PDF page number of its left page; 0 leaves the left page blank,
as the inside cover faces the title page. Each page keeps its A4 aspect ratio (scaled
to the page box width, centred vertically) and is multiplied onto the paper so the
photo's shading shows through. The scan look comes from flattened, slightly cool light,
a darker spine shadow, fine sensor grain, a small skew, and a final unsharp mask.

Run with no arguments to build every book, or name books: python make_book_mockups.py maroon
"""

import os
import sys

import fitz
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
THESIS = os.path.join(HERE, "..", "thesis", "dissertation.pdf")
OUT_DIR = os.path.join(HERE, "mockups")
GRAIN_SIGMA = 2.2
SEED = 7

BOOKS = {
    "black": {
        "photo": "book_blank.png",
        "scale": 4,
        "spine_x": 367,
        "book_rows": (97, 640),
        "spine_shadow": 0.32,
        "skew": 0.3,
        "left_page": (30, 104, 362, 632),
        "right_page": (373, 104, 706, 632),
        "spreads": {
            "spread_title": 0,
            "spread_piv_pv_abstract": 4,
            "spread_pvi_pvii_publications": 6,
            "spread_p14_p15_physics": 34,
            "spread_p20_p21_instrument": 40,
            "spread_p32_p33_results": 52,
        },
    },
    "maroon": {
        "photo": "book_maroon.png",
        "scale": 3,
        "spine_x": 512,
        "book_rows": (138, 889),
        "spine_shadow": 0.18,
        "skew": 0.0,
        "left_page": (76, 150, 502, 874),
        "right_page": (518, 150, 944, 874),
        "spreads": {
            "maroon_p30_p31_results": 50,
            "maroon_p32_p33_results": 52,
            "maroon_p34_p35_results": 54,
        },
    },
}


def page_image(doc, pdf_page, width):
    page = doc[pdf_page - 1]
    zoom = 2 * width / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    height = round(width * page.rect.height / page.rect.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def place(book, doc, pdf_page, box, scale):
    x0, y0, x1, y1 = (value * scale for value in box)
    page = page_image(doc, pdf_page, x1 - x0)
    top = y0 + ((y1 - y0) - page.height) // 2
    region = (x0, top, x0 + page.width, top + page.height)
    book.paste(ImageChops.multiply(book.crop(region), page), region[:2])


def scan_light(book, spec):
    scale = spec["scale"]
    flat = ImageEnhance.Color(book).enhance(0.85)
    flat = ImageEnhance.Contrast(flat).enhance(1.06)
    pixels = np.asarray(flat).astype(np.float32)
    columns = np.arange(pixels.shape[1], dtype=np.float32)
    spine = spec["spine_x"] * scale
    shadow = 1 - spec["spine_shadow"] * np.exp(-((columns - spine) / (14 * scale)) ** 2)
    top, bottom = spec["book_rows"]
    pixels[top * scale:bottom * scale] *= shadow[None, :, None]
    pixels *= np.array([0.992, 0.996, 1.0], dtype=np.float32)
    grain = np.random.default_rng(SEED).normal(0, GRAIN_SIGMA, pixels.shape[:2])
    pixels += grain[:, :, None]
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))


def finish(book, skew):
    if skew:
        book = book.rotate(skew, resample=Image.Resampling.BICUBIC, fillcolor=(250, 250, 249))
    return book.filter(ImageFilter.UnsharpMask(radius=1.6, percent=90, threshold=2))


def load_photo(spec):
    photo = Image.open(os.path.join(OUT_DIR, spec["photo"])).convert("RGB")
    scale = spec["scale"]
    photo = photo.resize((photo.width * scale, photo.height * scale), Image.Resampling.LANCZOS)
    return photo.filter(ImageFilter.MedianFilter(7))


def build(spec, doc):
    photo = load_photo(spec)
    for name, left in spec["spreads"].items():
        book = photo.copy()
        if left:
            place(book, doc, left, spec["left_page"], spec["scale"])
        place(book, doc, left + 1, spec["right_page"], spec["scale"])
        out = os.path.join(OUT_DIR, name + ".png")
        finish(scan_light(book, spec), spec["skew"]).save(out)
        print("wrote", out, "pdf pages", left, left + 1)


def main(selected):
    doc = fitz.open(THESIS)
    for key, spec in BOOKS.items():
        if not selected or key in selected:
            build(spec, doc)


if __name__ == "__main__":
    main(sys.argv[1:])
