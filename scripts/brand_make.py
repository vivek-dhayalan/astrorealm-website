import math, random
random.seed(7)
C = 256

def star(rv=196, rh=178, w=34):
    """Four-point star with bevelled arms: each arm = a light and a dark facet meeting on the arm's ridge."""
    pts = []
    out = []
    # inner corners at 45°
    ic = {(-1,-1):(C-w, C-w), (1,-1):(C+w, C-w), (1,1):(C+w, C+w), (-1,1):(C-w, C+w)}
    tips = {"n": (C, C-rv), "e": (C+rh, C), "s": (C, C+rv), "w": (C-rh, C)}
    arms = [("n", (-1,-1), (1,-1)), ("e", (1,-1), (1,1)), ("s", (1,1), (-1,1)), ("w", (-1,1), (-1,-1))]
    for name, a, b in arms:
        tx, ty = tips[name]
        ax, ay = ic[a]; bx, by = ic[b]
        out.append(f'<path d="M{tx},{ty} L{ax},{ay} L{C},{C} Z" fill="url(#gLight)"/>')
        out.append(f'<path d="M{tx},{ty} L{bx},{by} L{C},{C} Z" fill="url(#gDark)"/>')
    # fine engraved line along each ridge
    for name in tips:
        tx, ty = tips[name]
        out.append(f'<line x1="{tx}" y1="{ty}" x2="{C}" y2="{C}" stroke="#fff3c4" stroke-opacity=".55" stroke-width="1.6"/>')
    return "\n".join(out)

DEFS = '''<defs>
  <linearGradient id="gGold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#f6dc93"/><stop offset=".45" stop-color="#d4a94f"/><stop offset="1" stop-color="#8c6a2a"/>
  </linearGradient>
  <linearGradient id="gLight" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fbe7a6"/><stop offset="1" stop-color="#d9b25c"/>
  </linearGradient>
  <linearGradient id="gDark" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#c69a42"/><stop offset="1" stop-color="#7d5d22"/>
  </linearGradient>
  <radialGradient id="gSky" cx=".5" cy=".45" r=".6">
    <stop offset="0" stop-color="#1b1f2b"/><stop offset="1" stop-color="#07080c"/>
  </radialGradient>
  <radialGradient id="gPlanet" cx=".34" cy=".38" r=".75">
    <stop offset="0" stop-color="#a9abae"/><stop offset=".55" stop-color="#5d6064"/><stop offset="1" stop-color="#1c1d20"/>
  </radialGradient>
  <linearGradient id="gShade" x1="0" y1="0" x2="1" y2=".25">
    <stop offset=".3" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".85"/>
  </linearGradient>
  <linearGradient id="gRim" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#e8e9eb" stop-opacity=".55"/><stop offset=".5" stop-color="#e8e9eb" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="cPlanet"><circle cx="256" cy="256" r="150"/></clipPath>
</defs>'''

# a greyed-out, Earth-like planet behind the star: grey sphere, faint land masses, night side, a thin lit rim
PLANET = """<g clip-path="url(#cPlanet)">
  <circle cx="256" cy="256" r="150" fill="url(#gPlanet)"/>
  <g fill="#c9cbce" opacity=".3">
    <path d="M150 190c18-30 58-44 88-34 22 8 18 30 40 34 26 5 40 28 28 48-14 22-48 14-60 34-12 20 4 44-18 58-24 15-52-6-58-34-5-24-30-30-34-56-3-18 4-34 14-50z"/>
    <path d="M300 150c22-8 52 0 66 18 10 13 4 30-12 34-18 5-24-14-42-12-20 2-30-10-26-24 2-8 6-13 14-16z"/>
    <path d="M296 296c20-12 50-6 62 14 10 17 0 40-20 48-22 9-36-6-46-24-8-15-10-30 4-38z"/>
    <path d="M196 364c14-6 34-2 40 10 5 11-6 22-22 22-16 0-30-8-28-18 1-6 4-11 10-14z"/>
  </g>
  <circle cx="256" cy="256" r="150" fill="url(#gShade)"/>
</g>
<circle cx="256" cy="256" r="149" fill="none" stroke="url(#gRim)" stroke-width="3"/>"""


def mark(full=True, bg=True):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">', DEFS]
    if bg:
        parts.append('<circle cx="256" cy="256" r="252" fill="url(#gSky)"/>')
    if full and bg:
        dots = []
        for _ in range(46):
            a = random.random()*2*math.pi; r = 40 + random.random()*180
            x, y = C + r*math.cos(a), C + r*math.sin(a)
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{random.choice([0.8,1,1.2,1.6])}" fill="#fff" opacity="{random.uniform(.35,.9):.2f}"/>')
        parts.append("".join(dots))
    if full:
        # crescent behind the star, lit from the left as in the reference
        parts.append(PLANET)
    ring_w = 14 if full else 30
    parts.append(f'<circle cx="256" cy="256" r="{236 if full else 228}" fill="none" stroke="url(#gGold)" stroke-width="{ring_w}"/>')
    parts.append(star(rv=236, rh=236, w=36) if full else star(rv=228, rh=228, w=56))
    parts.append('</svg>')
    return "\n".join(parts)

open("mark.svg","w").write(mark(True))
open("favicon.svg","w").write(mark(False))
open("mark-transparent.svg","w").write(mark(True, bg=False))
