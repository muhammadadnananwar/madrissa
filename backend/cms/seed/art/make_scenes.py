"""
Website illustrations in the University's purple-and-gold style (no stock photos).

    python3 make_scenes.py OUT_DIR        -> OUT_DIR/<name>.html  (render with ../../../website/demo_assets/programs/source/render.mjs)

Scenes are centred and text-free so they survive any crop (square department cards, wide banners, gallery tiles);
the website prints titles over them. Replace them with real photographs of the Jamia from the portal when available.
"""
import base64
import math
import os
import runpy
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM_SRC = os.path.join(HERE, "..", "..", "..", "website", "demo_assets", "programs", "source", "make_html.py")
OUT = sys.argv[1]

# Reuse the program emblems (hifz, nazra, alim, alimah, tajweed, tarjuma, ifta, online)
_saved = sys.argv
sys.argv = ["make_html.py", tempfile.mkdtemp()]
P = runpy.run_path(PROGRAM_SRC)
sys.argv = _saved
GOLD, CREAM = P["GOLD"], P["CREAM"]
S, S3, FILL = P["S"], P["S3"], P["FILL"]
lines, star = P["lines"], P["star"]
EMBLEM = {k: v["svg"] for k, v in P["PROGRAMS"].items() if not k.startswith("_")}


def arch(x, y, w, h, extra=""):
    """Pointed (Mughal) arch outline: base at y, width w, height h."""
    r = w / 2
    return (f'<path d="M{x} {y} V{y - h + r} Q{x} {y - h + r * .2} {x + r} {y - h} Q{x + w} {y - h + r * .2} {x + w} {y - h + r} V{y}" '
            f'{extra or S}/>')


def dome(cx, base, r, h):
    return (f'<path d="M{cx - r} {base} C{cx - r} {base - h * .75} {cx - r * .35} {base - h} {cx} {base - h * 1.12} '
            f'C{cx + r * .35} {base - h} {cx + r} {base - h * .75} {cx + r} {base} Z" {FILL}/>'
            f'<path d="M{cx} {base - h * 1.12} v-22" {S3}/>'
            f'<path d="M{cx - 7} {base - h * 1.12 - 30} a9 9 0 1 0 12 -8 a7 7 0 1 1 -12 8z" fill="{GOLD}"/>')


def minaret(x, base, height, w=26):
    top = base - height
    return (f'<rect x="{x - w / 2}" y="{top}" width="{w}" height="{height}" {FILL}/>'
            f'<path d="M{x - w / 2 - 8} {top + height * .35} h{w + 16} M{x - w / 2 - 8} {top + height * .62} h{w + 16}" {S3}/>'
            f'<path d="M{x - w / 2 - 4} {top} L{x} {top - 46} L{x + w / 2 + 4} {top} Z" {FILL}/>'
            f'<path d="M{x} {top - 46} v-14" {S3}/>')


MOSQUE = (minaret(62, 360, 230) + minaret(338, 360, 230)
          + f'<rect x="96" y="250" width="208" height="110" {FILL}/>'
          + dome(200, 252, 92, 118)
          + dome(120, 252, 24, 30) + dome(280, 252, 24, 30)
          + arch(172, 360, 56, 74) + arch(116, 330, 30, 44, S3) + arch(254, 330, 30, 44, S3)
          + f'<path d="M30 362 H370" {S}/>')

LANTERN = (f'<path d="M200 20 V70" {S3}/><circle cx="200" cy="78" r="9" {S3}/>'
           f'<path d="M150 112 Q200 74 250 112 Z" {FILL}/>'
           f'<path d="M150 112 L132 250 Q200 300 268 250 L250 112 Z" {FILL}/>'
           f'<path d="M175 112 L168 265 M225 112 L232 265 M200 112 V276" {S3}/>'
           f'<path d="M140 180 Q200 196 260 180" {S3}/>'
           f'<path d="M168 272 Q200 300 232 272 L214 318 H186 Z" {FILL}/>'
           f'<path d="M200 318 v30" {S3}/>{star(200, 352, 12)}'
           f'<ellipse cx="200" cy="200" rx="34" ry="46" fill="{GOLD}" opacity=".35"/>'
           f'{star(84, 96, 14, .8)}{star(320, 140, 10, .7)}{star(300, 320, 8, .6)}')

