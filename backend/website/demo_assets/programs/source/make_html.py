"""Generate one HTML page (1200x750) per program illustration. Rendered to PNG by render.mjs."""
import os
import sys

OUT = sys.argv[1]
GOLD, CREAM, LINE = "#e9be3b", "#f6ecd2", "#f1e2b8"

# Each program: background gradient, Arabic title, English caption, emblem SVG (drawn in a 400x400 box)
S = f'stroke="{GOLD}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
S3 = f'stroke="{GOLD}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"'
FILL = f'fill="{CREAM}" stroke="{GOLD}" stroke-width="5" stroke-linejoin="round"'


def lines(x1, x2, y0, n, gap, sw=3, color=GOLD, opacity=.55):
    return "".join(f'<line x1="{x1}" x2="{x2}" y1="{y0 + i * gap}" y2="{y0 + i * gap}" stroke="{color}" stroke-width="{sw}" '
                   f'stroke-linecap="round" opacity="{opacity}"/>' for i in range(n))


QURAN_OPEN = f'''
  <!-- open mushaf -->
  <path d="M200 120 C160 92 95 88 52 100 L52 268 C95 256 160 260 200 288 Z" {FILL}/>
  <path d="M200 120 C240 92 305 88 348 100 L348 268 C305 256 240 260 200 288 Z" {FILL}/>
  <path d="M200 120 L200 288" {S}/>
  <rect x="70" y="118" width="112" height="140" rx="6" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".6"/>
  <rect x="218" y="118" width="112" height="140" rx="6" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".6"/>
  {lines(82, 170, 140, 6, 19)}{lines(230, 318, 140, 6, 19)}'''

REHAL = f'''
  <path d="M80 300 L320 372 M320 300 L80 372" {S}/>
  <path d="M60 300 L140 300 M260 300 L340 300" {S}/>'''


def star(cx, cy, r, op=1):
    import math
    pts = []
    for i in range(16):
        rr = r if i % 2 == 0 else r * .55
        a = math.pi * i / 8
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{GOLD}" opacity="{op}"/>'


