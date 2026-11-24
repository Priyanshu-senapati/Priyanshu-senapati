"""Build the SVG images used by the profile README.

Run:  python tools/make_assets.py   (writes assets/*.svg)

Design: things on a desk. A graph-paper notebook page (hero), a terminal you can
"ask" (results), handwritten index cards (projects) and sticky notes (toolbox).
Handwriting is Kalam (Indian Type Foundry, also covers Devanagari); the terminal is
JetBrains Mono; Kannada is Noto Sans Kannada. Fonts are embedded as subsets so the
page renders the same everywhere. Every number comes from the resume: change it
here, never in the SVGs.
"""
import base64
import io
import random
from collections import defaultdict
from functools import lru_cache
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"
FONT_DIR = ROOT / "fonts"
HAND, MONO, KANNADA = "Kalam", "JetBrains Mono", "Noto Sans Kannada"
STATIC_FONTS = {(HAND, 400): "Kalam-Regular.ttf", (HAND, 700): "Kalam-Bold.ttf"}
VARIABLE_FONTS = {MONO: "JetBrainsMono.ttf", KANNADA: "NotoSansKannada.ttf"}
FALLBACK = "'Segoe Print', 'Comic Sans MS', cursive"

BLUE = "#1f3a93"       # ballpoint
BLUE2 = "#6f86c9"      # lighter ink for secondary doodle lines
PENCIL = "#5b6170"
RED = "#d63a2a"        # correction pen
HV = "#f07a12"         # high-voltage orange: what each system guards against
HIGHLIGHT = "#ffe45c"
PAPER = "#ffffff"

DEFS = f"""
<pattern id="quad" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#cfdff3" stroke-width="1"/></pattern>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="{HV}" stroke-width="1.8"/></pattern>
<filter id="wobble" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="3.2"/></filter>
<filter id="lift" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="2" dy="5" stdDeviation="5" flood-color="#000" flood-opacity=".22"/></filter>"""

rng = random.Random(11)  # fixed seed: the hand-drawn wobble is identical on every build


# ------------------------------------------------------------------ fonts
@lru_cache(None)
def _instance_bytes(family: str, weight: int) -> bytes:
    if (family, weight) in STATIC_FONTS:
        return (FONT_DIR / STATIC_FONTS[(family, weight)]).read_bytes()
    font = TTFont(FONT_DIR / VARIABLE_FONTS[family])
    axes = {"wght": weight}
    if any(a.axisTag == "wdth" for a in font["fvar"].axes):
        axes["wdth"] = 100
    buf = io.BytesIO()
    instancer.instantiateVariableFont(font, axes).save(buf)
    return buf.getvalue()


@lru_cache(None)
def _metrics(family: str, weight: int):
    font = TTFont(io.BytesIO(_instance_bytes(family, weight)))
    return font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm


def measure(s: str, size: float, weight: int = 400, family: str = HAND) -> float:
    """Advance width from the real font (kerning ignored, close enough for layout)."""
    cmap, hmtx, upem = _metrics(family, weight)
    return sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in s) * size / upem


def font_face(family: str, weight: int, chars: str) -> str:
    font = TTFont(io.BytesIO(_instance_bytes(family, weight)))
    opts = subset.Options()
    opts.layout_features = ["*"]  # keep shaping features: Kannada and Devanagari need them
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/ttf;base64,{data}) format('truetype')}}"


def wrap_widths(s: str, size: float, widths: list[float], weight: int = 400, family: str = HAND) -> list[str]:
    """Greedy wrap where line i may be widths[i] wide (the last width repeats)."""
    lines, cur = [], ""
    for word in s.split():
        limit = widths[min(len(lines), len(widths) - 1)]
        trial = f"{cur} {word}".strip()
        if measure(trial, size, weight, family) <= limit:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


# ------------------------------------------------------------------ svg builder
class Svg:
    def __init__(self, w: int, h: int, label: str):
        self.w, self.h, self.label = w, h, label
        self.parts: list[str] = []
        self.used: dict[tuple[str, int], set[str]] = defaultdict(set)

    def raw(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size, *, weight=400, fill=BLUE, anchor="start", family=HAND):
        self.used[(family, weight)].update(s)
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="\'{family}\', {FALLBACK}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')

    def render(self, style: str = "") -> str:
        faces = "".join(font_face(f, w, "".join(sorted(ch))) for (f, w), ch in sorted(self.used.items()))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">\n'
                f'<title>{escape(self.label)}</title>\n<defs>{DEFS}\n</defs>\n<style>{faces}\n{style}</style>\n'
                + "\n".join(self.parts) + "\n</svg>\n")