SCROLL_QUILL = (f'<path d="M92 92 H292 V330 H92 Z" {FILL}/>'
                f'<path d="M92 92 q-30 0 -30 -18 q0 -18 30 -18 H292 q30 0 30 18 q0 18 -30 18" {FILL}/>'
                f'<path d="M92 330 q-30 0 -30 18 q0 18 30 18 H292 q30 0 30 -18 q0 -18 -30 -18" {FILL}/>'
                + lines(118, 266, 130, 9, 21) +
                f'<path d="M352 60 C300 110 262 190 232 262" {S}/>'
                f'<path d="M352 60 C330 120 300 170 262 212 M352 60 C318 96 286 140 262 212" {S3}/>'
                f'<path d="M232 262 l-6 22 l18 -14" {S3}/>')

BOOKLETS = (f'<rect x="70" y="120" width="70" height="220" rx="6" {FILL} transform="rotate(-8 105 230)"/>'
            f'<rect x="150" y="100" width="76" height="240" rx="6" {FILL}/>'
            f'<rect x="236" y="120" width="70" height="220" rx="6" {FILL} transform="rotate(8 271 230)"/>'
            f'<path d="M168 140 h40 M168 160 h40 M168 300 h40" {S3}/>'
            + star(188, 220, 20) +
            f'<path d="M300 92 h60 v76 h-60 z" {FILL}/>' + lines(310, 350, 108, 4, 14, 2) +
            f'<path d="M40 340 H360" {S}/>')

BOOKSHELF = (f'<rect x="60" y="50" width="280" height="310" rx="10" {S}/>'
             f'<path d="M60 150 H340 M60 252 H340" {S}/>'
             + "".join(f'<rect x="{x}" y="{y - h}" width="{w}" height="{h}" rx="3" {FILL}/>'
                       for y, row in ((150, ((76, 22, 80), (102, 18, 70), (124, 26, 86), (154, 20, 66), (178, 24, 82), (206, 18, 72),
                                             (228, 26, 84), (258, 20, 68), (282, 24, 80), (310, 18, 74))),
                                      (252, ((76, 26, 84), (106, 18, 72), (128, 22, 80), (154, 26, 86), (184, 18, 66), (206, 24, 82),
                                             (234, 20, 74), (258, 26, 86), (288, 18, 70), (310, 22, 80))),
                                      (360, ((76, 22, 86), (102, 24, 76), (130, 18, 82), (152, 26, 86), (182, 20, 72), (206, 22, 84),
                                             (232, 26, 80), (262, 18, 70), (284, 24, 84), (312, 20, 74))))
                       for x, w, h in row))

BOARDING = (f'<rect x="60" y="150" width="280" height="210" {FILL}/>'
            + dome(200, 152, 56, 70) + minaret(48, 360, 170, 20) + minaret(352, 360, 170, 20)
            + "".join(arch(x, y, 34, 44, S3) for y in (222, 298) for x in (86, 140, 228, 282))
            + arch(180, 360, 40, 62) + f'<path d="M20 362 H380" {S}/>')
MOON = f'<path d="M300 70 a26 26 0 1 0 22 40 a20 20 0 1 1 -22 -40z" fill="{GOLD}"/>'

HALQA = ("".join(
    f'<g transform="translate({x} {y}) scale(.42)"><path d="M200 120 C160 92 95 88 52 100 L52 268 C95 256 160 260 200 288 Z" {FILL}/>'
    f'<path d="M200 120 C240 92 305 88 348 100 L348 268 C305 256 240 260 200 288 Z" {FILL}/>'
    f'<path d="M200 120 L200 288" {S}/><path d="M80 300 L320 372 M320 300 L80 372" {S}/></g>'
    for x, y in ((32, 70), (200, 70), (116, 200))) + f'<path d="M30 372 H370" {S3}/>' + star(200, 60, 16))