PROGRAMS = {
    "hifz": dict(bg=("#25104a", "#4b2a86"), ar="حِفْظُ الْقُرْآن", en="Hifz-ul-Quran", sub="Memorise the Book of Allah",
                 svg=QURAN_OPEN + REHAL + star(200, 52, 22) + star(70, 52, 9, .7) + star(330, 52, 9, .7)),
    "nazra": dict(bg=("#2e1459", "#5a3796"), ar="الْقَاعِدَةُ النُّورَانِيَّة", en="Noorani Qaida & Nazra", sub="Read the Qur'an correctly from the first letter",
                  svg=f'''
  <!-- takhti (wooden reading board) -->
  <path d="M110 60 Q200 30 290 60 L300 360 Q200 380 100 360 Z" {FILL}/>
  <circle cx="200" cy="66" r="10" fill="none" stroke="{GOLD}" stroke-width="4"/>
  <path d="M135 110 L265 110 M135 360 L265 360" stroke="{GOLD}" stroke-width="2" opacity=".5"/>
  <text x="200" y="182" text-anchor="middle" font-family="Amiri" font-size="46" fill="#3b1e6d" direction="rtl">ا  ب  ت  ث</text>
  <text x="200" y="256" text-anchor="middle" font-family="Amiri" font-size="46" fill="#3b1e6d" direction="rtl">ج  ح  خ  د</text>
  <text x="200" y="332" text-anchor="middle" font-family="Amiri" font-size="38" fill="#a57f0e" direction="rtl">بَ  بِ  بُ</text>'''),
    "alim": dict(bg=("#1f0d40", "#3b1e6d"), ar="دَرْسِ نِظَامِي", en="Dars-e-Nizami — Alim Course", sub="Eight years of the classical Islamic sciences",
                 svg=f'''
  <!-- stack of kutub -->
  <rect x="70" y="300" width="270" height="52" rx="8" {FILL}/>
  <rect x="90" y="246" width="240" height="52" rx="8" {FILL}/>
  <rect x="60" y="192" width="250" height="52" rx="8" {FILL}/>
  <path d="M100 300 v52 M120 246 v52 M90 192 v52" {S3}/>
  <path d="M150 326 h120 M170 272 h110 M140 218 h120" stroke="{GOLD}" stroke-width="3" opacity=".6"/>
  <!-- inkpot & qalam -->
  <path d="M260 186 q0 -36 26 -36 q26 0 26 36 z" {FILL}/>
  <rect x="274" y="138" width="24" height="14" rx="3" {FILL}/>
  <path d="M296 150 L352 52" {S}/>
  <path d="M352 52 l-6 18" {S3}/>
  {star(130, 120, 26)}'''),
    "alimah": dict(bg=("#35124f", "#6b2f86"), ar="عَالِمَة", en="Alimah Course (Banaat)", sub="Scholarship for sisters in a secure environment",
                   svg=f'''
  <!-- mihrab arch -->
  <path d="M90 370 L90 170 Q90 60 200 40 Q310 60 310 170 L310 370" {S}/>
  <path d="M118 370 L118 178 Q118 90 200 72 Q282 90 282 178 L282 370" {S3} opacity=".7"/>
  <!-- lamp -->
  <path d="M200 72 L200 108" {S3}/>
  <path d="M182 108 h36 l-6 26 q-12 10 -24 0 z" {FILL}/>
  <!-- open book -->
  <path d="M200 260 C175 244 140 242 122 248 L122 330 C140 324 175 326 200 342 Z" {FILL}/>
  <path d="M200 260 C225 244 260 242 278 248 L278 330 C260 324 225 326 200 342 Z" {FILL}/>
  {lines(134, 186, 272, 3, 18)}{lines(214, 266, 272, 3, 18)}
  {star(200, 190, 18)}'''),
    "tajweed": dict(bg=("#24125a", "#47309a"), ar="التَّجْوِيد", en="Tajweed & Qira'at", sub="Recite the Qur'an as it was revealed",
                    svg=f'''
  <!-- recitation waves around a letter -->
  <circle cx="200" cy="200" r="88" {FILL}/>
  <text x="200" y="238" text-anchor="middle" font-family="Amiri" font-size="120" fill="#3b1e6d">ق</text>
  <path d="M95 120 Q60 200 95 280" {S}/><path d="M305 120 Q340 200 305 280" {S}/>
  <path d="M62 92 Q12 200 62 308" {S3} opacity=".7"/><path d="M338 92 Q388 200 338 308" {S3} opacity=".7"/>
  <path d="M34 70 Q-28 200 34 330" stroke="{GOLD}" stroke-width="2" fill="none" opacity=".45"/>
  <path d="M366 70 Q428 200 366 330" stroke="{GOLD}" stroke-width="2" fill="none" opacity=".45"/>
  <text x="200" y="350" text-anchor="middle" font-family="Amiri" font-size="44" fill="{GOLD}">إِخْفَاء · إِظْهَار · إِدْغَام</text>'''),
    "tarjuma": dict(bg=("#1c1250", "#3d2d8a"), ar="تَرْجَمَةُ الْقُرْآن", en="Tarjuma-tul-Quran", sub="Understand the Qur'an word by word",
                    svg=f'''
  <!-- two pages: Arabic ↔ meaning -->
  <rect x="18" y="80" width="164" height="230" rx="12" {FILL}/>
  <rect x="218" y="80" width="164" height="230" rx="12" {FILL}/>
  <text x="100" y="140" text-anchor="middle" font-family="Amiri" font-size="34" fill="#2a1a66">بِسْمِ اللّٰه</text>
  <text x="100" y="195" text-anchor="middle" font-family="Amiri" font-size="34" fill="#2a1a66">الرَّحْمٰن</text>
  <text x="100" y="250" text-anchor="middle" font-family="Amiri" font-size="34" fill="#2a1a66">الرَّحِيْم</text>
  <text x="300" y="132" text-anchor="middle" font-family="Georgia" font-size="18" fill="#2a1a66">In the name</text>
  <text x="300" y="158" text-anchor="middle" font-family="Georgia" font-size="18" fill="#2a1a66">of Allah,</text>
  <text x="300" y="196" text-anchor="middle" font-family="Georgia" font-size="18" fill="#2a1a66">the Most</text>
  <text x="300" y="222" text-anchor="middle" font-family="Georgia" font-size="18" fill="#2a1a66">Compassionate,</text>
  <text x="300" y="260" text-anchor="middle" font-family="Georgia" font-size="18" fill="#2a1a66">the Most</text>
  <text x="300" y="286" text-anchor="middle" font-family="Georgia" font-size="18" fill="#2a1a66">Merciful</text>
  <path d="M186 168 h28 m-10 -10 l10 10 l-10 10 M214 232 h-28 m10 -10 l-10 10 l10 10" {S3}/>
  {star(200, 352, 20)}'''),
    "ifta": dict(bg=("#1a0b36", "#3a2252"), ar="التَّخَصُّص فِي الإِفْتَاء", en="Takhassus fil Ifta", sub="Specialisation in Islamic jurisprudence",
                 svg=f'''
  <!-- balance -->
  <path d="M200 70 L200 330 M140 340 h120 M170 330 h60" {S}/>
  <path d="M70 120 L330 120" {S}/>
  <circle cx="200" cy="70" r="12" fill="{GOLD}"/>
  <path d="M90 120 L50 220 M90 120 L130 220 M310 120 L270 220 M310 120 L350 220" {S3}/>
  <path d="M40 220 h100 q-50 50 -100 0 z" {FILL}/>
  <path d="M260 220 h100 q-50 50 -100 0 z" {FILL}/>
  <!-- book & quill on the pans -->
  <rect x="64" y="196" width="52" height="22" rx="4" fill="{GOLD}"/>
  <path d="M290 216 L340 168 q8 -6 4 6 L298 220" {FILL}/>'''),
    "online": dict(bg=("#2a1157", "#55318f"), ar="التَّعْلِيم عَن بُعْد", en="Online Quran Classes", sub="Live classes for students anywhere in the world",
                   svg=f'''
  <!-- laptop -->
  <rect x="70" y="80" width="260" height="180" rx="14" {FILL}/>
  <rect x="88" y="98" width="224" height="144" rx="6" fill="#2a1157"/>
  <path d="M40 270 h320 l-24 34 h-272 z" {FILL}/>
  <!-- mushaf on screen + live dot -->
  <path d="M200 140 C180 128 150 126 132 132 L132 214 C150 208 180 210 200 222 Z" fill="{CREAM}"/>
  <path d="M200 140 C220 128 250 126 268 132 L268 214 C250 208 220 210 200 222 Z" fill="{CREAM}"/>
  <circle cx="296" cy="114" r="8" fill="#e85d4a"/>
  <!-- signal arcs -->
  <path d="M300 40 q30 -18 60 0 M312 56 q18 -10 36 0" {S3}/>
  <circle cx="330" cy="70" r="5" fill="{GOLD}"/>'''),
}

