"""
Generate the E2 instance-replication stimuli (AS-2, cspaper review 6 con 3/Q3).

WHY THIS FILE EXISTS. Every image-property level in the paper's hosted-model
table is ONE rendered file. Review 6: *"Stable multi-instance effects would
raise my score."* Answering that needs several INDEPENDENT images per content
level, matched on dimensions so instance is the only thing that moves.

⚠️ THE REVIEWER'S REQUEST IS ONLY HALF WELL-POSED, AND THIS SCRIPT ENCODES THE
HALF THAT IS. They ask for "multiple independently rendered black, white, grey,
caption, and non-caption images at the same dimensions". For CONTENT that is
meaningful: three different caption sentences and three different line drawings
are genuinely three draws from a class. For COLOUR it is degenerate: three
independent renders of a pure-white 512x512 PNG are BYTE-IDENTICAL, so there is
no instance variation to estimate. The instance of a flat colour fill IS the
colour. This script therefore emits content instances only; the colour arms in
the E2 preset are run-to-run replications of the published cells, which is a
different (and separately labelled) claim. Do not describe the colour arms as
instance-replicated.

MATCHING. Captions are 1024x141 with the same margin, font and line pitch as the
published `mountain.png` (measured from its pixels: ink starts x=40, first line
band y=45..71, pitch 34px, DejaVu Sans 28) so all four caption instances differ
only in the sentence. Drawings are 512x512 to match this sweep's reference
canvas, carry no glyphs at all (the non-OCR-able level), and are built from
primitives so they are licence-clean and reproducible in a public repo.

Caption A deliberately re-renders the published mountain sentence through THIS
script rather than reusing mountain.png, so all three caption instances share a
renderer and the only variable is the text.

Regenerate:  .venv/bin/python src/prompt_transformations/image/images/make_instance_images.py
Outputs are COMMITTED — the clusters get them by `git pull`, never by rsync.
"""
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[3]))
from src.prompt_transformations.image.font_utils import (  # noqa: E402
    LATIN_FONTS, get_font_for_text,
)

OUT = _HERE / "instances"

# --- caption geometry, measured from mountain.png (do not "tidy") ------------
CAP_W, CAP_H = 1024, 141
CAP_MARGIN_X = 40
CAP_TOP = 38          # ink of line 1 then starts at y=45 for DejaVu Sans 28
CAP_PITCH = 34
CAP_SIZE = 28
CAP_WRAP = 62         # chars; yields two lines for all three sentences

CAPTIONS = {
    # A = the published mountain sentence, re-rendered here for style parity.
    "caption_a": "A photograph of a mountain landscape with trees and a river under blue sky.",
    "caption_b": "A close-up photograph of a wooden table with a ceramic bowl of fresh fruit.",
    "caption_c": "An illustration of a quiet city street at night with parked cars and lamps.",
}

DRAW_W = DRAW_H = 512
STROKE = 4
BLACK, WHITE = (0, 0, 0), (255, 255, 255)


def make_caption(text: str) -> Image.Image:
    img = Image.new("RGB", (CAP_W, CAP_H), WHITE)
    d = ImageDraw.Draw(img)
    font = get_font_for_text(text, CAP_SIZE, LATIN_FONTS)
    lines = textwrap.wrap(text, width=CAP_WRAP)
    if len(lines) != 2:
        raise ValueError(
            f"caption {text!r} wrapped to {len(lines)} lines, expected 2 — "
            "instances must match the published mountain layout")
    for i, line in enumerate(lines):
        d.text((CAP_MARGIN_X, CAP_TOP + i * CAP_PITCH), line, font=font, fill=BLACK)
    return img


def _draw_house(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([140, 250, 372, 430], outline=BLACK, width=STROKE)      # walls
    d.line([120, 250, 256, 140, 392, 250], fill=BLACK, width=STROKE)    # roof
    d.rectangle([230, 330, 290, 430], outline=BLACK, width=STROKE)      # door
    d.rectangle([170, 290, 215, 335], outline=BLACK, width=STROKE)      # window
    d.rectangle([305, 290, 350, 335], outline=BLACK, width=STROKE)      # window
    d.ellipse([390, 70, 460, 140], outline=BLACK, width=STROKE)         # sun
    for x0, y0, x1, y1 in ((375, 105, 350, 105), (475, 105, 500, 105),
                           (425, 55, 425, 30), (425, 155, 425, 180)):
        d.line([x0, y0, x1, y1], fill=BLACK, width=STROKE)              # rays
    d.line([60, 430, 452, 430], fill=BLACK, width=STROKE)               # ground


def _draw_boat(d: ImageDraw.ImageDraw) -> None:
    d.line([150, 340, 362, 340, 320, 400, 192, 400, 150, 340],
           fill=BLACK, width=STROKE)                                     # hull
    d.line([256, 340, 256, 110], fill=BLACK, width=STROKE)               # mast
    d.line([266, 130, 266, 320, 380, 320, 266, 130],
           fill=BLACK, width=STROKE)                                     # mainsail
    d.line([246, 150, 246, 320, 160, 320, 246, 150],
           fill=BLACK, width=STROKE)                                     # jib
    for k, y in enumerate((430, 462)):                                   # waves
        off = 0 if k == 0 else 26
        for x in range(40 + off, 480, 104):
            d.arc([x, y - 16, x + 52, y + 16], 180, 360, fill=BLACK, width=STROKE)
            d.arc([x + 52, y - 16, x + 104, y + 16], 0, 180, fill=BLACK, width=STROKE)


def _draw_tree(d: ImageDraw.ImageDraw) -> None:
    d.line([236, 430, 236, 250], fill=BLACK, width=STROKE)               # trunk
    d.line([276, 430, 276, 250], fill=BLACK, width=STROKE)
    d.line([236, 300, 170, 250], fill=BLACK, width=STROKE)               # branches
    d.line([276, 290, 345, 235], fill=BLACK, width=STROKE)
    d.ellipse([120, 90, 392, 285], outline=BLACK, width=STROKE)          # canopy
    d.ellipse([175, 60, 340, 175], outline=BLACK, width=STROKE)
    d.line([60, 430, 452, 430], fill=BLACK, width=STROKE)                # ground
    d.ellipse([330, 380, 372, 422], outline=BLACK, width=STROKE)         # a stone
    d.ellipse([110, 396, 140, 426], outline=BLACK, width=STROKE)


DRAWINGS = {
    "drawing_a_house": _draw_house,
    "drawing_b_boat": _draw_boat,
    "drawing_c_tree": _draw_tree,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, text in CAPTIONS.items():
        p = OUT / f"{name}.png"
        make_caption(text).save(p)
        made.append(p)
    for name, fn in DRAWINGS.items():
        img = Image.new("RGB", (DRAW_W, DRAW_H), WHITE)
        fn(ImageDraw.Draw(img))
        p = OUT / f"{name}.png"
        img.save(p)
        made.append(p)
    for p in made:
        im = Image.open(p)
        print(f"{p.relative_to(_HERE.parents[3])}  {im.size}  {p.stat().st_size} B")


if __name__ == "__main__":
    main()
