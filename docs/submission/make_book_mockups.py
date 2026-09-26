"""Place facing dissertation pages into an open-book photo so it reads as a flatbed scan.

Spreads follow the bound book: an even printed page on the left, the next odd page on
the right. Each page keeps its A4 aspect ratio (scaled to the paper width, centred
vertically) and is multiplied onto the paper so the photo's shading shows through.
The scan look comes from flattened, slightly cool light, a darker spine shadow,
fine sensor grain, a small skew, and a final unsharp mask for crisp text.
"""

import os

import fitz
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "mockups", "book_blank.png")
THESIS = os.path.join(HERE, "..", "thesis", "dissertation.pdf")
OUT_DIR = os.path.join(HERE, "mockups")
SCALE = 4
PRINTED_OFFSET = 20
SPINE_X = 367
BOOK_TOP, BOOK_BOTTOM = 97, 640
SKEW_DEGREES = 0.3
GRAIN_SIGMA = 2.2
SEED = 7

LEFT_PAGE = (30, 104, 362, 632)
RIGHT_PAGE = (373, 104, 706, 632)

SPREADS = {
    "spread_p14_p15_physics": 14,
    "spread_p20_p21_instrument": 20,
    "spread_p32_p33_results": 32,
}


def page_image(doc, printed, width):
    page = doc[printed + PRINTED_OFFSET - 1]
    zoom = 2 * width / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    height = round(width * page.rect.height / page.rect.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def place(book, doc, printed, box):
    x0, y0, x1, y1 = (value * SCALE for value in box)
    page = page_image(doc, printed, x1 - x0)
    top = y0 + ((y1 - y0) - page.height) // 2
    region = (x0, top, x0 + page.width, top + page.height)
    book.paste(ImageChops.multiply(book.crop(region), page), region[:2])


def scan_light(book):
    flat = ImageEnhance.Color(book).enhance(0.85)
    flat = ImageEnhance.Contrast(flat).enhance(1.06)
    pixels = np.asarray(flat).astype(np.float32)
    columns = np.arange(pixels.shape[1], dtype=np.float32)
    spine = SPINE_X * SCALE
    shadow = 1 - 0.32 * np.exp(-((columns - spine) / (14 * SCALE)) ** 2)
    rows = slice(BOOK_TOP * SCALE, BOOK_BOTTOM * SCALE)
    pixels[rows] *= shadow[None, :, None]
    pixels *= np.array([0.992, 0.996, 1.0], dtype=np.float32)
    grain = np.random.default_rng(SEED).normal(0, GRAIN_SIGMA, pixels.shape[:2])
    pixels += grain[:, :, None]
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))


def finish(book):
    skewed = book.rotate(SKEW_DEGREES, resample=Image.Resampling.BICUBIC,
                         fillcolor=(250, 250, 249))
    return skewed.filter(ImageFilter.UnsharpMask(radius=1.6, percent=90, threshold=2))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    photo = Image.open(PHOTO).convert("RGB")
    size = (photo.width * SCALE, photo.height * SCALE)
    photo = photo.resize(size, Image.Resampling.LANCZOS)
    photo = photo.filter(ImageFilter.MedianFilter(7))
    doc = fitz.open(THESIS)
    for old in os.listdir(OUT_DIR):
        if old.startswith("spread_") and old.endswith(".png"):
            os.remove(os.path.join(OUT_DIR, old))
    for name, left in SPREADS.items():
        book = photo.copy()
        place(book, doc, left, LEFT_PAGE)
        place(book, doc, left + 1, RIGHT_PAGE)
        out = os.path.join(OUT_DIR, name + ".png")
        finish(scan_light(book)).save(out)
        print("wrote", out, "pages", left, left + 1)


if __name__ == "__main__":
    main()
