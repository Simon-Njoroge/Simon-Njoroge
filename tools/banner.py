#!/usr/bin/env python3
"""Draws the profile banner.

A page of small monospace text. The name sits on it in a serif face, and
contour rings spread out from the letters through the text, one character
cell at a time. Every so often a pulse travels outward along the rings.

    pip install fonttools pillow numpy scipy
    python3 tools/banner.py --font path/to/serif.woff --out assets

Writes banner-light.svg and banner-dark.svg. The name is embedded as outlines
and everything else is plain SVG text and CSS, so it renders inside an <img>
on GitHub with no script and no external font.
"""
import argparse
from xml.sax.saxutils import escape

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

NAME = "Simon Njoroge"
ROLE = "MACHINE LEARNING & AI ENGINEER"
PLACE = "NAIROBI · 1°17′S 36°49′E"
PASSAGE = ("i build machine learning systems that ship  "
           "retrieval-augmented llm pipelines  model fine-tuning and evaluation  "
           "fastapi + react products  nairobi  ai for african markets  ").replace(" ", "·")

W = 900                  # canvas width, px
PAD_X = 42               # left / right margin of the character grid
TOP = 26                 # top margin of the character grid
ROWS = 28
FS, CW, CH, BASE = 9, 5.4, 10.0, 7.8      # mono size, cell w/h, baseline in cell
COLS = int((W - 2 * PAD_X) / CW)
NAME_PX = 98             # serif font size
TRACK = -0.004           # tracking, em
RING_START, RING_PITCH, RING_WIDTH, RINGS = 14.0, 27.0, 10.5, 11
SS = 4                   # supersampling for the distance field

THEMES = {
    "light": dict(bg="#F0EEE6", edge="#E3DFD3", ink="#141413", page="#DDDAD0",
                  ring="#99968C", clay="#C96442", label="#6B6A63"),
    "dark": dict(bg="#161614", edge="#2A2925", ink="#F0EEE6", page="#32312D",
                 ring="#7C7A71", clay="#D97757", label="#8F8D85"),
}
MONO = ('ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,'
        '"DejaVu Sans Mono","Liberation Mono",monospace')


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def set_name(font_path):
    """Lay the name out once; return (svg path data, mask at SS resolution)."""
    font = TTFont(font_path)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    upm = font["head"].unitsPerEm
    cap = getattr(font["OS/2"], "sCapHeight", 0) or upm * 0.68
    scale = NAME_PX / upm
    base_y = TOP + ROWS * CH / 2 + cap * scale / 2

    def num(v):
        return f"{v:.1f}".rstrip("0").rstrip(".")

    pen = SVGPathPen(glyphs, ntos=num)
    mask = Image.new("L", (int(COLS * CW * SS), int(ROWS * CH * SS)), 0)
    draw = ImageDraw.Draw(mask)
    pil_font = ImageFont.truetype(font_path, NAME_PX * SS)
    width = sum(glyphs[cmap[ord(ch)]].width / upm + TRACK for ch in NAME) * NAME_PX
    x = (W - width) / 2                                  # centred
    for ch in NAME:
        g = glyphs[cmap[ord(ch)]]
        g.draw(TransformPen(pen, (scale, 0, 0, -scale, x, base_y)))
        draw.text(((x - PAD_X) * SS, (base_y - TOP) * SS), ch, font=pil_font,
                  fill=255, anchor="ls")
        x += (g.width / upm + TRACK) * NAME_PX
    return pen.getCommands(), np.asarray(mask) > 127


def classify(mask):
    """Ring index for every cell (None where the plain page shows)."""
    dist = ndi.distance_transform_edt(~mask) / SS         # px outside the letters
    cw, ch = CW * SS, CH * SS
    cls = [[None] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            d = float(dist[int((r + .5) * ch), int((c + .5) * cw)]) - RING_START
            k = int(d // RING_PITCH)
            if d >= 0 and k < RINGS and d % RING_PITCH < RING_WIDTH:
                cls[r][c] = k
    n = ROWS * COLS
    stream = (PASSAGE * (n // len(PASSAGE) + 1))[:n]
    page = [stream[r * COLS:(r + 1) * COLS] for r in range(ROWS)]
    return page, cls


def layer(page, cls, want, klass):
    """One <g> holding only the cells whose class is `want` (None = plain page)."""
    out = []
    for r, line in enumerate(page):
        s = "".join(ch if cls[r][c] == want else " " for c, ch in enumerate(line)).rstrip()
        if not s:
            continue
        lead = len(s) - len(s.lstrip())
        s = s.lstrip()
        tl = f' textLength="{len(s) * CW:g}"' if len(s) > 1 else ""
        out.append(f'<text x="{PAD_X + lead * CW:g}" y="{TOP + r * CH + BASE:g}"{tl}>'
                   f'{escape(s)}</text>')
    return f'<g class="{klass}">' + "".join(out) + "</g>"


def render(theme, name_path, page, cls):
    t = THEMES[theme]
    H = int(TOP + ROWS * CH + 56)
    css = [
        f'text{{font:{FS}px/1 {MONO};white-space:pre}}',
        f'.p{{fill:{t["page"]}}}',
        '.r{animation:9s linear infinite}',
        f'.l{{font-size:11px;letter-spacing:1.4px;fill:{t["label"]}}}',
        f'.c{{fill:{t["clay"]};animation:b 1.4s steps(1) infinite}}',
        '@keyframes b{50%{opacity:0}}',
        '@media (prefers-reduced-motion:reduce){.r,.c{animation:none}}',
    ]
    for k in range(RINGS):
        col = mix(t["ring"], t["page"], (k / RINGS) ** .8)
        css.append(f'.r{k}{{fill:{col};animation-name:w{k};animation-delay:{1 + k * .22:.2f}s}}')
        css.append(f'@keyframes w{k}{{0%,7%,to{{fill:{col}}}2%{{fill:{t["clay"]}}}}}')
    fy = TOP + ROWS * CH + 32
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" '
        f'height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{NAME}, machine '
        f'learning and AI engineer in Nairobi. The name is set in a serif face on a '
        f'page of small monospace text, with contour rings spreading out from the letters.">',
        '<style>' + "".join(css) + '</style>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" '
        f'fill="{t["bg"]}" stroke="{t["edge"]}"/>',
        layer(page, cls, None, 'p'),
        *[layer(page, cls, k, f'r r{k}') for k in range(RINGS)],
        f'<path fill="{t["ink"]}" d="{name_path}"/>',
        f'<text class="l" x="{PAD_X}" y="{fy}">{escape(ROLE)}<tspan class="c" dx="7">█</tspan></text>',
        f'<text class="l" x="{W - PAD_X}" y="{fy}" text-anchor="end">{PLACE}</text>',
        '</svg>',
    ]) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--font", required=True, help="serif font file (ttf, otf or woff)")
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()
    name_path, mask = set_name(a.font)
    page, cls = classify(mask)
    for theme in THEMES:
        path = f"{a.out}/banner-{theme}.svg"
        svg = render(theme, name_path, page, cls)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(path, len(svg.encode()), "bytes")


if __name__ == "__main__":
    main()