# UMS website programs (python3 make_html.py OUT --ums): calligraphy + artwork only — the card shows the English title.
UMS = {
    "hq": ("hifz", "تَحْفِيظُ الْقُرْآن", ("#25104a", "#4b2a86")),
    "tqr": ("tajweed", "تَجْوِيد و قِرَاءَت", ("#24125a", "#47309a")),
    "dn": ("alim", "دَرْسِ نِظَامِي", ("#1f0d40", "#3b1e6d")),
    "tfh": ("ifta", "تَخَصُّص فِي الْفِقْهِ الْحَنَفِي", ("#1a0b36", "#3a2252")),
    "odn": ("online", "آن لائن درسِ نظامی", ("#2a1157", "#55318f")),
    "qt": ("nazra", "تعلیمِ قرآن مع تجوید", ("#2e1459", "#5a3796")),
    "fsc": ("alim", "فہمِ شریعت", ("#22104c", "#4d2a8c")),
    "ttc": ("tarjuma", "ترجمہ و تفسیر", ("#1c1250", "#3d2d8a")),
    "fdc": ("alimah", "فہمِ دین", ("#2c1252", "#5c3392")),
    "imc": ("ifta", "علمِ میراث", ("#1d0c3c", "#43266f")),
}
ART_ONLY = "--ums" in sys.argv
if ART_ONLY:
    PROGRAMS = {k: dict(PROGRAMS[base], ar=ar, bg=bg, en="", sub="") for k, (base, ar, bg) in UMS.items()}