MINBAR = (f'<path d="M110 360 V250 H150 V200 H190 V150 H230 V360 Z" {FILL}/>'
          f'<path d="M230 150 V96 Q230 70 256 70 Q282 70 282 96 V360" {S}/>'
          + arch(244, 160, 26, 44, S3) +
          f'<path d="M120 250 h30 M160 200 h30 M200 150 h30" {S3}/>'
          f'<path d="M318 360 V210 M296 360 h44" {S}/><rect x="306" y="168" width="24" height="44" rx="12" {FILL}/>'
          f'<path d="M80 362 H360" {S}/>{star(110, 110, 18)}{star(70, 170, 9, .7)}')

FORM_PEN = (f'<rect x="90" y="60" width="210" height="290" rx="12" {FILL}/>'
            f'<rect x="150" y="44" width="90" height="30" rx="8" {FILL}/>'
            + "".join(f'<rect x="114" y="{y}" width="22" height="22" rx="4" {S3}/><path d="M150 {y + 11} h120" {S3}/>'
                      for y in (110, 160, 210, 260)) +
            f'<path d="M118 120 l6 7 l12 -14 M118 170 l6 7 l12 -14" {S3}/>'
            f'<path d="M352 120 L262 300 l-8 30 l22 -20 L366 128 Z" {FILL}/>')

CALENDAR = (f'<rect x="70" y="80" width="260" height="260" rx="16" {FILL}/>'
            f'<path d="M70 140 H330" {S}/><path d="M130 56 v44 M270 56 v44" {S}/>'
            + "".join(f'<circle cx="{110 + c * 45}" cy="{180 + r * 45}" r="7" fill="{GOLD}" opacity="{1 if (r, c) == (1, 2) else .45}"/>'
                      for r in range(4) for c in range(5)) +
            f'<path d="M318 40 a30 30 0 1 0 26 46 a24 24 0 1 1 -26 -46z" fill="{GOLD}"/>')

ARCADE = ("".join(arch(x, 330, 64, 140) for x in (40, 128, 216, 304))
          + f'<path d="M24 190 H384 M24 330 H384" {S}/>' + f'<path d="M24 172 H384" {S3}/>'
          + "".join(dome(x, 172, 26, 30) for x in (72, 336)) + star(204, 110, 22))

STUDENTS_READING = EMBLEM["hifz"]

# name: (art, background gradient)
SCENES = {
    # departments
    "dept-ib": (LANTERN, ("#1d0b3a", "#4a2683")),
    "dept-tq": (EMBLEM["hifz"], ("#25104a", "#4b2a86")),
    "dept-tj": (EMBLEM["tajweed"], ("#24125a", "#47309a")),
    "dept-dn": (EMBLEM["alim"], ("#1f0d40", "#3b1e6d")),
    "dept-tfh": (EMBLEM["ifta"], ("#1a0b36", "#3a2252")),
    "dept-di": (SCROLL_QUILL, ("#22104c", "#4d2a8c")),
    "dept-ni": (BOOKLETS, ("#2c1252", "#5c3392")),
    "dept-oe": (EMBLEM["online"], ("#2a1157", "#55318f")),
    # site-wide
    "about": (MOSQUE, ("#1f0d40", "#4b2a86")),
    "facility-boarding": (BOARDING + MOON, ("#25104a", "#4b2a86")),
    "facility-library": (BOOKSHELF, ("#1f0d40", "#3b1e6d")),
    "facility-classroom": (HALQA, ("#2e1459", "#5a3796")),
    # gallery
    "gallery-masjid": (MOSQUE, ("#25104a", "#55318f")),
    "gallery-arcade": (ARCADE, ("#1f0d40", "#47309a")),
    "gallery-library": (BOOKSHELF, ("#2c1252", "#5c3392")),
    "gallery-halqa": (HALQA, ("#1d0b3a", "#4a2683")),
    "gallery-iqama": (BOARDING + MOON, ("#22104c", "#4d2a8c")),
    "gallery-bazm": (MINBAR, ("#2a1157", "#55318f")),
    "gallery-kutub": (EMBLEM["alim"], ("#1a0b36", "#3a2252")),
    # news & events
    "news-admissions": (FORM_PEN, ("#25104a", "#4b2a86")),
    "news-bazm": (MINBAR, ("#1f0d40", "#3b1e6d")),
    "news-online": (EMBLEM["online"], ("#2c1252", "#5c3392")),
    "event-openday": (MOSQUE, ("#2e1459", "#5a3796")),
    "event-bazm": (MINBAR, ("#24125a", "#47309a")),
    "event-exams": (CALENDAR, ("#1f0d40", "#3b1e6d")),
    "event-welcome": (ARCADE, ("#25104a", "#4b2a86")),
    "event-jalsa": (LANTERN, ("#2a1157", "#55318f")),
    "event-qiraat": (EMBLEM["tajweed"], ("#22104c", "#4d2a8c")),
    "event-seerah": (BOOKLETS, ("#1d0b3a", "#4a2683")),
}

