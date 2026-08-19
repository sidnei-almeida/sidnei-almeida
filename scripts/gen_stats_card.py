#!/usr/bin/env python3
"""Render the GitHub summary card used in README.md.

Pulls public profile data straight from the GitHub REST API and writes a light
and a dark SVG. Self-contained on purpose: the third-party card services this
replaces kept going down or running out of API quota.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

USER = "sidnei-almeida"
LIVE_DEMOS = 9  # deployed demos linked in README.md
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "readme"

WIDTH, HEIGHT = 820, 196
LANG_COLORS = {
    "Python": "#3572A5",
    "Jupyter Notebook": "#DA5B0B",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Astro": "#FF5A03",
    "QML": "#44A51C",
    "Shell": "#89E051",
    "TeX": "#3D6117",
    "Vue": "#41B883",
    "Java": "#B07219",
    "C++": "#F34B7D",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Dart": "#00B4AB",
    "Svelte": "#FF3E00",
}
FALLBACK_LANG_COLOR = "#8b949e"

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "panel": "#161b22",
        "border": "#30363d",
        "title": "#79c0ff",
        "value": "#e6edf3",
        "label": "#8b949e",
        "track": "#21262d",
    },
    "light": {
        "bg": "#ffffff",
        "panel": "#f6f8fa",
        "border": "#d0d7de",
        "title": "#0969da",
        "value": "#1f2328",
        "label": "#656d76",
        "track": "#eaeef2",
    },
}


def api(path: str) -> object:
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-readme-card",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collect() -> dict:
    user = api(f"/users/{USER}")

    repos: list[dict] = []
    page = 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    created = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    now = datetime.now(timezone.utc)
    months = (now.year - created.year) * 12 + now.month - created.month

    sources = [r for r in repos if not r.get("fork")]
    languages = Counter(r["language"] for r in sources if r.get("language"))

    return {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "demos": LIVE_DEMOS,
        "months": max(months, 1),
        "languages": languages.most_common(6),
        "language_total": sum(languages.values()),
    }


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render(data: dict, theme_name: str) -> str:
    c = THEMES[theme_name]
    tiles = [
        (data["repos"], "public repos"),
        (data["demos"], "live demos"),
        (data["followers"], "followers"),
        (data["months"], "months building"),
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="GitHub summary for {USER}">',
        "<defs>",
        '<linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#388bfd"/>',
        '<stop offset="35%" stop-color="#8957e5"/>',
        '<stop offset="68%" stop-color="#79c0ff"/>',
        '<stop offset="100%" stop-color="#3fb950"/>',
        "</linearGradient>",
        '<clipPath id="barclip"><rect x="28" y="150" width="764" height="9" rx="4.5"/></clipPath>',
        "</defs>",
        "<style>",
        ".t{font:600 15px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["title"] + "}",
        ".v{font:700 30px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["value"] + "}",
        ".l{font:400 11.5px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["label"] + "}",
        ".g{font:400 11px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["label"] + "}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
        '<rect x="0" y="0" width="820" height="4" fill="url(#accent)"/>',
        '<rect x="0" y="0" width="12" height="4" fill="url(#accent)"/>',
        f'<text x="28" y="42" class="t">GitHub at a glance</text>',
    ]

    for index, (value, label) in enumerate(tiles):
        x = 28 + index * 196
        parts.append(f'<rect x="{x}" y="58" width="176" height="70" rx="10" '
                     f'fill="{c["panel"]}" stroke="{c["border"]}"/>')
        parts.append(f'<text x="{x + 18}" y="94" class="v">{value}</text>')
        parts.append(f'<text x="{x + 18}" y="114" class="l">{esc(label)}</text>')

    total = data["language_total"] or 1
    offset = 28.0
    parts.append(f'<rect x="28" y="150" width="764" height="9" rx="4.5" fill="{c["track"]}"/>')
    parts.append('<g clip-path="url(#barclip)">')
    for name, count in data["languages"]:
        span = 764 * count / total
        color = LANG_COLORS.get(name, FALLBACK_LANG_COLOR)
        parts.append(f'<rect x="{offset:.1f}" y="150" width="{span:.1f}" height="9" fill="{color}"/>')
        offset += span
    parts.append("</g>")

    legend_x = 28
    for name, count in data["languages"]:
        color = LANG_COLORS.get(name, FALLBACK_LANG_COLOR)
        parts.append(f'<circle cx="{legend_x + 4}" cy="177" r="4" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 14}" y="181" class="g">{esc(name)}</text>')
        legend_x += 22 + int(len(name) * 6.1)
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    try:
        data = collect()
    except urllib.error.HTTPError as error:
        print(f"GitHub API failed: {error.code} {error.reason}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        target = OUT_DIR / f"github-stats-{theme}.svg"
        target.write_text(render(data, theme) + "\n", encoding="utf-8")
        print(f"wrote {target.relative_to(OUT_DIR.parent.parent)}")

    print(json.dumps({k: v for k, v in data.items() if k != "languages"}))
    print("languages:", data["languages"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