# ------------------------------------------------------------------ hand-drawn marks
def rough(x1, y1, x2, y2, color=BLUE, w=2.2, jitter=1.4) -> str:
    """A pen stroke: two slightly different passes, like a real line drawn twice."""
    out = []
    for p in range(2):
        j = jitter
        mx, my = (x1 + x2) / 2 + rng.uniform(-j, j) * 2, (y1 + y2) / 2 + rng.uniform(-j, j) * 2
        out.append(f'<path d="M{x1 + rng.uniform(-j, j):.1f},{y1 + rng.uniform(-j, j):.1f} Q{mx:.1f},{my:.1f} '
                   f'{x2 + rng.uniform(-j, j):.1f},{y2 + rng.uniform(-j, j):.1f}" fill="none" stroke="{color}" '
                   f'stroke-width="{w if p == 0 else w * .6:.2f}" stroke-linecap="round" pathLength="1" '
                   f'opacity="{1 if p == 0 else .6}"/>')
    return "".join(out)


def rough_rect(x, y, w, h, color=BLUE, sw=2.2) -> str:
    return (rough(x, y, x + w, y, color, sw) + rough(x + w, y, x + w, y + h, color, sw)
            + rough(x + w, y + h, x, y + h, color, sw) + rough(x, y + h, x, y, color, sw))


def highlight(x, y, w, h=26) -> str:
    """A highlighter swipe behind text (y is the text baseline)."""
    t = y - h + 6
    return (f'<path d="M{x - 4},{t + 3} L{x + w + 6},{t} L{x + w + 3},{t + h} L{x - 6},{t + h + 2} Z" '
            f'fill="{HIGHLIGHT}" fill-opacity=".85" style="mix-blend-mode:multiply"/>')


def tape(cx, cy, angle=-4, w=110) -> str:
    return (f'<rect x="{cx - w / 2}" y="{cy - 14}" width="{w}" height="28" fill="#efe3b0" fill-opacity=".85" '
            f'transform="rotate({angle} {cx} {cy})"/>')


# ------------------------------------------------------------------ the car (side elevation, 560 x 205 units)
CAR_BODY = ("M30,166 L27,142 Q26,122 40,114 L100,104 Q118,100 132,88 L160,66 Q172,56 192,54 L322,52 "
            "Q342,52 356,64 L398,94 L470,104 Q512,110 528,120 Q536,126 535,142 L532,166 L480,166 "
            "A40,40 0 0 0 400,166 L160,166 A40,40 0 0 0 80,166 Z")
CAR_DETAIL = ["M170,98 L196,68 Q202,62 212,62 L268,62 L268,98 Z",
              "M282,98 L282,62 L318,62 Q330,62 338,70 L370,98 Z",
              "M276,102 L278,160", "M386,104 L392,156",
              "M506,114 L528,121 L526,128 L508,124 Z", "M30,122 L44,118 L44,128 L31,130 Z"]
WHEELS = [f"M{cx - r},168 a{r},{r} 0 1,0 {2 * r},0 a{r},{r} 0 1,0 -{2 * r},0" for cx in (120, 440) for r in (34, 20)]
HV_BATTERY = "M170,150 L388,150 L388,162 L170,162 Z"
HV_CABLE = "M388,156 C412,156 420,130 452,121"
HV_MOTOR = "M452,112 L480,112 L480,128 L452,128 Z"


def car(stroke=3.0) -> str:
    def path(d, color, width):
        return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'
    out = [path(CAR_BODY, BLUE, stroke)] + [path(d, BLUE, stroke) for d in WHEELS]
    out += [path(d, BLUE, stroke * .7) for d in CAR_DETAIL]
    out.append(f'<path d="{HV_BATTERY}" fill="url(#hatch)"/>')
    out += [path(d, HV, stroke * 1.1) for d in (HV_BATTERY, HV_CABLE, HV_MOTOR)]
    return "".join(out)


