"""SVG chart images: South Indian Rasi/Navamsa grids and KP planet/cusp tables."""
from __future__ import annotations

from html import escape

from ..core.chart import Chart
from ..core.reference import (
    NAKSHATRA_LORDS, NAKSHATRAS, PADA_SPAN, RASHI_LORDS, RASHIS, kp_lords, nakshatra_index, norm360, rashi_index,
)
from . import i18n

# South Indian layout: (row, col) of each rashi in a 4×4 grid; signs are fixed, centre 2×2 is the title.
SOUTH_GRID = {11: (0, 0), 0: (0, 1), 1: (0, 2), 2: (0, 3), 3: (1, 3), 4: (2, 3),
              5: (3, 3), 6: (3, 2), 7: (3, 1), 8: (3, 0), 9: (2, 0), 10: (1, 0)}
PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
NODES = {"Rahu", "Ketu"}

INK = "#1f2933"
MUTED = "#7b8794"
LINE = "#9aa5b1"
ACCENT = "#b44d12"
PAPER = "#fffdf7"
HEAD = "#f3ece0"


def dms(x: float) -> str:
    x = x % 30.0
    d = int(x)
    m_full = (x - d) * 60
    m = int(m_full)
    s = int(round((m_full - m) * 60))
    if s == 60:
        s, m = 0, m + 1
    if m == 60:
        m, d = 0, d + 1
    return f"{d:02d}°{m:02d}′{s:02d}″"


def _t(x, y, text, size=12, fill=INK, weight="normal", anchor="start") -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{escape(str(text))}</text>')


def _planet_label(chart: Chart, name: str, L: dict, with_degree: bool) -> str:
    p = chart.planets[name]
    label = L["planet_short"][name]
    if p.retrograde and name not in NODES:
        label += L["retro"]
    if with_degree:
        label += " " + dms(p.longitude)
    return label


