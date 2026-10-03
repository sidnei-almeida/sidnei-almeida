#!/usr/bin/env python3
"""Render the README banner as a self-contained SVG.

The name is figlet "ANSI Shadow" art (pyfiglet output pasted below) drawn as
plain rectangles, so it looks identical everywhere regardless of which
monospace font the viewer has. Black background on purpose: the README is
meant to read dark in both GitHub themes.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "readme" / "banner.svg"

ART = """
███████╗██╗██████╗ ███╗   ██╗███████╗██╗
██╔════╝██║██╔══██╗████╗  ██║██╔════╝██║
███████╗██║██║  ██║██╔██╗ ██║█████╗  ██║
╚════██║██║██║  ██║██║╚██╗██║██╔══╝  ██║
███████║██║██████╔╝██║ ╚████║███████╗██║
╚══════╝╚═╝╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝

 █████╗ ██╗     ███╗   ███╗███████╗██╗██████╗  █████╗
██╔══██╗██║     ████╗ ████║██╔════╝██║██╔══██╗██╔══██╗
███████║██║     ██╔████╔██║█████╗  ██║██║  ██║███████║
██╔══██║██║     ██║╚██╔╝██║██╔══╝  ██║██║  ██║██╔══██║
██║  ██║███████╗██║ ╚═╝ ██║███████╗██║██████╔╝██║  ██║
╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝
""".strip("\n").splitlines()

WIDTH = 820
CW, CH = 9.0, 15.0          # cell size
LINE = 3.0                   # shadow stroke thickness
BG, BORDER = "#050505", "#1c1c1c"
BLOCK, SHADOW = "#e4e4e4", "#3a3a3a"
TAG, DIM = "#8a8a8a", "#4a4a4a"

ART_W = max(len(l) for l in ART)
ART_X = (WIDTH - ART_W * CW) / 2
ART_Y = 54
ART_H = len(ART) * CH
TAG_Y = ART_Y + ART_H + 46
HEIGHT = int(TAG_Y + 50)


def r(x, y, w, h, fill):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"/>'


def cell(ch, x, y):
    cx, cy = x + CW / 2, y + CH / 2
    hb = lambda x0, x1: r(x0, cy - LINE / 2, x1 - x0, LINE, SHADOW)     # horizontal bar
    vb = lambda y0, y1: r(cx - LINE / 2, y0, LINE, y1 - y0, SHADOW)     # vertical bar
    if ch == "█":
        return [r(x, y, CW + 0.3, CH + 0.3, BLOCK)]
    if ch == "═":
        return [hb(x, x + CW + 0.3)]
    if ch == "║":
        return [vb(y, y + CH + 0.3)]
    if ch == "╗":
        return [hb(x, cx + LINE / 2), vb(cy - LINE / 2, y + CH + 0.3)]
    if ch == "╔":
        return [hb(cx - LINE / 2, x + CW + 0.3), vb(cy - LINE / 2, y + CH + 0.3)]
    if ch == "╝":
        return [hb(x, cx + LINE / 2), vb(y, cy + LINE / 2)]
    if ch == "╚":
        return [hb(cx - LINE / 2, x + CW + 0.3), vb(y, cy + LINE / 2)]
    return []


def main() -> None:
    shapes = []
    for row, line in enumerate(ART):
        for col, ch in enumerate(line):
            shapes += cell(ch, ART_X + col * CW, ART_Y + row * CH)

    font = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Sidnei Almeida, AI Engineer">
<style>
.tag{{font:500 13px {font};fill:{TAG};letter-spacing:3px}}
.dim{{font:400 11px {font};fill:{DIM};letter-spacing:1px}}
.cur{{animation:blink 1.1s steps(1,end) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style>
<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="6" fill="{BG}" stroke="{BORDER}"/>
<text x="24" y="28" class="dim">~/sidnei-almeida</text>
<text x="{WIDTH - 24}" y="28" class="dim" text-anchor="end">● ● ●</text>
{chr(10).join(shapes)}
<text x="{WIDTH / 2:.0f}" y="{TAG_Y}" class="tag" text-anchor="middle">AI ENGINEER   ·   MODELS THAT LEAVE THE NOTEBOOK<tspan class="cur">▌</tspan></text>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(OUT.parents[2])} ({WIDTH}x{HEIGHT}, {len(shapes)} shapes)")


if __name__ == "__main__":
    main()