PATTERN = f'''<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><g fill="none" stroke="{GOLD}" stroke-opacity=".16" stroke-width="1.2">
<path d="M48 4 l12 32 32 12 -32 12 -12 32 -12 -32 -32 -12 32 -12z"/><circle cx="48" cy="48" r="14"/><path d="M0 0 l14 14 M96 0 l-14 14 M0 96 l14 -14 M96 96 l-14 -14"/></g></svg>'''

import base64  # noqa: E402

pat = "data:image/svg+xml;base64," + base64.b64encode(PATTERN.encode()).decode()

for slug, p in PROGRAMS.items():
    html = f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cormorant+Garamond:wght@600;700&family=Inter:wght@500;600&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;width:1200px;height:750px;overflow:hidden}}
.c{{position:relative;width:1200px;height:750px;background:linear-gradient(135deg,{p["bg"][0]},{p["bg"][1]});display:grid;grid-template-columns:1fr 520px;align-items:center;font-family:Inter,sans-serif}}
.c::before{{content:"";position:absolute;inset:0;background:url("{pat}");opacity:1}}
.c::after{{content:"";position:absolute;inset:0;background:radial-gradient(circle at 78% 45%,rgba(233,190,59,.28),transparent 45%),linear-gradient(0deg,rgba(0,0,0,.25),transparent 40%)}}
.frame{{position:absolute;inset:22px;border:2px solid rgba(233,190,59,.45);border-radius:18px;z-index:1}}
.txt{{position:relative;z-index:2;padding-left:84px}}
.ar{{font-family:Amiri,serif;font-weight:700;font-size:{(112 if len(p["ar"]) < 16 else 92 if len(p["ar"]) < 24 else 74) if ART_ONLY else (88 if len(p["ar"]) < 16 else 72)}px;color:{GOLD};direction:rtl;text-align:left;line-height:1.35;margin:0}}
.en{{font-family:"Cormorant Garamond",serif;font-weight:700;font-size:58px;color:#fff;margin:6px 0 10px;line-height:1.05}}
.sub{{font-size:24px;color:#e3dbf3;font-weight:500;max-width:520px}}
.rule{{width:120px;height:3px;background:{GOLD};border-radius:2px;margin:18px 0}}
.art{{position:relative;z-index:2;display:grid;place-items:center}}
.halo{{position:absolute;width:470px;height:470px;border-radius:50%;border:2px dashed rgba(233,190,59,.35)}}
</style></head><body><div class="c"><div class="frame"></div>
<div class="txt"><p class="ar" dir="rtl">{p["ar"]}</p><div class="rule"></div>{f'<div class="en">{p["en"]}</div><div class="sub">{p["sub"]}</div>' if p["en"] else ""}</div>
<div class="art"><div class="halo"></div><svg width="420" height="420" viewBox="0 0 400 400">{p["svg"]}</svg></div>
</div></body></html>'''
    with open(os.path.join(OUT, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)
print("\n".join(PROGRAMS))