def south_grid(chart: Chart, L: dict, x0: float, y0: float, size: float, title: str, navamsa: bool,
               subtitle: list[str], degrees: bool | None = None) -> str:
    show_deg = (not navamsa) if degrees is None else degrees
    cell = size / 4
    out = [f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>']
    contents: dict[int, list[tuple[str, str]]] = {i: [] for i in range(12)}
    asc = norm360(chart.ascendant)
    asc_sign = int(asc // PADA_SPAN) % 12 if navamsa else rashi_index(asc)
    contents[asc_sign].append((L["lagna_short"] + (" " + dms(asc) if show_deg else ""), ACCENT))
    for name in PLANET_ORDER:
        p = chart.planets[name]
        sign = p.navamsa if navamsa else p.rashi
        contents[sign].append((_planet_label(chart, name, L, show_deg), INK))

    for sign, (r, c) in SOUTH_GRID.items():
        x, y = x0 + c * cell, y0 + r * cell
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="none" stroke="{LINE}"/>')
        items = contents[sign]
        if show_deg:
            sign_fs, fs = 9, (11 if len(items) <= 4 else 9.5)
        else:  # no degrees: larger labels so the chart reads well when printed small
            sign_fs = 11 * cell / 110
            fs = min(18.0, (cell - sign_fs - 10) / max(len(items), 1) - 3)
        out.append(_t(x + cell - 5, y + cell - 6, L["rashi"][RASHIS[sign]], sign_fs, MUTED, anchor="end"))
        for i, (txt, color) in enumerate(items):
            out.append(_t(x + 6, y + fs + 4 + i * (fs + 3), txt, fs, color, "600" if color == ACCENT else "normal"))
    cx, cy = x0 + size / 2, y0 + size / 2
    out.append(f'<rect x="{x0 + cell:.1f}" y="{y0 + cell:.1f}" width="{2 * cell:.1f}" height="{2 * cell:.1f}" fill="{HEAD}" stroke="{LINE}"/>')
    tfs, sfs, lh = (16, 10.5, 15) if show_deg else (21, 13.5, 18)
    out.append(_t(cx, cy - 10 - 8 * (len(subtitle) - 1), title, tfs, INK, "700", "middle"))
    for i, line in enumerate(subtitle):
        out.append(_t(cx, cy + 14 + i * lh - 8 * (len(subtitle) - 1), line, sfs, MUTED, anchor="middle"))
    return "\n".join(out)


def _table(x0, y0, title, headers, widths, rows, L) -> tuple[str, float]:
    rh = 20
    total_w = sum(widths)
    out = [_t(x0, y0, title, 14, INK, "700")]
    y = y0 + 10
    out.append(f'<rect x="{x0}" y="{y}" width="{total_w}" height="{rh}" fill="{HEAD}" stroke="{LINE}"/>')
    cx = x0
    for h, w in zip(headers, widths):
        out.append(_t(cx + 6, y + 14, h, 10.5, INK, "600"))
        cx += w
    for i, row in enumerate(rows):
        yy = y + rh * (i + 1)
        fill = PAPER if i % 2 == 0 else "#ffffff"
        out.append(f'<rect x="{x0}" y="{yy}" width="{total_w}" height="{rh}" fill="{fill}" stroke="{LINE}" stroke-width="0.5"/>')
        cx = x0
        for v, w in zip(row, widths):
            out.append(_t(cx + 6, yy + 14, v, 10.5))
            cx += w
    return "\n".join(out), y + rh * (len(rows) + 1)


def _table_compact(x0, y0, title, headers, widths, rows) -> tuple[str, float]:
    """Narrow table for portrait pages: headers wrap onto two lines, slightly larger body text."""
    hh, rh = 30, 19
    total_w = sum(widths)
    out = [_t(x0, y0, title, 13, INK, "700")]
    y = y0 + 8
    out.append(f'<rect x="{x0}" y="{y}" width="{total_w}" height="{hh}" fill="{HEAD}" stroke="{LINE}"/>')
    cx = x0
    for h, w in zip(headers, widths):
        words = str(h).split(" ", 1)
        if len(words) == 2:
            out.append(_t(cx + 4, y + 12, words[0], 9, INK, "600"))
            out.append(_t(cx + 4, y + 24, words[1], 9, INK, "600"))
        else:
            out.append(_t(cx + 4, y + 18, h, 9, INK, "600"))
        cx += w
    for i, row in enumerate(rows):
        yy = y + hh + rh * i
        fill = PAPER if i % 2 == 0 else "#ffffff"
        out.append(f'<rect x="{x0}" y="{yy}" width="{total_w}" height="{rh}" fill="{fill}" stroke="{LINE}" stroke-width="0.5"/>')
        cx = x0
        for v, w in zip(row, widths):
            out.append(_t(cx + 4, yy + 13.5, v, 10.5))
            cx += w
    return "\n".join(out), y + hh + rh * len(rows)


def kp_tables(kp_chart: Chart, significations: dict[str, list[int]], L: dict, x0: float, y0: float,
              compact: bool = False) -> tuple[str, float]:
    lb = L["labels"]
    sh = lambda p: L["planet_short"][p]  # noqa: E731
    widths = [74, 80, 78, 46, 50, 46, 34, 36, 104] if compact else [96, 100, 90, 84, 104, 80, 56, 56, 254]
    table = (lambda x, y, title, heads, w, rows, _L: _table_compact(x, y, title, heads, w, rows)) if compact else _table
    rows = []
    for name in PLANET_ORDER:
        p = kp_chart.planets[name]
        nm = L["planet"][name] + (" " + L["retro"] if p.retrograde and name not in NODES else "")
        lords = kp_lords(p.longitude)
        rows.append([nm, L["rashi"][RASHIS[p.rashi]], dms(p.longitude), sh(RASHI_LORDS[p.rashi]),
                     sh(lords[0]), sh(lords[1]), sh(lords[2]), sh(lords[3]),
                     ", ".join(map(str, significations.get(name, [])))])
    t1, y = table(x0, y0, lb["kp_planets"],
                   [lb["planet"], lb["sign"], lb["degree"], lb["sign_lord"], lb["star_lord"], lb["sub_lord"],
                    "SS", "SSS", lb["signifies"]],
                   widths, rows, L)
    rows = []
    roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    for i, c in enumerate(kp_chart.cusps):
        lords = kp_lords(c)
        sl = lords[1]
        rows.append([roman[i], L["rashi"][RASHIS[rashi_index(c)]], dms(c), sh(RASHI_LORDS[rashi_index(c)]),
                     sh(lords[0]), sh(sl), sh(lords[2]), sh(lords[3]),
                     ", ".join(map(str, significations.get(sl, []))) + f"  ({sh(sl)})"])
    t2, y2 = table(x0, y + 34, lb["kp_cusps"],
                    [lb["house"], lb["sign"], lb["degree"], lb["sign_lord"], lb["star_lord"], lb["sub_lord"],
                     "SS", "SSS", lb["signifies"]],
                    widths, rows, L)
    return t1 + "\n" + t2, y2


def render(chart: Chart, kp_chart: Chart | None, significations: dict | None, lang: str, include: list[str],
           heading: list[str]) -> str:
    L = i18n.get(lang)
    lb = L["labels"]
    W = 960
    grid = 440
    parts: list[str] = []
    y = 20
    for i, line in enumerate(heading):
        parts.append(_t(20, y + 16 + i * 18, line, 15 if i == 0 else 12, INK if i == 0 else MUTED, "700" if i == 0 else "normal"))
    y += 18 * len(heading) + 16

    m = chart.moon
    sub = [f'{lb["nakshatra"]}: {L["nakshatra"][NAKSHATRAS[m.nakshatra]]} {m.pada}',
           f'{lb["lagna"]}: {L["rashi"][RASHIS[chart.lagna_rashi]]}',
           f'{lb["ayanamsa"]}: {chart.ayanamsa.value} · {chart.position_mode.value}']
    grids = [k for k in ("RASI", "NAVAMSA") if k in include]
    if grids:
        x = 20
        for k in grids:
            nav_lagna = RASHIS[int(norm360(chart.ascendant) // PADA_SPAN) % 12]
            subtitle = sub if k == "RASI" else [f'{lb["lagna"]}: {L["rashi"][nav_lagna]}']
            parts.append(south_grid(chart, L, x, y, grid, lb["rasi" if k == "RASI" else "navamsa"], k == "NAVAMSA",
                                    subtitle))
            x += grid + 40
        y += grid + 40
    if "KP_TABLES" in include and kp_chart is not None:
        tables, y = kp_tables(kp_chart, significations or {}, L, 20, y + 10)
        parts.append(tables)
        y += 20
    H = int(y + 10)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="{L["font"]}">\n<rect width="100%" height="100%" fill="#ffffff"/>\n'
            + "\n".join(parts) + "\n</svg>\n")


# ---------------------------------------------------------------- standalone pieces for web pages
def _wrap(body: str, w: float, h: float, font: str, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" font-family="{escape(font)}" '
            f'role="img" aria-label="{escape(label)}" preserveAspectRatio="xMidYMid meet">\n{body}\n</svg>')


def grid_svg(chart: Chart, lang: str, kind: str = "RASI", degrees: bool | None = None,
             subtitle: list[str] | None = None) -> str:
    """One South Indian chart (RASI or NAVAMSA) as a self-contained, scalable SVG."""
    L = i18n.get(lang)
    lb = L["labels"]
    nav = kind == "NAVAMSA"
    if subtitle is None:
        if nav:
            subtitle = [f'{lb["lagna"]}: {L["rashi"][RASHIS[int(norm360(chart.ascendant) // PADA_SPAN) % 12]]}']
        else:
            m = chart.moon
            subtitle = [f'{lb["nakshatra"]}: {L["nakshatra"][NAKSHATRAS[m.nakshatra]]} {m.pada}',
                        f'{lb["lagna"]}: {L["rashi"][RASHIS[chart.lagna_rashi]]}']
    size = 440
    body = south_grid(chart, L, 2, 2, size - 4, lb["navamsa" if nav else "rasi"], nav, subtitle, degrees)
    return _wrap(body, size, size, L["font"], lb["navamsa" if nav else "rasi"])


def kp_svg(kp_chart: Chart, significations: dict, lang: str, compact: bool = False) -> str:
    """KP planet and cusp tables as a self-contained, scalable SVG (compact = narrow, for portrait A5)."""
    L = i18n.get(lang)
    body, y = kp_tables(kp_chart, significations or {}, L, 4, 18, compact=compact)
    width = (548 + 8) if compact else 928
    return _wrap(body, width, y + 6, L["font"], L["labels"]["kp_planets"])