PATTERN = (f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><g fill="none" stroke="{GOLD}" '
           'stroke-opacity=".16" stroke-width="1.2"><path d="M48 4 l12 32 32 12 -32 12 -12 32 -12 -32 -32 -12 32 -12z"/>'
           '<circle cx="48" cy="48" r="14"/><path d="M0 0 l14 14 M96 0 l-14 14 M0 96 l14 -14 M96 96 l-14 -14"/></g></svg>')
PAT = "data:image/svg+xml;base64," + base64.b64encode(PATTERN.encode()).decode()


def page(svg, bg, w=1200, h=750, size=470):
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
.c{{position:relative;width:{w}px;height:{h}px;background:linear-gradient(135deg,{bg[0]},{bg[1]});display:grid;place-items:center}}
.c::before{{content:"";position:absolute;inset:0;background:url("{PAT}")}}
.c::after{{content:"";position:absolute;inset:0;background:radial-gradient(circle at 50% 46%,rgba(233,190,59,.30),transparent 42%),linear-gradient(0deg,rgba(0,0,0,.28),transparent 45%)}}
.halo{{position:absolute;width:{size + 90}px;height:{size + 90}px;border-radius:50%;border:2px dashed rgba(233,190,59,.35);z-index:1}}
svg.art{{position:relative;z-index:2}}
</style></head><body><div class="c"><div class="halo"></div>
<svg class="art" width="{size}" height="{size}" viewBox="0 0 400 400">{svg}</svg></div></body></html>'''


def hero():
    """1920x1080 skyline at dusk: the Jamia's domes and minarets on the right, open sky for the headline on the left."""
    stars = "".join(star(x, y, r, op) for x, y, r, op in ((180, 140, 10, .7), (420, 90, 7, .6), (700, 180, 9, .5), (960, 70, 8, .7),
                                                         (1250, 120, 6, .6), (1500, 90, 9, .8), (1780, 160, 7, .6), (1620, 300, 6, .5)))
    skyline = (f'<g transform="translate(980 250) scale(2.2)">{MOSQUE}</g>'
               f'<g transform="translate(640 666) scale(1.05)" opacity=".75">{BOARDING}</g>'
               f'<g transform="translate(1545 733) scale(.95)" opacity=".7">{ARCADE}</g>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden}}
.c{{position:relative;width:1920px;height:1080px;background:linear-gradient(180deg,#140726 0%,#2a1157 45%,#5a3796 78%,#8a5fb8 100%)}}
.c::before{{content:"";position:absolute;inset:0;background:url("{PAT}");opacity:.7}}
.glow{{position:absolute;left:1180px;top:430px;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,rgba(233,190,59,.35),transparent 60%)}}
svg{{position:absolute;inset:0}}
</style></head><body><div class="c"><div class="glow"></div>
<svg width="1920" height="1080" viewBox="0 0 1920 1080">{stars}
<path d="M1560 170 a70 70 0 1 0 60 108 a56 56 0 1 1 -60 -108z" fill="{GOLD}"/>
{skyline}<rect x="0" y="1048" width="1920" height="32" fill="#140726"/></svg></div></body></html>'''


os.makedirs(OUT, exist_ok=True)
for name, (svg, bg) in SCENES.items():
    with open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8") as f:
        f.write(page(svg, bg))
with open(os.path.join(OUT, "hero.html"), "w", encoding="utf-8") as f:
    f.write(hero())
print(len(SCENES) + 1, "scenes")
