#!/usr/bin/env python3
"""Render the contribution calendar used in README.md.

Pulls the contribution calendar from the GitHub GraphQL API and writes a light
and a dark SVG. Self-contained on purpose: the third-party activity graph this
replaces rendered "Can't fetch any contribution. Please check your username"
instead of a graph.

Needs GITHUB_TOKEN in the environment (GraphQL rejects anonymous requests).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

USER = "sidnei-almeida"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "readme"

WIDTH = 820
PAD = 28
GRID_LEFT = PAD + 26  # room for the weekday labels
GRID_TOP = 72
STEP = 14.4
CELL = 11.4
HEIGHT = 218

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "title": "#79c0ff",
        "value": "#e6edf3",
        "label": "#8b949e",
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "cell_stroke": "#ffffff12",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "title": "#0969da",
        "value": "#1f2328",
        "label": "#656d76",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "cell_stroke": "#1f232812",
    },
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
  }
}
"""


def collect() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required: the GraphQL API rejects anonymous requests")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER}-readme-card",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if payload.get("errors"):
        raise SystemExit(f"GraphQL errors: {payload['errors']}")

    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [week["contributionDays"] for week in calendar["weeks"]]
    if not weeks:
        raise SystemExit("GraphQL returned an empty calendar")

    return {"total": calendar["totalContributions"], "weeks": weeks}


def thresholds(weeks: list[list[dict]]) -> list[int]:
    """Quartiles of the active days, the way GitHub buckets its own calendar.

    Scaling against the peak day instead washes the whole year out whenever a
    single day spikes.
    """
    active = sorted(
        day["contributionCount"]
        for week in weeks
        for day in week
        if day["contributionCount"] > 0
    )
    if not active:
        return [1, 2, 3]
    return [max(1, active[int(len(active) * q)] if q < 1 else active[-1])
            for q in (0.25, 0.5, 0.75)]


def level(count: int, cuts: list[int]) -> int:
    if count <= 0:
        return 0
    for index, cut in enumerate(cuts):
        if count <= cut:
            return index + 1
    return 4


def month_labels(weeks: list[list[dict]]) -> list[tuple[int, str]]:
    """First week column of each month, skipping a stub leading month."""
    labels: list[tuple[int, str]] = []
    seen: int | None = None
    for index, days in enumerate(weeks):
        month = datetime.strptime(days[0]["date"], "%Y-%m-%d").month
        if month != seen:
            seen = month
            if index == 0 and len(weeks) > 1:
                continue
            if labels and index - labels[-1][0] < 3:
                continue
            labels.append((index, MONTHS[month - 1]))
    return labels


def render(data: dict, theme_name: str) -> str:
    c = THEMES[theme_name]
    weeks = data["weeks"]
    peak = max((day["contributionCount"] for week in weeks for day in week), default=0)
    cuts = thresholds(weeks)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="Contribution calendar for {USER}: '
        f'{data["total"]} contributions in the last year">',
        "<defs>",
        '<linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%" stop-color="#388bfd"/>',
        '<stop offset="35%" stop-color="#8957e5"/>',
        '<stop offset="68%" stop-color="#79c0ff"/>',
        '<stop offset="100%" stop-color="#3fb950"/>',
        "</linearGradient>",
        "</defs>",
        "<style>",
        ".t{font:600 15px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["title"] + "}",
        ".n{font:600 13px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["value"] + "}",
        ".l{font:400 10.5px 'Segoe UI',Ubuntu,Helvetica,Sans-Serif;fill:" + c["label"] + "}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
        f'<rect x="0" y="0" width="{WIDTH}" height="4" fill="url(#accent)"/>',
        f'<text x="{PAD}" y="42" class="t">Contribution activity</text>',
        f'<text x="{WIDTH - PAD}" y="42" class="n" text-anchor="end">'
        f'{data["total"]} contributions in the last year</text>',
    ]

    for index, name in month_labels(weeks):
        x = GRID_LEFT + index * STEP
        parts.append(f'<text x="{x:.1f}" y="{GRID_TOP - 8}" class="l">{name}</text>')

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = GRID_TOP + row * STEP + CELL - 2
        parts.append(f'<text x="{PAD}" y="{y:.1f}" class="l">{name}</text>')

    for index, days in enumerate(weeks):
        x = GRID_LEFT + index * STEP
        for day in days:
            y = GRID_TOP + day["weekday"] * STEP
            fill = c["levels"][level(day["contributionCount"], cuts)]
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{fill}" stroke="{c["cell_stroke"]}"/>'
            )

    legend_y = GRID_TOP + 7 * STEP + 20
    legend_x = WIDTH - PAD - 5 * 16 - 74
    parts.append(f'<text x="{legend_x:.1f}" y="{legend_y + 9:.1f}" class="l">Less</text>')
    for step, color in enumerate(c["levels"]):
        x = legend_x + 30 + step * 16
        parts.append(
            f'<rect x="{x:.1f}" y="{legend_y:.1f}" width="11.4" height="11.4" rx="2.5" '
            f'fill="{color}" stroke="{c["cell_stroke"]}"/>'
        )
    parts.append(
        f'<text x="{legend_x + 30 + 5 * 16 + 4:.1f}" y="{legend_y + 9:.1f}" class="l">More</text>'
    )
    parts.append(f'<text x="{PAD}" y="{legend_y + 9:.1f}" class="l">'
                 f'Peak day: {peak} contributions</text>')
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
        target = OUT_DIR / f"contrib-graph-{theme}.svg"
        target.write_text(render(data, theme) + "\n", encoding="utf-8")
        print(f"wrote {target.relative_to(OUT_DIR.parent.parent)}")

    print(json.dumps({"total": data["total"], "weeks": len(data["weeks"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
