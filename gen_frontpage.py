#!/usr/bin/env python3
"""Draws the 18 November 2026 front page for make.fun news-image-20261118.

One image, 1024x1024, summing up Wednesday 18 November 2026 in world news:
a masthead naming the day, 11 featured stories with flat illustrations,
a world map with numbered pins, and 24 one-line briefs — 35 stories, 6
continents. Every headline is drawn with PIL from the verified story list
in news-notes.md, so the text is exactly as written and legible.

Usage: python3 gen_frontpage.py [variant ...]  (no args = all variants)
Output: candidates/<variant>.png next to this script.
Deterministic: same inputs -> same bytes (no time, no randomness).
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "candidates")
os.makedirs(OUT, exist_ok=True)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def wrap(text, fnt, max_w):
    """Greedy word wrap to a pixel width."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if fnt.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_tracked(d, xy, text, fnt, fill, tracking=1):
    """Draw text with extra pixels between characters (letterspaced caps)."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + tracking
    return x


def text_w(fnt, text, tracking=0):
    return fnt.getlength(text) + tracking * max(0, len(text) - 1)


# ---------------------------------------------------------------- stories
# (n, region, beat, headline, deck, illustration)
FEATURED = [
    (1, "MIDDLE EAST", "IRAN WAR",
     "Iran strikes Kuwait and Bahrain after US hits Qeshm Island",
     "US jets hit a missile site on Qeshm; Iran answered by striking "
     "Kuwait and Bahrain.",
     "gulf"),
    (2, "EUROPE", "UKRAINE WAR",
     "Kerch Bridge span falls into the sea",
     "Ukraine hit the Crimea bridge again; part of its road span fell "
     "into the sea.",
     "bridge"),
    (3, "ASIA", "DIPLOMACY",
     "Trump, Xi and Putin to meet in Shenzhen",
     "Xi and Putin opened APEC in Shenzhen; a three-way summit with Trump "
     "follows.",
     "summit"),
    (4, "UNITED STATES", "POLITICS",
     "Peltola wins Alaska; Democrats take 56-44 Senate",
     "Peltola beat Sen. Dan Sullivan (R); largest majority since 2009.",
     "ballot"),
    (5, "AFRICA", "HEALTH",
     "Ebola in DR Congo passes 11,000 cases",
     "Doubled in three months; 5,400 dead; children hit hardest.",
     "ebola"),
    (6, "SCIENCE", "SPACE",
     "Voyager 1 reaches one light-day from Earth",
     "16 billion miles out — no human-made object has gone farther.",
     "voyager"),
    (7, "UNITED STATES", "HEALTH",
     "US loses measles-free status after 26 years",
     "5,412 cases in 2026, 10 deaths, 45 states; held since 2000.",
     "measles"),
    (8, "EUROPE", "DISASTER",
     "Russian military plane crashes in Siberia, 19 dead",
     "An An-12 went down in Kemerovo; all aboard were killed.",
     "plane"),
    (9, "MARKETS", "ECONOMY",
     "Stocks fall as Gulf fighting rattles markets",
     "S&P 500 -1.03%, FTSE -1.76%, DAX -2.08%; Brent $92.47.",
     "markets"),
    (10, "ASIA", "WEATHER",
     "Category 5 Cyclone Xavier hits Cook Islands",
     "Gusts to 315 km/h over the Northern Cook Islands.",
     "cyclone"),
    (11, "GLOBAL", "TECHNOLOGY",
     "Tech outages hit US banks, flights and the NSA",
     "An NSA network went down — the eighth US outage in a week.",
     "outages"),
]

# (n, region, one-liner) — 24 briefs, stories 12..35. Kept short so each
# fits on one line in a ~270px column at ~11.5px.
BRIEFS = [
    (12, "Gaza", "ceasefire may collapse, board warns"),
    (13, "Israel", "Kahana elected Knesset speaker"),
    (14, "Yemen", "five drones fired at Saudi pipeline"),
    (15, "Russia", 'Putin "not ready" for peace talks'),
    (16, "Germany", 'US criticism of strikes "stupid"'),
    (17, "Ethiopia–Eritrea", "armies mass on border"),
    (18, "Myanmar", "president to review ASEAN ties"),
    (19, "UK", "US spy suspect moved to US custody"),
    (20, "France", "140,000 join pay protests"),
    (21, "Turkey", "government takes over Sozcu TV"),
    (22, "Serbia", "student-list majority opens parliament"),
    (23, "EU", "migrant return hubs planned in Rwanda"),
    (24, "New York", "27 years for plot to kill Trump"),
    (25, "Manila", "Trump meets Marcos Jr., Quad allies"),
    (26, "South Korea", "2027 growth forecast up to 3.9%"),
    (27, "France–Malaysia", "rare-earths partnership"),
    (28, "Brazil", "real falls on Lula fiscal plan"),
    (29, "Pakistan", "rooftop solar share hits 28%"),
    (30, "US", 'Kalshi halts "mention" markets'),
    (31, "Nvidia", "Huang would return; board says no"),
    (32, "Culture", '"human" is word of the year'),
    (33, "Culture", "Fela Kuti joins Rock Hall of Fame"),
    (34, "Sport", "Zverev into ATP Finals knockouts"),
    (35, "Earthquakes", "6.0 in PNG; 5.3 in Romania"),
]

# (n, map-col, map-row) for the featured stories that have a place on Earth.
# Map grid: 100 cols (lon -180..180), 46 rows (lat 78..-52). Story 6 (Voyager)
# is in space and gets a star note under the map instead of a pin.
PINS = {
    1: (66, 18),   # Gulf / Qeshm
    2: (60, 11),   # Kerch Bridge
    3: (82, 19),   # Shenzhen
    4: (8, 5),     # Alaska
    5: (57, 28),   # DR Congo
    7: (23, 13),   # United States
    8: (74, 8),    # Kemerovo, Siberia
    9: (50, 9),    # London (markets)
    10: (6, 34),   # Cook Islands
    11: (29, 13),  # Washington DC
}
# Small dots for a few briefs (col, row).
DOTS = [(59, 16), (63, 22), (61, 24), (77, 19), (51, 11), (60, 13),
        (36, 30), (69, 17), (91, 29), (57, 11), (85, 14), (61, 16)]

# Hand-drawn world map, 100 cols x 46 rows ('#' = land). Coarse but the
# continents must read at a glance: Americas left, Europe/Africa centre,
# Asia right, Australia bottom-right.
MAP_ROWS = [
    "            ####                    #######            #                  ####",
    "    ####### ###############       ###########                 ###################################",
    "    ###########################   ##########          ###    ######################################",
    "    #############################  ########          #####   #######################################",
    "    ##############################  ######           #####   #######################################",
    "     #############################           #      ######    ######################################",
    "      ############################             #    #####     ######################################",
    "       ###########################             ## ########### #####################################",
    "        #########################               #################################################",
    "         ########################               ###############################################",
    "          ######################                ############# ###############################",
    "           #####################                ############# #############################",
    "            ###################                #############  ###########################",
    "             ##################                 ###########    ########################",
    "              ################                   #########  #########################",
    "               ##############                 ############### ######################",
    "               #############                  #####################################",
    "                ###########                   ################# ##################",
    "                ##########                    ################       ######  ####",
    "                 #########                    ###############        #####   ####",
    "                   #######                     ##############         ####   ###",
    "                      #####                    #############          ###    ###",
    "                        ####                    ############          ###     #####",
    "                            ############        ###########                   ###########",
    "                            #############        ##########                     ###########",
    "                            #############        #########                        #########",
    "                             ###########          ########",
    "                             ###########          #######",
    "                              ##########           ######                         ##########",
    "                              #########            ######                        ############",
    "                              #########             #####                        ############",
    "                               #######              ####                          ###########",
    "                               #######              ####                          ##########",
    "                                ######               ###                           #########",
    "                                #####                ###                            #######",
    "                                #####                 ##                             #####",
    "                                 ####                                                ####      #",
    "                                 ###                                                           #",
    "                                 ###",
    "                                 ###",
    "                                  ##",
    "                                  ##",
    "                                  #",
    "                                  #",
    "",
    "",
]

# ---------------------------------------------------------------- illustrations
# Flat, simple scenes in the winning front page's style. Each draws inside
# the box (x, y, w, h) on draw object d. No text smaller than 9px.


def _star(d, cx, cy, r, color):
    pts = []
    for i in range(8):
        ang = i * 3.14159 / 4
        rr = r if i % 2 == 0 else r * 0.38
        pts.append((cx + rr * 1.6 * (1 if i % 4 in (0, 1) else -1) * 0.7,
                    cy + rr * (1 if i < 4 else -1) * 0.7))
    # simpler: 4-point starburst from lines
    d.line([cx - r, cy, cx + r, cy], fill=color, width=max(2, r // 4))
    d.line([cx, cy - r, cx, cy + r], fill=color, width=max(2, r // 4))
    d.line([cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7],
           fill=color, width=max(2, r // 5))
    d.line([cx - r * 0.7, cy + r * 0.7, cx + r * 0.7, cy - r * 0.7],
           fill=color, width=max(2, r // 5))
    d.ellipse([cx - r // 3, cy - r // 3, cx + r // 3, cy + r // 3], fill=color)


def _pill(d, x, y, text, fnt, fg, bg):
    tw = fnt.getlength(text)
    pad = 6
    h = fnt.size + 7
    d.rounded_rectangle([x, y, x + tw + pad * 2, y + h], radius=h // 2, fill=bg)
    d.text((x + pad, y + 3), text, font=fnt, fill=fg)
    return tw + pad * 2


def _flag_us(d, x, y, w, h):
    for i in range(7):
        d.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                    fill="#b22234" if i % 2 == 0 else "#ffffff")
    d.rectangle([x, y, x + w * 0.42, y + h * 4 / 7], fill="#3c3b6e")
    for r in range(3):
        for c in range(4):
            d.ellipse([x + 3 + c * w * 0.09, y + 3 + r * h * 0.17,
                       x + 6 + c * w * 0.09, y + 6 + r * h * 0.17], fill="white")


def _flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill="#de2910")
    _star(d, x + w * 0.22, y + h * 0.28, max(3, h // 6), "#ffde00")
    for sx, sy in [(0.55, 0.18), (0.68, 0.32), (0.68, 0.52), (0.55, 0.66)]:
        _star(d, x + w * sx, y + h * sy, max(2, h // 10), "#ffde00")


def _flag_ru(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h / 3], fill="#ffffff")
    d.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill="#0039a6")
    d.rectangle([x, y + 2 * h / 3, x + w, y + h], fill="#d52b1e")


def illu_gulf(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#efe3c2")
    d.rectangle([x, y + h * 0.45, x + w, y + h], fill="#7fb3d5")
    d.rectangle([x, y + h * 0.45, x + w, y + h * 0.52], fill="#5b8db0")
    # land masses: Arabia below-left, Iran above-right
    d.polygon([(x, y + h * 0.45), (x + w * 0.42, y + h * 0.45),
               (x + w * 0.34, y + h), (x, y + h)], fill="#e0c896")
    d.polygon([(x + w * 0.55, y), (x + w, y), (x + w, y + h * 0.45),
               (x + w * 0.62, y + h * 0.45)], fill="#d9bd8a")
    _star(d, x + w * 0.30, y + h * 0.60, 11, "#e8862e")
    _star(d, x + w * 0.68, y + h * 0.68, 9, "#e8862e")
    _star(d, x + w * 0.52, y + h * 0.32, 8, "#c0392b")
    # drone: small dark diamond + dashed path
    for i in range(5):
        px = x + w * (0.12 + i * 0.05)
        py = y + h * (0.72 - i * 0.06)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill="#333333")
    _pill(d, x + 6, y + 6, "QESHM", font(SANS_B, 10), "#ffffff", "#333333")
    _pill(d, x + w - 62, y + h - 22, "KUWAIT", font(SANS_B, 10), "#ffffff", "#8e2f2f")


def illu_bridge(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#dfe8ee")
    d.rectangle([x, y + h * 0.62, x + w, y + h], fill="#5b8db0")
    d.rectangle([x, y + h * 0.62, x + w, y + h * 0.68], fill="#9fc3d8")
    # towers
    d.rectangle([x + w * 0.16, y + h * 0.18, x + w * 0.20, y + h * 0.62], fill="#3a3a3a")
    d.rectangle([x + w * 0.78, y + h * 0.18, x + w * 0.82, y + h * 0.62], fill="#3a3a3a")
    # deck, left + right, middle span dropped
    d.rectangle([x, y + h * 0.40, x + w * 0.44, y + h * 0.46], fill="#3a3a3a")
    d.rectangle([x + w * 0.56, y + h * 0.40, x + w, y + h * 0.46], fill="#3a3a3a")
    d.polygon([(x + w * 0.45, y + h * 0.42), (x + w * 0.55, y + h * 0.42),
               (x + w * 0.52, y + h * 0.62), (x + w * 0.47, y + h * 0.66)],
              fill="#555555")
    # splash + smoke
    for cx, cy, r in [(0.50, 0.66, 9), (0.46, 0.60, 7), (0.55, 0.62, 6)]:
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r, y + h * cy + r],
                  fill="#eaf4f9")
    for cx, cy, r in [(0.30, 0.30, 8), (0.34, 0.24, 6), (0.27, 0.22, 5)]:
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r, y + h * cy + r],
                  fill="#9aa5ad")


def illu_summit(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#f6ead0")
    fw, fh = w * 0.20, h * 0.42
    for i, fn in enumerate((_flag_us, _flag_cn, _flag_ru)):
        fx = x + w * (0.10 + i * 0.32)
        d.rectangle([fx + fw / 2 - 1, y + h * 0.10, fx + fw / 2 + 1, y + h * 0.62],
                    fill="#7a6a4f")
        fn(d, fx, y + h * 0.10, fw, fh)
    d.ellipse([x + w * 0.06, y + h * 0.62, x + w * 0.94, y + h * 0.86], fill="#8a6d3b")
    d.ellipse([x + w * 0.10, y + h * 0.64, x + w * 0.90, y + h * 0.80], fill="#a98548")
    _pill(d, x + w * 0.32, y + h - 24, "APEC · SHENZHEN", font(SANS_B, 10),
          "#ffffff", "#1f4e79")


def illu_ballot(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#eef3f7")
    d.rectangle([x + w * 0.14, y + h * 0.42, x + w * 0.62, y + h * 0.92], fill="#1f4e79")
    d.rectangle([x + w * 0.14, y + h * 0.42, x + w * 0.62, y + h * 0.55], fill="#2e6da4")
    d.rectangle([x + w * 0.30, y + h * 0.46, x + w * 0.46, y + h * 0.51], fill="#0e2a4a")
    d.polygon([(x + w * 0.30, y + h * 0.46), (x + w * 0.38, y + h * 0.14),
               (x + w * 0.52, y + h * 0.20), (x + w * 0.46, y + h * 0.51)],
              fill="#ffffff", outline="#999999")
    d.ellipse([x + w * 0.66, y + h * 0.10, x + w * 0.94, y + h * 0.48], fill="#1e6b4a")
    d.line([x + w * 0.72, y + h * 0.30, x + w * 0.78, y + h * 0.38,
            x + w * 0.90, y + h * 0.18], fill="#ffffff", width=5)
    _pill(d, x + w * 0.58, y + h - 24, "56–44", font(SANS_B, 12), "#ffffff", "#b01e24")


def illu_ebola(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#fbf0e6")
    d.rectangle([x + 6, y + 6, x + 30, y + 30], fill="#b01e24")
    d.rectangle([x + 14, y + 10, x + 22, y + 26], fill="#ffffff")
    d.rectangle([x + 10, y + 14, x + 26, y + 22], fill="#ffffff")
    for cx, cy, r in [(0.62, 0.45, 22), (0.28, 0.66, 15), (0.84, 0.70, 12)]:
        px, py = x + w * cx, y + h * cy
        for k in range(10):
            import math
            a = k * 3.14159 / 5
            d.line([px + r * 0.9 * math.cos(a), py + r * 0.9 * math.sin(a),
                    px + r * 1.35 * math.cos(a), py + r * 1.35 * math.sin(a)],
                   fill="#8e2f2f", width=3)
        d.ellipse([px - r, py - r, px + r, py + r], fill="#b01e24")
        d.ellipse([px - r * 0.45, py - r * 0.45, px + r * 0.2, py + r * 0.2],
                  fill="#d96a6a")


def illu_voyager(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#0b1e3a")
    for sx, sy, r in [(0.08, 0.14, 2), (0.22, 0.08, 1), (0.38, 0.20, 2), (0.55, 0.10, 1),
                      (0.72, 0.18, 2), (0.88, 0.08, 1), (0.94, 0.30, 2), (0.12, 0.38, 1),
                      (0.48, 0.32, 1), (0.66, 0.38, 2)]:
        d.ellipse([x + w * sx - r, y + h * sy - r, x + w * sx + r, y + h * sy + r],
                  fill="#ffffff")
    d.ellipse([x - w * 0.18, y + h * 0.62, x + w * 0.30, y + h * 0.98], fill="#2e6da4")
    d.ellipse([x + w * 0.04, y + h * 0.72, x + w * 0.14, y + h * 0.88], fill="#3f9e57")
    d.ellipse([x + w * 0.18, y + h * 0.82, x + w * 0.25, y + h * 0.93], fill="#3f9e57")
    # dashed trajectory
    for i in range(9):
        t = i / 8
        px = x + w * (0.30 + t * 0.55)
        py = y + h * (0.78 - t * 0.55) + 6 * t * t * h / 100
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill="#e8c15a")
    px, py = x + w * 0.78, y + h * 0.24
    d.rectangle([px - 12, py - 8, px + 12, py + 8], fill="#e8c15a")
    d.polygon([(px + 12, py - 8), (px + 26, py - 18), (px + 26, py + 2)], fill="#f5e6b8")
    d.line([px - 12, py, px - 30, py + 8], fill="#e8c15a", width=3)
    d.text((x + 8, y + 6), "16 BN MILES", font=font(SANS_B, 11), fill="#e8c15a")


def illu_measles(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#fbf3e8")
    for cx, cy, r in [(0.16, 0.24, 7), (0.30, 0.16, 5), (0.44, 0.28, 8), (0.60, 0.18, 5),
                      (0.74, 0.30, 7), (0.88, 0.20, 5), (0.22, 0.44, 5), (0.86, 0.46, 6),
                      (0.10, 0.62, 5), (0.92, 0.64, 5)]:
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r, y + h * cy + r],
                  fill="#c0392b")
    d.text((x + w * 0.5, y + h * 0.30), "5,412", font=font(SERIF_B, 28),
           fill="#b01e24", anchor="ma")
    d.text((x + w * 0.5, y + h * 0.30 + 32), "CASES IN 2026", font=font(SANS_B, 10),
           fill="#7a1f1f", anchor="ma")


def illu_plane(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#dfe7ee")
    d.polygon([(x, y + h), (x + w * 0.30, y + h * 0.34), (x + w * 0.62, y + h)],
              fill="#ffffff")
    d.polygon([(x + w * 0.45, y + h), (x + w * 0.75, y + h * 0.44), (x + w, y + h)],
              fill="#c9d4dc")
    d.polygon([(x + w * 0.14, y + h * 0.34), (x + w * 0.56, y + h * 0.50),
               (x + w * 0.62, y + h * 0.58), (x + w * 0.26, y + h * 0.48)],
              fill="#333333")
    d.polygon([(x + w * 0.30, y + h * 0.40), (x + w * 0.38, y + h * 0.26),
               (x + w * 0.46, y + h * 0.44)], fill="#333333")
    d.polygon([(x + w * 0.48, y + h * 0.46), (x + w * 0.54, y + h * 0.38),
               (x + w * 0.60, y + h * 0.50)], fill="#333333")
    for cx, cy, r in [(0.62, 0.52, 9), (0.66, 0.44, 7), (0.60, 0.40, 6), (0.70, 0.36, 5)]:
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r, y + h * cy + r],
                  fill="#8a949c")
    _pill(d, x + 6, y + 6, "19 DEAD", font(SANS_B, 10), "#ffffff", "#333333")


def illu_markets(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#101c2e")
    for gy in (0.25, 0.50, 0.75):
        d.line([x + 6, y + h * gy, x + w - 6, y + h * gy], fill="#22344d", width=1)
    pts = [(0.06, 0.30), (0.20, 0.38), (0.32, 0.34), (0.46, 0.52), (0.58, 0.48),
           (0.72, 0.66), (0.84, 0.62), (0.94, 0.78)]
    xy = [(x + w * px, y + h * py) for px, py in pts]
    d.line(xy, fill="#e05252", width=4)
    for px, py in xy:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill="#ff7b7b")
    _pill(d, x + w - 66, y + 6, "-1.03%", font(SANS_B, 11), "#ffffff", "#b01e24")
    d.text((x + 8, y + h - 22), "BRENT $92.47", font=font(SANS_B, 10), fill="#9fb3c8")


def illu_cyclone(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#dceef7")
    cx, cy = x + w * 0.5, y + h * 0.46
    for r, a0, a1 in [(34, 0, 300), (26, 40, 340), (18, 80, 380), (11, 120, 420)]:
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill="#ffffff", width=6)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill="#2e6da4")
    d.ellipse([x + w * 0.06, y + h * 0.78, x + w * 0.34, y + h * 0.94], fill="#3f9e57")
    d.ellipse([x + w * 0.72, y + h * 0.82, x + w * 0.94, y + h * 0.94], fill="#3f9e57")
    _pill(d, x + w - 76, y + 6, "315 KM/H", font(SANS_B, 10), "#ffffff", "#1f4e79")


def illu_outages(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#eef1f4")
    for i in range(3):
        rx = x + w * (0.10 + i * 0.24)
        d.rectangle([rx, y + h * 0.16, rx + w * 0.18, y + h * 0.84], fill="#22344d")
        for r in range(4):
            d.ellipse([rx + 4, y + h * (0.24 + r * 0.15), rx + 9, y + h * (0.24 + r * 0.15) + 5],
                      fill="#7be3a8" if r % 2 == 0 else "#e05252")
    d.polygon([(x + w * 0.86, y + h * 0.14), (x + w * 0.98, y + h * 0.42),
               (x + w * 0.74, y + h * 0.42)], fill="#e8c15a")
    d.text((x + w * 0.86, y + h * 0.20), "!", font=font(SANS_B, 20), fill="#333333", anchor="ma")
    _pill(d, x + 6, y + h - 24, "NSA", font(SANS_B, 10), "#ffffff", "#333333")


ILLU = {"gulf": illu_gulf, "bridge": illu_bridge, "summit": illu_summit,
        "ballot": illu_ballot, "ebola": illu_ebola, "voyager": illu_voyager,
        "measles": illu_measles, "plane": illu_plane, "markets": illu_markets,
        "cyclone": illu_cyclone, "outages": illu_outages}

# ---------------------------------------------------------------- layout

TAG_COLOR = {"MIDDLE EAST": "#9c3d1e", "EUROPE": "#1f4e79", "ASIA": "#1e6b4a",
             "UNITED STATES": "#b01e24", "AFRICA": "#8a6d1b", "SCIENCE": "#5b2d8e",
             "MARKETS": "#0f6b5c", "GLOBAL": "#555555"}


def brief_color(region):
    r = region.lower()
    if any(k in r for k in ("gaza", "israel", "yemen", "new york", "manila")):
        return "#9c3d1e"
    if any(k in r for k in ("russia", "germany", "eu", "uk", "france", "turkey",
                            "serbia", "europe")):
        return "#1f4e79"
    if any(k in r for k in ("myanmar", "pakistan", "korea", "malaysia", "asia")):
        return "#1e6b4a"
    if "brazil" in r:
        return "#c15527"
    if r in ("us", "culture", "sport", "earthquakes"):
        return "#5b2d8e"
    return "#555555"


def fit_lines(text, path, size, max_w, max_lines, min_size=8):
    s = size
    while s >= min_size:
        f = font(path, s)
        lines = wrap(text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        s -= 1
    f = font(path, min_size)
    return f, wrap(text, f, max_w)[:max_lines]


def fit_one_line(text, path, size, max_w, min_size=9):
    s = size
    while s >= min_size:
        f = font(path, s)
        if f.getlength(text) <= max_w:
            return f
        s -= 1
    return font(path, min_size)


def draw_card(d, x, y, w, h, story, P, hl_size, deck_size, illu_h, max_hl=3,
              max_deck=3):
    n, region, beat, headline, deck, kind = story
    d.rectangle([x, y, x + w, y + h], outline=P["card_border"], width=1)
    ILLU[kind](d, x + 1, y + 1, w - 2, illu_h, P)
    cy = y + illu_h + 8
    # number badge + tag
    col = TAG_COLOR.get(region, "#555555")
    d.ellipse([x + 8, cy, x + 25, cy + 17], fill=col)
    num = str(n)
    nf = font(SANS_B, 11 if len(num) == 1 else 10)
    d.text((x + 16.5, cy + 8.5), num, font=nf, fill="#ffffff", anchor="mm")
    tag = f"{region} · {beat}"
    tf = font(SANS_B, 11)
    d.text((x + 30, cy + 8.5), tag, font=tf, fill=col, anchor="lm")
    cy += 24
    # headline
    hf, hlines = fit_lines(headline, SERIF_B, hl_size, w - 16, max_hl)
    lh = int(hf.size * 1.08)
    for ln in hlines:
        d.text((x + 8, cy), ln, font=hf, fill=P["ink"])
        cy += lh
    cy += 3
    # deck
    remain = (y + h - 6) - cy
    df, dlines = fit_lines(deck, SANS, deck_size, w - 16, max_deck)
    dlh = int(df.size * 1.28)
    while len(dlines) * dlh > remain and len(dlines) > 1:
        dlines = dlines[:-1]
    for ln in dlines:
        d.text((x + 8, cy), ln, font=df, fill="#333333")
        cy += dlh


def draw_map(d, x, y, w, h, P):
    d.rectangle([x, y, x + w, y + h], fill="#dcebf5")
    cw, ch = w / 100.0, h / 46.0
    for r, row in enumerate(MAP_ROWS):
        row = (row + " " * 100)[:100]
        for c, ch_ in enumerate(row):
            if ch_ == "#":
                d.rectangle([x + c * cw, y + r * ch,
                             x + (c + 1) * cw, y + (r + 1) * ch],
                            fill="#d9c49a")
    # brief dots
    for c, r in DOTS:
        px, py = x + (c + 0.5) * cw, y + (r + 0.5) * ch
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill="#7a6a4f",
                  outline="#ffffff", width=1)
    # numbered pins
    for n, (c, r) in PINS.items():
        px, py = x + (c + 0.5) * cw, y + (r + 0.5) * ch
        region = FEATURED[n - 1][1]
        col = TAG_COLOR.get(region, "#555555")
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=col,
                  outline="#ffffff", width=2)
        nf = font(SANS_B, 10 if n < 10 else 9)
        d.text((px, py), str(n), font=nf, fill="#ffffff", anchor="mm")


def render(name, P):
    W, H = 1024, 1024
    M = 16
    img = Image.new("RGB", (W, H), P["paper"])
    d = ImageDraw.Draw(img)
    mast_h = P["mast_h"]
    # masthead
    d.rectangle([0, 0, W, mast_h], fill=P["mast_bg"])
    kf = font(SANS_B, 13)
    draw_tracked(d, (M, 12), "THE DAY IN WORLD NEWS", kf, P["kicker"], 1)
    right = "35 STORIES · 6 CONTINENTS · ONE DAY"
    draw_tracked(d, (W - M - text_w(kf, right, 1), 12), right, kf, P["kicker"], 1)
    dsize = P["date_size"]
    while dsize > 40:
        df = font(SERIF_B, dsize)
        if df.getlength("Wednesday 18 November 2026") <= W - 2 * M:
            break
        dsize -= 1
    d.text((W // 2, mast_h - 12), "Wednesday 18 November 2026", font=df,
           fill="#ffffff", anchor="mb")
    d.rectangle([0, mast_h, W, mast_h + 3], fill=P["accent"])
    y = mast_h + 9
    # row 1: 3 big cards
    rh1 = P["rh1"]
    widths1 = [325, 326, 325]
    xs1 = [M, M + 325 + 8, M + 325 + 8 + 326 + 8]
    for i, st in enumerate(FEATURED[:3]):
        draw_card(d, xs1[i], y, widths1[i], rh1, st, P, P["hl1"], P["deck1"],
                  P["illu1"], max_hl=3, max_deck=3)
    y += rh1 + 8
    # rows 2-3: 4 cards each
    for row in (FEATURED[3:7], FEATURED[7:11]):
        rh = P["rh2"]
        xs = [M + i * (242 + 8) for i in range(4)]
        for i, st in enumerate(row):
            draw_card(d, xs[i], y, 242, rh, st, P, P["hl2"], P["deck2"],
                      P["illu2"], max_hl=3, max_deck=3)
        y += rh + 8
    # bottom band
    band_y = y
    band_h = H - band_y - 26
    hf = font(SANS_B, 13)
    d.text((M, band_y), "WHERE IT HAPPENED", font=hf, fill=P["ink"])
    d.text((M + 178, band_y + 1), "numbers = stories 1–11 · dots = briefs",
           font=font(SANS, 10), fill="#777777")
    bx = M + 420 + 12
    d.text((bx, band_y), "ALSO ON WEDNESDAY 18 NOVEMBER", font=hf, fill=P["ink"])
    d.line([M, band_y + 18, M + 420, band_y + 18], fill=P["ink"], width=2)
    d.line([bx, band_y + 18, W - M, band_y + 18], fill=P["ink"], width=2)
    map_y = band_y + 24
    map_h = band_h - 24 - 16
    draw_map(d, M, map_y, 420, map_h, P)
    d.text((M, map_y + map_h + 3),
           "★ 6 Voyager 1 is one light-day out — no pin on this map.",
           font=font(SANS, 10), fill="#777777")
    # briefs, 2 columns x 12 rows
    colw = (W - M - bx - 12) // 2
    for i, (n, region, text) in enumerate(BRIEFS):
        col, row = divmod(i, 12)
        bxx = bx + col * (colw + 12)
        byy = map_y + row * ((map_h - 4) // 12)
        colr = brief_color(region)
        d.rectangle([bxx, byy, bxx + 15, byy + 15], fill=colr)
        nf = font(SANS_B, 9)
        d.text((bxx + 7.5, byy + 7.5), str(n), font=nf, fill="#ffffff", anchor="mm")
        full = f"{region}: {text}"
        bf = fit_one_line(full, SANS, 12, colw - 20, min_size=9)
        d.text((bxx + 19, byy + 7.5), full, font=bf, fill=P["ink"], anchor="lm")
    # footer
    fy = H - 18
    ff = font(SANS, 10)
    d.text((M, fy), "Every story was reported on Wednesday 18 November 2026; "
                    "disputed claims are attributed. Original drawings.",
           font=ff, fill="#777777")
    src = "Sources: AP, Reuters, AFP, BBC, Al Jazeera, UN News"
    d.text((W - M, fy), src, font=ff, fill="#777777", anchor="ra")
    return img


BASE = dict(paper="#f8f4e8", mast_bg="#0e2a4a", kicker="#e8c15a", accent="#b01e24",
            ink="#141414", card_border="#1a1a1a", mast_h=96, date_size=60,
            rh1=252, rh2=200, illu1=100, illu2=66, hl1=23, deck1=13, hl2=18, deck2=12)

STYLES = {
    "v1-classic": dict(BASE),
    "v2-blue": dict(BASE, paper="#f2f5f7", mast_bg="#123a6d", kicker="#ffd166",
                    accent="#c0392b"),
    "v3-red": dict(BASE, mast_bg="#7d1a1a", kicker="#f5e6b8", accent="#1f4e79"),
    "v4-ink": dict(BASE, paper="#f5f2ea", mast_bg="#141414", kicker="#d4af37"),
    "v5-teal": dict(BASE, paper="#f4f6f2", mast_bg="#0b3d3a", kicker="#ffd166",
                    accent="#c15527"),
    "v6-bigtype": dict(BASE, mast_h=110, date_size=66, hl1=24, hl2=19, deck1=13,
                       deck2=12),
    "v7-compact": dict(BASE, mast_h=88, date_size=52, hl1=22, hl2=18),
    "v8-warm": dict(BASE, paper="#fbf6e9", mast_bg="#1f2a44", kicker="#e8c15a",
                    accent="#c15527"),
}


def main():
    import hashlib
    names = sys.argv[1:] or list(STYLES)
    for name in names:
        img = render(name, STYLES[name])
        path = os.path.join(OUT, name + ".png")
        img.save(path, optimize=True)
        data = open(path, "rb").read()
        print(f"{name}: {path} {len(data)} bytes sha256={hashlib.sha256(data).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