# ------------------------------------------------------------------ hero: a notebook page
def hero() -> str:
    W, H = 1200, 500
    s = Svg(W, H, "Notebook page. Priyanshu Kumar Senapati, B.Tech CSE (AI and ML) at RV University, class of 2028, Bengaluru. "
                  "'I build AI that is always right' is crossed out and corrected to 'knows when it's wrong'. "
                  "Sticky note: RescueLens, 94.55% top-1; shown 60 cars it had never seen, it said not sure 58 times instead of guessing. "
                  "Tally: 10 hackathons, 2 made the finale. A sketched car marks where the high voltage runs.")
    s.raw(f'<rect width="{W}" height="{H}" rx="14" fill="{PAPER}"/><rect width="{W}" height="{H}" rx="14" fill="url(#quad)"/>')
    s.raw('<path d="M92,0 V500" stroke="#f0a0a0" stroke-width="1.6"/>')
    for y in (110, 250, 390):
        s.raw(f'<circle cx="44" cy="{y}" r="13" fill="#eef2f7" stroke="#c4cfdd" stroke-width="1.5"/>')

    s.text(122, 96, "Priyanshu Kumar Senapati", 58, weight=700)
    nw = measure("Priyanshu Kumar Senapati", 58, 700)
    s.raw(rough(120, 114, 122 + nw, 110, BLUE, 2.6) + rough(140, 122, 110 + nw, 120, BLUE, 1.6))
    s.text(124, 152, "B.Tech CSE (AI & ML) at RV University, class of 2028. Bengaluru.", 21, fill=PENCIL)

    x0, y = 122, 262
    pre, struck, fix = "I build AI that ", "is always right.", "knows when it’s wrong."
    w1, w2 = measure(pre, 38), measure(struck, 38)
    s.text(x0, y, pre + struck, 38, fill="#22252c")
    s.raw(f'<g class="strike">{rough(x0 + w1 - 6, y - 12, x0 + w1 + w2 + 6, y - 16, RED, 4)}</g>')
    s.raw(f'<path class="caret" d="M{x0 + w1 - 10},{y + 18} L{x0 + w1 - 2},{y + 4} L{x0 + w1 + 6},{y + 18}" fill="none" '
          f'stroke="{RED}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    s.raw('<g class="write">')
    s.text(x0 + w1 - 4, y - 48, fix, 40, weight=700, fill=RED)
    s.raw("</g>")
    s.text(x0, y + 46, "the one thing RescueLens, Neralu and Query2Diagnose have in common", 21, fill=PENCIL)

    s.raw(f'<g transform="rotate(-3 272 416)"><rect x="122" y="350" width="300" height="134" fill="#fff3a3" filter="url(#lift)"/>')
    for i, line in enumerate(["RescueLens: 94.55% top-1.", "Shown 60 cars it had never seen,",
                              "it said “not sure” 58 times", "instead of guessing."]):
        s.text(140, 382 + i * 27, line, 21, fill="#2b2b2b")
    s.raw("</g>")

    s.text(470, 392, "hackathons:", 22, fill=PENCIL)
    for g in range(2):
        gx = 600 + g * 62
        s.raw("".join(rough(gx + k * 10, 372, gx + k * 10 + 1, 404, BLUE, 2.4) for k in range(4)))
        s.raw(rough(gx - 6, 400, gx + 38, 374, BLUE, 2.4))
    s.text(470, 440, "2 made the finale (Vietnam, Hack4SDG)", 21, fill=PENCIL)
    two = 470 + measure("2", 21) / 2
    s.raw(f'<ellipse cx="{two:.0f}" cy="433" rx="15" ry="16" fill="none" stroke="{RED}" stroke-width="2.2" transform="rotate(-8 {two:.0f} 433)"/>')

    s.raw(f'<g transform="translate(748,250) scale(.76)" filter="url(#wobble)">{car()}</g>')
    s.raw(f'<g transform="translate(750,252) scale(.76)" filter="url(#wobble)" opacity=".3">'
          f'<path d="{CAR_BODY}" fill="none" stroke="{BLUE}" stroke-width="2.4"/></g>')
    s.raw(f'<path d="M905,456 C895,430 900,410 920,382" fill="none" stroke="{HV}" stroke-width="2.6" stroke-linecap="round"/>'
          f'<path d="M911,389 L921,379 L925,393" fill="none" stroke="{HV}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    s.text(830, 482, "high voltage: don’t cut here!", 23, weight=700, fill=HV)
    style = """.strike path{stroke-dasharray:1 1.1;animation:draw .5s ease-out .6s backwards}
@keyframes draw{from{stroke-dashoffset:1.05}}
.caret{animation:fade .2s 1.1s backwards}
.write{animation:write 1.4s steps(22) 1.2s backwards}
@keyframes write{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes fade{from{opacity:0}}
@media (prefers-reduced-motion:reduce){.strike path,.caret,.write{animation:none}}"""
    return s.render(style)


# ------------------------------------------------------------------ results: a terminal you can ask
QA = [
    ("does your AI guess when it isn't sure?", "no. RescueLens refused to guess on 58 of 60 cars it had never seen."),
    ("is it any good?", "94.55% top-1 across 196 car classes."),
    ("and the LLM agent?", "Query2Diagnose: 0% unsafe answers on 300 cases. LLM baselines: 43-70%."),
    ("does any of it have tests?", "790 across four projects: ULTRON 337, Neralu 287, RescueLens 94, Voyance 72."),
    ("hackathons?", "10 so far. 2 finales: Hack4SDG 2026, and Top 30 in Vietnam."),
    ("what's his best project?", None),
]
ABSTAIN = "not certain. refusing to guess. scroll down and judge for yourself."
assert 337 + 287 + 94 + 72 == 790


def terminal() -> str:
    W, top, step = 1200, 118, 78
    H = top + step * len(QA) + 40
    s = Svg(W, H, "Terminal. " + " ".join(f'Q: {q} A: {a or ABSTAIN}' for q, a in QA))
    BG, FG, MUTED, GREEN, ORANGE = "#0f1419", "#e6edf3", "#8b949e", "#3fb950", "#ff9d42"
    s.raw(f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="#30363d"/>')
    s.text(48, 50, "~/priyanshu", 17, fill=MUTED, family=MONO)
    s.text(W - 48, 50, "ask-the-model", 17, fill=MUTED, family=MONO, anchor="end")
    s.raw(f'<path d="M0,70 H{W}" stroke="#30363d"/>')
    line = 0
    for i, (q, a) in enumerate(QA):
        y = top + i * step
        s.raw(f'<g class="ln" style="animation-delay:{.3 + line * .42:.2f}s">')
        s.text(48, y, "$", 20, weight=700, fill=GREEN, family=MONO)
        s.text(76, y, f'ask "{q}"', 20, weight=500, fill=FG, family=MONO)
        s.raw("</g>")
        line += 1
        s.raw(f'<g class="ln" style="animation-delay:{.3 + line * .42:.2f}s">')
        if a:
            s.text(76, y + 30, a, 20, fill=FG, family=MONO)
        else:
            s.text(76, y + 30, ABSTAIN, 20, weight=700, fill=ORANGE, family=MONO)
        s.raw("</g>")
        line += 1
        assert 76 + measure(a or ABSTAIN, 20, 700, MONO) < W - 40, f"terminal line too long: {a}"
    y = top + len(QA) * step
    s.raw(f'<g class="ln" style="animation-delay:{.3 + line * .42:.2f}s">')
    s.text(48, y - 8, "$", 20, weight=700, fill=GREEN, family=MONO)
    s.raw(f'<rect class="cursor" x="76" y="{y - 26}" width="12" height="24" fill="{FG}"/></g>')
    style = """.ln{animation:type .45s steps(28) backwards}
@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
.cursor{animation:blink 1.1s steps(1) 6s infinite}
@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.ln,.cursor{animation:none}}"""
    return s.render(style)


# ------------------------------------------------------------------ project index cards: one doodle each
def ill_rescuelens() -> str:
    return (f'<g transform="translate(0,40) scale(.36)">{car(stroke=4)}</g>'
            + "".join(rough(*seg, PENCIL, 2) for seg in [(2, 42, 18, 42), (2, 42, 2, 58), (200, 42, 184, 42), (200, 42, 200, 58),
                                                          (2, 126, 18, 126), (2, 126, 2, 110), (200, 126, 184, 126), (200, 126, 200, 110)]))


def ill_query2diagnose() -> str:
    def bubble(x, y, w, h, color, tail_left=True):
        tx = x + 16 if tail_left else x + w - 16
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#fff" stroke="{color}" stroke-width="2"/>'
                f'<path d="M{tx - 6},{y + h} L{tx},{y + h + 9} L{tx + 6},{y + h}" fill="#fff" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>'
                f'<path d="M{tx - 5},{y + h} H{tx + 5}" stroke="#fff" stroke-width="3"/>')

    def lines(x, y, widths):
        return "".join(f'<path d="M{x},{y + i * 9} h{w}" stroke="{BLUE2}" stroke-width="2.4" stroke-linecap="round"/>' for i, w in enumerate(widths))
    return (bubble(0, 4, 128, 38, BLUE) + lines(12, 18, [92, 66])
            + bubble(68, 56, 128, 36, HV, tail_left=False)
            + f'<path d="M84,68 q0,-6 6,-6 q6,0 6,6 q0,4 -6,6 v4 M90,84 v.5" fill="none" stroke="{HV}" stroke-width="2.6" stroke-linecap="round"/>'
            + lines(106, 70, [72, 48])
            + bubble(0, 108, 150, 34, BLUE)
            + f'<path d="M12,125 l6,6 l11,-12" fill="none" stroke="{BLUE}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
            + lines(40, 121, [94, 64]))


def ill_neralu() -> str:
    pts = [(0, 130), (18, 122), (36, 116), (54, 98), (72, 76), (90, 52), (108, 44), (126, 60), (144, 88), (150, 96)]
    return (rough(0, 148, 160, 148, PENCIL, 1.6) + rough(0, 148, 0, 22, PENCIL, 1.6)
            + f'<path d="M0,68 H158" stroke="{HV}" stroke-width="2.2" stroke-dasharray="6 5"/>'
            + f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{BLUE}" stroke-width="2.8" stroke-linejoin="round" stroke-linecap="round"/>'
            + f'<circle cx="79" cy="68" r="6" fill="{HV}"/>'
            + f'<path d="M166,118 L182,102 L198,118 V148 H166 Z" fill="none" stroke="{BLUE}" stroke-width="2.4" stroke-linejoin="round"/>'
            + f'<rect x="178" y="128" width="9" height="20" fill="{HV}"/>')


def ill_ultron() -> str:
    out = [rough(0, 70, 200, 70, BLUE, 2.8)]
    for n in range(19):  # one node per process
        x, y = 5 + n * 10.5, (42 if n % 2 == 0 else 98)
        out.append(f'<path d="M{x:.1f},70 V{y}" stroke="{BLUE2}" stroke-width="1.5"/>'
                   f'<circle cx="{x:.1f}" cy="{y}" r="3.8" fill="#fff" stroke="{BLUE}" stroke-width="1.9"/>')
    for k in range(5):  # hash-chained audit log
        x = 2 + k * 40
        out.append(f'<rect x="{x}" y="122" width="28" height="18" rx="4" fill="#fff" stroke="{BLUE}" stroke-width="1.9"/>')
        if k < 4:
            out.append(f'<path d="M{x + 28},131 H{x + 40}" stroke="{HV}" stroke-width="2.8" stroke-linecap="round"/>')
    return "".join(out)


def ill_dor() -> str:
    out = [f'<path d="M160,6 L186,32 L160,64 L134,32 Z M134,32 H186 M160,6 V64" fill="none" stroke="{BLUE}" stroke-width="2.4" stroke-linejoin="round"/>',
           f'<path d="M160,64 C140,94 100,88 88,110" fill="none" stroke="{HV}" stroke-width="2.6" stroke-linecap="round"/>']
    for i, x in enumerate((22, 88, 154)):  # the middle carer owns this event
        color = HV if i == 1 else BLUE
        out.append(f'<circle cx="{x}" cy="116" r="7" fill="#fff" stroke="{color}" stroke-width="2.2"/>'
                   f'<path d="M{x - 13},{140} Q{x},{122} {x + 13},{140}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>')
    return "".join(out)


def ill_voyance() -> str:
    demand = [50, 58, 72, 92, 112, 126, 120, 100, 82, 68, 62, 56]
    cap, base = 96, 146  # bookings stop at the sell-out cap; orange is the demand hidden above it
    out = [rough(0, base, 204, base, PENCIL, 1.6), rough(0, base, 0, 12, PENCIL, 1.6)]
    for i, d in enumerate(demand):
        h = min(d, cap)
        out.append(f'<rect x="{6 + i * 16.5:.1f}" y="{base - h}" width="11" height="{h}" fill="{BLUE2}" fill-opacity=".45" stroke="{BLUE}" stroke-width="1.4"/>')
    out.append(f'<path d="M0,{base - cap} H204" stroke="{PENCIL}" stroke-width="1.6" stroke-dasharray="4 4"/>')
    pts = " ".join(f"{11.5 + i * 16.5:.1f},{base - d}" for i, d in enumerate(demand))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{HV}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>')
    return "".join(out)


CARDS = [
    dict(slug="rescuelens", title="RescueLens", sub="identifies cars at crash sites", art=ill_rescuelens, tilt=-1.2,
         desc="Names a car’s make, model and year from one photo and shows rescuers where its high voltage runs. Says so when it isn’t sure.",
         result="94.55% top-1, 196 classes", foot="CV Hackathon 2026. PyTorch, YOLO11, ONNX."),
    dict(slug="query2diagnose", title="Query2Diagnose", sub="LLM agent research, co-author", art=ill_query2diagnose, tilt=1.0,
         desc="Diagnoses appliance faults from messages that mix Kannada, Hindi and English. Asks follow-ups and answers only when grounded.",
         result="0% unsafe answers", foot="RV University. LLM agents, RAG, Python."),
    dict(slug="neralu", title="Neralu", native=("ನೆರಳು", KANNADA, 400), sub="heatwave check-ins for older people", art=ill_neralu, tilt=.8,
         desc="Calls people who live alone when the heat crosses their own threshold. A worrying answer sends a volunteer to the door.",
         result="Hack4SDG 2026 finale", foot="287 tests. FastAPI, Twilio, React."),
    dict(slug="ultron", title="ULTRON", sub="a personal AI that runs locally", art=ill_ultron, tilt=-1.0,
         desc="19 Rust and Python processes on one authenticated WebSocket bus. Every event lands in a hash-chained audit log.",
         result="337 tests", foot="Personal project. Rust, Python, Ollama."),
    dict(slug="dor", title="Dor", native=("डोर", HAND, 700), sub="care coordination for families", art=ill_dor, tilt=-.8,
         desc="Every missed dose, refill and doctor visit gets one responsible person, with escalation. The elder approves changes.",
         result="accessibility score 100", foot="Elder-care hackathon. Next.js, Postgres, Gemini."),
    dict(slug="voyance", title="Voyance", sub="hotel inventory planning", art=ill_voyance, tilt=1.2,
         desc="Decides which hotel-weeks to pre-buy on a budget. Recovers demand hidden by sell-outs and weighs the risk of unsold rooms.",
         result="+14–24% profit (simulated)", foot="TBO VoyageHack 4.0. Python, SciPy, FastAPI."),
]


def card(c: dict) -> str:
    W, H = 600, 400
    cx0, cy0, cw, ch = 22, 30, 556, 344
    s = Svg(W, H, f'Index card. {c["title"]}: {c["sub"]}. {c["desc"]} Key result: {c["result"]}. {c["foot"]}')
    s.raw(f'<g transform="rotate({c["tilt"]} {W / 2} {H / 2})">')
    s.raw(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" fill="{PAPER}" filter="url(#lift)"/>')
    s.raw(f'<path d="M{cx0},{cy0 + 62} H{cx0 + cw}" stroke="#eba0a0" stroke-width="1.6"/>')
    for k in range(9):
        y = cy0 + 92 + k * 30
        if y < cy0 + ch - 4:
            s.raw(f'<path d="M{cx0},{y} H{cx0 + cw}" stroke="#cddff3" stroke-width="1.2"/>')
    s.text(cx0 + 22, cy0 + 50, c["title"], 36, weight=700)
    if c.get("native"):
        word, family, weight = c["native"]
        s.text(cx0 + 34 + measure(c["title"], 36, 700), cy0 + 48, word, 26, weight=weight, family=family, fill=PENCIL)
    s.raw(f'<g transform="translate({cx0 + cw - 228},{cy0 + 78})" filter="url(#wobble)">{c["art"]()}</g>')
    s.text(cx0 + 22, cy0 + 88, c["sub"], 21, fill=PENCIL)
    desc = wrap_widths(c["desc"], 21, [300, 300, 300, 300, cw - 44])
    assert len(desc) <= 5, f'{c["slug"]}: description runs to {len(desc)} lines'
    for i, line in enumerate(desc):
        s.text(cx0 + 22, cy0 + 118 + i * 30, line, 21, fill="#22252c")
    ry = cy0 + 118 + len(desc) * 30 + 8
    rw = measure("→ " + c["result"], 23, 700)
    s.raw(highlight(cx0 + 22, ry, rw))
    s.text(cx0 + 22, ry, "→ " + c["result"], 23, weight=700, fill="#22252c")
    s.text(cx0 + 22, cy0 + ch - 16, c["foot"], 19, fill=PENCIL)
    assert ry < cy0 + ch - 44, f'{c["slug"]}: result line collides with the footer'
    s.raw("</g>")
    s.raw(tape(W / 2, cy0 + 2, angle=-3 if c["tilt"] > 0 else 3))
    return s.render()


# ------------------------------------------------------------------ toolbox: sticky notes
STICKIES = [
    ("languages", ["Python", "TypeScript", "Rust", "Kotlin", "Java", "SQL"], "#fff3a3", -2.5),
    ("ML and AI", ["PyTorch", "scikit-learn", "XGBoost", "LightGBM", "YOLO", "OpenCV", "ONNX", "LLM agents", "RAG", "Whisper"], "#ffd9e2", 1.8),
    ("backend and web", ["FastAPI", "Flask", "Next.js", "React", "Tailwind", "PostgreSQL", "SQLite", "Firebase", "Twilio"], "#d8ecff", -1.2),
    ("ops and cloud", ["Docker", "GitHub Actions", "pytest", "Modal", "Vercel", "Hugging Face"], "#dcf5d3", 2.2),
    ("finance", ["DCF valuation", "backtesting", "CVaR", "linear programming"], "#ffe3c7", -1.6),
]


def stickies() -> str:
    W, H, size = 1200, 300, 222
    s = Svg(W, H, "Toolbox. " + " ".join(f'{k}: {", ".join(v)}.' for k, v, _, _ in STICKIES))
    for i, (label, items, color, tilt) in enumerate(STICKIES):
        x, y = 14 + i * 236, 40
        s.raw(f'<g transform="rotate({tilt} {x + size / 2} {y + size / 2})">'
              f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="{color}" filter="url(#lift)"/>')
        s.text(x + 16, y + 38, label, 24, weight=700)
        s.raw(rough(x + 16, y + 48, x + 16 + measure(label, 24, 700), y + 47, BLUE, 1.8))
        lines = wrap_widths(", ".join(items), 19, [size - 30])
        assert len(lines) <= 6, f"sticky '{label}' overflows"
        for k, line in enumerate(lines):
            s.text(x + 16, y + 80 + k * 26, line, 19, fill="#22252c")
        s.raw("</g>")
    return s.render()


def button(label: str, live: bool) -> str:
    w = measure(label, 22, 700) + (66 if live else 44)
    s = Svg(round(w) + 8, 60, label)
    s.raw(f'<rect x="4" y="6" width="{w:.0f}" height="46" rx="4" fill="{PAPER}"/>')
    s.raw(rough_rect(4, 6, w, 46, BLUE, 2))
    if live:
        s.raw(f'<circle cx="30" cy="29" r="6" fill="{HV}"/>')
    s.text(48 if live else 26, 37, label, 22, weight=700)
    return s.render()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    files = {"hero.svg": hero(), "terminal.svg": terminal(), "toolbox.svg": stickies(),
             "btn-linkedin.svg": button("connect on LinkedIn", False),
             "btn-rescuelens.svg": button("try RescueLens live", True),
             "btn-dor.svg": button("try Dor live", True)}
    files.update({f"card-{c['slug']}.svg": card(c) for c in CARDS})
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name} ({len(svg) / 1024:.0f} KB)")
