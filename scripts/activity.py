import re
import sys
import urllib.request
from datetime import date

USER = "n0tmar"
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/activity.svg"

SANS = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
JP = "'Yu Gothic UI', 'Hiragino Sans', 'Noto Sans JP', 'Meiryo', sans-serif"
LEVELS = ["#1a1a1a", "#333333", "#666666", "#a8a8a8", "#ffffff"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    cells = {}
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
        d = re.search(r'data-date="([\d-]+)"', tag)
        lvl = re.search(r'data-level="(\d)"', tag)
        cid = re.search(r'id="([^"]+)"', tag)
        if d and lvl and cid:
            cells[cid.group(1)] = [date.fromisoformat(d.group(1)), int(lvl.group(1)), 0]
    for cid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"([\d,]+) contribution", text)
        if cid in cells and m:
            cells[cid][2] = int(m.group(1).replace(",", ""))
    return sorted(cells.values(), key=lambda c: c[0])


def render(days):
    cell, gap = 16, 4
    left, top = 70, 92
    first = days[0][0]
    offset = (first.weekday() + 1) % 7
    weeks = (len(days) + offset + 6) // 7
    w = left + weeks * (cell + gap) + 50
    h = top + 7 * (cell + gap) + 60
    total = sum(c[2] for c in days)
    streak = best = 0
    for c in days:
        streak = streak + 1 if c[2] else 0
        best = max(best, streak)
    active = sum(1 for c in days if c[2])

    rects, labels, last_month = [], [], None
    for i, (d, lvl, _) in enumerate(days):
        col, row = divmod(i + offset, 7)
        x, y = left + col * (cell + gap), top + row * (cell + gap)
        start = col / weeks * 0.6
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{LEVELS[lvl]}">'
            f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{start:.3f};{start + 0.4:.3f}" dur="2.2s" fill="freeze"/>'
            f'</rect>'
        )
        if row == 0 and d.month != last_month and col < weeks - 2:
            labels.append(f'<text x="{x}" y="{top - 12}" font-family="{SANS}" font-size="13" fill="#9a9a9a">{MONTHS[d.month - 1]}</text>')
            last_month = d.month

    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        labels.append(f'<text x="{left - 14}" y="{top + row * (cell + gap) + 12}" text-anchor="end" font-family="{SANS}" font-size="12" fill="#9a9a9a">{name}</text>')

    legend_x = w - 50 - 5 * (cell + gap) - 70
    legend = [f'<text x="{legend_x - 10}" y="{h - 26}" text-anchor="end" font-family="{SANS}" font-size="12" fill="#9a9a9a">Less</text>']
    for i, color in enumerate(LEVELS):
        legend.append(f'<rect x="{legend_x + i * (cell + gap)}" y="{h - 39}" width="{cell}" height="{cell}" rx="4" fill="{color}"/>')
    legend.append(f'<text x="{legend_x + 5 * (cell + gap) + 6}" y="{h - 26}" font-family="{SANS}" font-size="12" fill="#9a9a9a">More</text>')

    stats = f"{total:,} contributions  ·  {active} active days  ·  {best} day best streak"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#111111"/><stop offset="1" stop-color="#0a0a0a"/>
</linearGradient>
</defs>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#bg)" stroke="#2a2a2a"/>
<text x="{left}" y="44" font-family="{SANS}" font-size="16" font-weight="600" fill="#ffffff">{stats}</text>
<text x="{w - 50}" y="44" text-anchor="end" font-family="{JP}" font-size="14" letter-spacing="4" fill="#ffffff" opacity="0.8">一年の記録</text>
{"".join(labels)}
{"".join(rects)}
<text x="{left}" y="{h - 26}" font-family="{SANS}" font-size="12" fill="#9a9a9a">Updated {date.today():%B %d, %Y}</text>
{"".join(legend)}
</svg>
'''


with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(render(fetch()))
