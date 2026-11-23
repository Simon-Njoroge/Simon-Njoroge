#!/usr/bin/env python3
"""Draws the self-attention figure: a sentence written one token at a time,
each new token drawing arcs back to the earlier tokens it attends to.

    python3 tools/attention.py --out assets

Writes attention-light.svg and attention-dark.svg (SVG + CSS, no script).
"""
import argparse

from banner import MONO, PAD_X, THEMES, W

H = 252
TOKENS = ["Every", "token", "asks", "which", "earlier", "words", "matter", "most"]
# WEIGHTS[i][j]: how much token i attends to earlier token j (illustrative).
WEIGHTS = [
    [],
    [1.0],
    [.25, .75],
    [.10, .30, .60],
    [.05, .15, .20, .60],
    [.05, .10, .10, .25, .50],
    [.05, .10, .25, .10, .10, .40],
    [.05, .05, .10, .10, .10, .15, .45],
]
X0, X1 = 118, W - 118          # centres of the first and last token
ARC_Y, TOKEN_Y = 176, 204
LOOP, STEP, FIRST, HOLD, OUT = 13.0, 1.15, 0.6, 11.6, 12.4


def pct(t):
    return f"{max(0, min(t, LOOP)) / LOOP * 100:.2f}%"


def render(theme):
    t = THEMES[theme]
    n = len(TOKENS)
    xs = [X0 + (X1 - X0) * i / (n - 1) for i in range(n)]
    css = [
        f'text{{font:13px/1 {MONO};fill:{t["label"]};text-anchor:middle}}',
        f'.l{{font-size:11px;letter-spacing:1.4px;text-anchor:start}}',
        '.e{text-anchor:end}',
        f'.a{{fill:none;stroke:{t["clay"]};stroke-linecap:round;stroke-dasharray:1;'
        f'opacity:.5;animation:{LOOP:g}s linear infinite}}',
        f'.t{{animation:{LOOP:g}s linear infinite}}',
        '@media (prefers-reduced-motion:reduce){.a,.t{animation:none}}',
    ]
    body = []
    for i in range(n):
        s = FIRST + (i - 1) * STEP if i else 0.15
        last = i == n - 1
        dim = "" if last else f'{pct(s + STEP + .45)}{{fill:{t["label"]}}}'
        css.append(
            f'@keyframes t{i}{{0%,{pct(s)}{{opacity:0}}'
            f'{pct(s + .25)}{{opacity:1;fill:{t["ink"]}}}'
            f'{pct(s + STEP)}{{fill:{t["ink"]}}}{dim}'
            f'{pct(HOLD)}{{opacity:1}}{pct(OUT)},to{{opacity:0}}}}')
        css.append(f'.t{i}{{animation-name:t{i}}}')
        body.append(f'<circle cx="{xs[i]:.1f}" cy="{ARC_Y}" r="1.6" fill="{t["ring"]}"/>')
        body.append(f'<text class="t t{i}" x="{xs[i]:.1f}" y="{TOKEN_Y}">{TOKENS[i]}</text>')
        if not i:
            continue
        css.append(
            f'@keyframes a{i}{{0%,{pct(s)}{{stroke-dashoffset:1;opacity:1}}'
            f'{pct(s + .6)},{pct(s + STEP)}{{stroke-dashoffset:0;opacity:1}}'
            f'{pct(s + STEP + .45)},{pct(HOLD)}{{stroke-dashoffset:0;opacity:.5}}'
            f'{pct(OUT)},to{{stroke-dashoffset:0;opacity:0}}}}')
        css.append(f'.a{i}{{animation-name:a{i}}}')
        for j, w in enumerate(WEIGHTS[i]):
            if w < .1:
                continue
            h = 24 + 17 * (i - j)
            body.append(
                f'<path class="a a{i}" pathLength="1" stroke-width="{.7 + 3.4 * w:.1f}" '
                f'stroke-opacity="{.3 + .7 * w:.2f}" d="M{xs[i]:.1f} {ARC_Y}C{xs[i]:.1f} '
                f'{ARC_Y - h} {xs[j]:.1f} {ARC_Y - h} {xs[j]:.1f} {ARC_Y}"/>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Self-attention, one head. The '
        f'sentence &quot;{" ".join(TOKENS)}&quot; is written one token at a time, and '
        f'each new token draws arcs back to the earlier tokens it attends to; heavier '
        f'arcs mean more attention.">',
        '<style>' + "".join(css) + '</style>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" '
        f'fill="{t["bg"]}" stroke="{t["edge"]}"/>',
        f'<text class="l" x="{PAD_X}" y="40">SELF-ATTENTION · ONE HEAD</text>',
        f'<text class="l e" x="{W - PAD_X}" y="40">LINE WEIGHT = ATTENTION</text>',
        *body,
        '</svg>',
    ]) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()
    for theme in THEMES:
        path = f"{a.out}/attention-{theme}.svg"
        svg = render(theme)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(path, len(svg.encode()), "bytes")


if __name__ == "__main__":
    main()
