"""Build the SVG images used by the profile README.

Run:  python tools/make_assets.py   (writes assets/*.svg)

Design: blueprint sheets (engineering drawing), one high-voltage orange that only
ever marks the thing a system guards against, Overpass type embedded as subset
fonts so it renders the same everywhere. Every number comes from the resume:
change it here, never in the SVGs.
"""
import base64
import io
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
SANS, KANNADA, DEVANAGARI = "Overpass", "Noto Sans Kannada", "Noto Sans Devanagari"
FONT_FILES = {SANS: "Overpass.ttf", KANNADA: "NotoSansKannada.ttf", DEVANAGARI: "NotoSansDevanagari.ttf"}
FALLBACK = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

PAPER_A, PAPER_B = "#1f4689", "#153267"
INK, INK2, INK3 = "#f3f7ff", "#b9cdef", "#7f9dd0"
HV = "#ff8c2b"          # EV high-voltage orange: marks what the system guards against
CHIP = "#122b5a"

DEFS = f"""
<linearGradient id="paper" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{PAPER_A}"/><stop offset="1" stop-color="{PAPER_B}"/></linearGradient>
<pattern id="minor" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#fff" stroke-opacity=".05"/></pattern>
<pattern id="grid" width="120" height="120" patternUnits="userSpaceOnUse"><rect width="120" height="120" fill="url(#minor)"/><path d="M120 0H0V120" fill="none" stroke="#fff" stroke-opacity=".1"/></pattern>
<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="{HV}" stroke-width="1.6" stroke-opacity=".75"/></pattern>"""


# ------------------------------------------------------------------ fonts
@lru_cache(None)
def _instance_bytes(family: str, weight: int) -> bytes:
    font = TTFont(FONT_DIR / FONT_FILES[family])
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


def measure(s: str, size: float, weight: int = 400, family: str = SANS) -> float:
    """Advance width from the real font (kerning ignored, which is close enough for layout)."""
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


def wrap(s: str, size: float, max_w: float, weight: int = 400) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if measure(trial, size, weight) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def wrap_balanced(s: str, size: float, max_w: float, weight: int = 400) -> list[str]:
    """Like CSS text-wrap: balance. Same line count as a greedy wrap, but no single stray word on the last line."""
    n = len(wrap(s, size, max_w, weight))
    lo, hi = max_w * .4, max_w
    while hi - lo > 1:
        mid = (lo + hi) / 2
        if len(wrap(s, size, mid, weight)) == n:
            hi = mid
        else:
            lo = mid
    return wrap(s, size, hi, weight)


# ------------------------------------------------------------------ svg builder
class Svg:
    def __init__(self, w: int, h: int, label: str):
        self.w, self.h, self.label = w, h, label
        self.parts: list[str] = []
        self.used: dict[tuple[str, int], set[str]] = defaultdict(set)

    def raw(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, size, *, weight=400, fill=INK, anchor="start", family=SANS, cls=""):
        self.used[(family, weight)].update(s)
        extra = f' class="{cls}"' if cls else ""
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="\'{family}\', {FALLBACK}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')

    def render(self, style: str = "") -> str:
        faces = "".join(font_face(f, w, "".join(sorted(ch))) for (f, w), ch in sorted(self.used.items()))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.label)}">\n'
                f'<title>{escape(self.label)}</title>\n<defs>{DEFS}\n</defs>\n<style>{faces}\n{style}</style>\n'
                + "\n".join(self.parts) + "\n</svg>\n")


def paper(svg: Svg, r: int = 14) -> None:
    w, h = svg.w, svg.h
    svg.raw(f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#paper)"/>')
    svg.raw(f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#grid)"/>')
    svg.raw(f'<rect x="10.5" y="10.5" width="{w - 21}" height="{h - 21}" rx="{r - 6}" fill="none" stroke="{INK3}" stroke-opacity=".6"/>')


def brackets(x0, y0, x1, y1, length=20, color=HV, width=3) -> str:
    corners = [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]
    return "".join(
        f'<path d="M{x},{y + dy * length} V{y} H{x + dx * length}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>' for x, y, dx, dy in corners)


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


def car(cls_body="", cls_detail="", cls_hv="", line=INK, detail=INK2, stroke=2.4) -> str:
    def path(d, color, width, cls):
        c = f' class="{cls}"' if cls else ""
        return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" '
                f'stroke-linecap="round" pathLength="1"{c}/>')
    out = [path(CAR_BODY, line, stroke, cls_body)]
    out += [path(d, line, stroke, cls_body) for d in WHEELS]
    out += [path(d, detail, stroke * .75, cls_detail) for d in CAR_DETAIL]
    fill_cls = ' class="hv-fill"' if cls_hv else ""
    out.append(f'<path d="{HV_BATTERY}" fill="url(#hatch)" stroke="none"{fill_cls}/>')
    out += [path(d, HV, stroke * 1.15, cls_hv) for d in (HV_BATTERY, HV_CABLE, HV_MOTOR)]
    return "\n".join(out)


# ------------------------------------------------------------------ hero
def hero() -> str:
    W, H = 1200, 480
    s = Svg(W, H, "Priyanshu Kumar Senapati, AI/ML and software engineer. I build AI that knows when it's wrong. "
                  "Drawing: RescueLens locks onto a car and marks where its high voltage runs.")
    paper(s)
    size = 72
    while max(measure(t, size, 800) for t in ("Priyanshu Kumar", "Senapati")) > 560:
        size -= 2
    s.text(64, 136, "Priyanshu Kumar", size, weight=800)
    s.text(64, 136 + size * 1.05, "Senapati", size, weight=800)
    s.text(66, 270, "I build AI that knows when it’s wrong.", 28, weight=500, fill=INK2)
    for i, line in enumerate(["On the right: RescueLens, my crash-rescue model, locks onto",
                              "a car, names it, and marks where its high voltage runs."]):
        s.text(66, 404 + i * 24, line, 15.5, fill=INK2)

    tx, ty, k = 656, 60, .9  # car placement
    s.raw(f'<g transform="translate({tx},{ty}) scale({k})">')
    s.raw(f'<path d="M0,202 H560" stroke="{INK3}" stroke-dasharray="18 5 3 5" stroke-width="1.2"/>')
    for cx in (120, 440):
        s.raw(f'<path d="M{cx - 8},168 H{cx + 8} M{cx},160 V176" stroke="{INK3}" stroke-width="1.2"/>')
    s.raw(car("d", "d d2", "d hv"))
    s.raw("</g>")
    fx0, fy0, fx1, fy1 = 662, 92, 1156, 258
    s.raw(f'<g class="lock">{brackets(fx0, fy0, fx1, fy1)}</g>')

    s.raw('<g class="rise">')
    tag_w = measure("Identified", 15, 700) + measure("94.55% top-1 across 196 classes", 15, 400) + 40
    s.raw(f'<rect x="{fx0}" y="52" width="{tag_w:.0f}" height="30" rx="6" fill="{CHIP}" stroke="{HV}" stroke-opacity=".8"/>')
    s.text(fx0 + 14, 72, "Identified", 15, weight=700)
    s.text(fx0 + 24 + measure("Identified", 15, 700), 72, "94.55% top-1 across 196 classes", 15, fill=INK2)
    bx, by = tx + 279 * k, ty + 156 * k
    cx, cy = tx + 432 * k, ty + 136 * k
    s.raw(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="4" fill="{HV}"/><path d="M{bx:.0f},{by:.0f} V290" stroke="{INK2}" stroke-width="1.2"/>')
    s.raw(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="4" fill="{HV}"/><path d="M{cx:.0f},{cy:.0f} L1110,290" stroke="{INK2}" stroke-width="1.2"/>')
    s.text(bx, 308, "High-voltage battery", 15, weight=600, anchor="middle")
    s.text(1156, 308, "High-voltage cable", 15, weight=600, anchor="end")
    s.raw("</g>")

    rows = [("Role", "AI/ML and software engineer"),
            ("Studying", "B.Tech CSE (AI & ML), RV University, 2028"),
            ("Based in", "Bengaluru, India"),
            ("Looking for", "AI/ML and software internships, 2027")]
    x0, y0, label_w, row_h, w = 662, 344, 108, 26, 494
    s.raw(f'<rect x="{x0}" y="{y0}" width="{w}" height="{row_h * len(rows)}" fill="{PAPER_B}" fill-opacity=".55" stroke="{INK2}" stroke-opacity=".8"/>')
    s.raw(f'<path d="M{x0 + label_w},{y0} V{y0 + row_h * len(rows)}" stroke="{INK2}" stroke-opacity=".6"/>')
    for i, (key, val) in enumerate(rows):
        y = y0 + i * row_h
        if i:
            s.raw(f'<path d="M{x0},{y} H{x0 + w}" stroke="{INK2}" stroke-opacity=".35"/>')
        s.text(x0 + 10, y + 18, key, 13, fill=INK2)
        s.text(x0 + label_w + 12, y + 18, val, 14.5, weight=600)
        assert x0 + label_w + 12 + measure(val, 14.5, 600) < x0 + w - 6, f"title block value too wide: {val}"

    style = """
.d{stroke-dasharray:1 1.1;animation:draw 1.5s cubic-bezier(.4,0,.2,1) .2s backwards}
.d2{animation-duration:.8s;animation-delay:1s}
.hv{animation-duration:.9s;animation-delay:1.7s}
.hv-fill{animation:fade .5s ease-out 2.4s backwards}
@keyframes draw{from{stroke-dashoffset:1.05}}  /* past 1 so round caps don't show as dots */
.lock{transform-box:fill-box;transform-origin:center;animation:lock .45s cubic-bezier(.2,.8,.2,1) 2.5s backwards}
@keyframes lock{from{opacity:0;transform:scale(1.12)}}
.rise{animation:rise .5s ease-out 2.9s backwards}
@keyframes rise{from{opacity:0;transform:translateY(6px)}}
@keyframes fade{from{opacity:0}}
@media (prefers-reduced-motion:reduce){.d,.hv-fill,.lock,.rise{animation:none}}"""
    return s.render(style)


# ------------------------------------------------------------------ results table
RESULT_ROWS = [
    ("RescueLens", "Top-1 accuracy on 196 car classes", "94.55%"),
    ("", "Unseen cars it refused to guess on", "58 of 60"),
    ("Query2Diagnose", "Unsafe answers on 300 test cases", "0%"),
    ("Voyance", "Expected profit vs re-buying last year’s bookings (simulated)", "+14–24%"),
    ("Four projects", "Automated tests", "790"),
    ("Competitions", "Hackathons and build sprints", "10"),
]
TESTS = [("ULTRON", 337), ("Neralu", 287), ("RescueLens", 94), ("Voyance", 72)]
assert sum(n for _, n in TESTS) == 790


def results() -> str:
    rows_h, top = 64, 58
    s = Svg(1200, top + rows_h * len(RESULT_ROWS) + 22,
            "Results. RescueLens: 94.55% top-1 accuracy on 196 car classes; refused to guess on 58 of 60 unseen cars. "
            "Query2Diagnose: 0% unsafe answers on 300 cases, LLM baselines 43 to 70%. Voyance: 14 to 24% more expected "
            "profit than re-buying last year's bookings, in simulation. 790 automated tests across four projects "
            "(ULTRON 337, Neralu 287, RescueLens 94, Voyance 72). 10 hackathons and build sprints, 2 finales.")
    paper(s)
    COL_P, COL_M, COL_R, C0, C1 = 44, 228, 742, 786, 1152
    span = C1 - C0
    for x, label, anchor in [(COL_P, "Project", "start"), (COL_M, "What was measured", "start"),
                             (COL_R, "Result", "end"), (C0, "Shown as", "start")]:
        s.text(x, 44, label, 14, fill=INK2, anchor=anchor)
    s.raw(f'<path d="M{COL_P},{top - 4} H{C1}" stroke="{INK2}" stroke-opacity=".7"/>')

    def track(y, ticks=("0", "100%")):
        s.raw(f'<rect x="{C0}" y="{y - 4}" width="{span}" height="8" rx="4" fill="{INK3}" fill-opacity=".28"/>')
        s.text(C0, y + 25, ticks[0], 13, fill=INK2)
        s.text(C1, y + 25, ticks[1], 13, fill=INK2, anchor="end")

    for i, (proj, what, res) in enumerate(RESULT_ROWS):
        y = top + i * rows_h
        mid = y + rows_h / 2
        if i:
            s.raw(f'<path d="M{COL_P},{y} H{C1}" stroke="{INK2}" stroke-opacity=".22"/>')
        if proj:
            s.text(COL_P, mid + 6, proj, 18, weight=700)
        lines = wrap_balanced(what, 16.5, COL_R - COL_M - 120)
        for j, line in enumerate(lines):
            s.text(COL_M, mid + 6 + (j - (len(lines) - 1) / 2) * 21, line, 16.5, fill=INK2)
        s.text(COL_R, mid + 9, res, 26, weight=800, anchor="end")
        if i == 0:
            track(mid - 6)
            s.raw(f'<rect x="{C0}" y="{mid - 10}" width="{span * .9455:.1f}" height="8" rx="4" fill="{HV}"/>')
        elif i == 1:
            sq, gap = 9, 3.2
            for n in range(60):
                x, yy = C0 + (n % 30) * (sq + gap), mid - 14 + (n // 30) * (sq + gap)
                fill = f'fill="{HV}"' if n < 58 else f'fill="none" stroke="{INK2}" stroke-width="1.4"'
                s.raw(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{sq}" height="{sq}" rx="2" {fill}/>')
        elif i == 2:
            track(mid - 6)
            x43, x70 = C0 + span * .43, C0 + span * .70
            s.raw(f'<rect x="{x43:.1f}" y="{mid - 10}" width="{x70 - x43:.1f}" height="8" rx="4" fill="{INK2}" fill-opacity=".75"/>')
            s.text((x43 + x70) / 2, mid - 18, "LLM baselines, 43–70%", 13.5, fill=INK2, anchor="middle")
            s.raw(f'<circle cx="{C0 + 5}" cy="{mid - 6}" r="7" fill="{HV}" stroke="{PAPER_A}" stroke-width="2"/>')
        elif i == 3:
            track(mid - 6, ticks=("0", "30%"))
            x14, x24 = C0 + span * 14 / 30, C0 + span * 24 / 30
            s.raw(f'<rect x="{x14:.1f}" y="{mid - 10}" width="{x24 - x14:.1f}" height="8" rx="4" fill="{HV}"/>')
        elif i == 4:
            total, x = sum(n for _, n in TESTS), C0
            for k, (name, n) in enumerate(TESTS):
                w = span * n / total - 2
                s.raw(f'<rect x="{x:.1f}" y="{mid - 10}" width="{w:.1f}" height="8" rx="3" fill="{HV}"/>')
                label = f"{name} {n}"
                if k == len(TESTS) - 1:
                    s.text(C1, mid + 15, label, 13.5, fill=INK2, anchor="end")
                elif k == 2:
                    s.text(x, mid - 18, label, 13.5, fill=INK2)
                else:
                    s.text(x, mid + 15, label, 13.5, fill=INK2)
                x += w + 2
        elif i == 5:
            for n in range(10):
                dot = f'fill="{HV}"' if n < 2 else f'fill="none" stroke="{INK2}" stroke-width="1.6"'
                s.raw(f'<circle cx="{C0 + 8 + n * 22}" cy="{mid - 6}" r="7" {dot}/>')
            s.text(C0 + 8 + 10 * 22 + 2, mid - 1, "2 reached the finale", 14, fill=INK2)
    return s.render()


# ------------------------------------------------------------------ project sheets: one line drawing each
def ill_rescuelens() -> str:
    return (f'<g transform="translate(-4,22) scale(.38)">{car(line=INK, detail=INK2, stroke=3.4)}</g>'
            + brackets(2, 34, 210, 108, length=14, width=2.4))


def ill_query2diagnose() -> str:
    def bubble(x, y, w, h, tail_left=True, stroke=INK2):
        tx = x + 16 if tail_left else x + w - 16
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{CHIP}" stroke="{stroke}" stroke-width="1.6"/>'
                f'<path d="M{tx - 6},{y + h} L{tx},{y + h + 9} L{tx + 6},{y + h}" fill="{CHIP}" stroke="{stroke}" stroke-width="1.6" stroke-linejoin="round"/>'
                f'<path d="M{tx - 5},{y + h} H{tx + 5}" stroke="{CHIP}" stroke-width="2.4"/>')

    def lines(x, y, widths):
        return "".join(f'<path d="M{x},{y + i * 9} h{w}" stroke="{INK2}" stroke-width="2.4" stroke-linecap="round"/>'
                       for i, w in enumerate(widths))
    return (bubble(0, 6, 132, 40) + lines(12, 20, [96, 70])
            + bubble(82, 60, 128, 36, tail_left=False, stroke=HV)
            + f'<path d="M100,72 q0,-6 6,-6 q6,0 6,6 q0,4 -6,6 v4 M106,88 v.5" fill="none" stroke="{HV}" stroke-width="2.6" stroke-linecap="round"/>'
            + lines(122, 74, [70, 48])
            + bubble(0, 112, 150, 36)
            + f'<path d="M12,130 l6,6 l11,-12" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
            + lines(40, 126, [94, 66]))


def ill_neralu() -> str:
    pts = [(0, 132), (18, 124), (36, 118), (54, 100), (72, 78), (90, 54), (108, 46), (126, 62), (144, 90), (160, 104)]
    return (f'<path d="M0,150 H168 M0,150 V20" stroke="{INK3}" stroke-width="1.4"/>'
            f'<path d="M0,70 H168" stroke="{HV}" stroke-width="2" stroke-dasharray="6 5"/>'
            f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="81" cy="70" r="5.5" fill="{HV}"/>'
            f'<path d="M176,118 L194,102 L212,118 V150 H176 Z" fill="none" stroke="{INK2}" stroke-width="2" stroke-linejoin="round"/>'
            f'<rect x="189" y="130" width="10" height="20" fill="{HV}"/>')


def ill_ultron() -> str:
    out = [f'<path d="M0,72 H212" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>']
    for n in range(19):  # one node per process
        x, y = 6 + n * 11.1, (44 if n % 2 == 0 else 100)
        out.append(f'<path d="M{x:.1f},72 V{y}" stroke="{INK2}" stroke-width="1.4"/>'
                   f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="{CHIP}" stroke="{INK}" stroke-width="1.8"/>')
    for k in range(5):  # hash-chained audit log
        x = 4 + k * 42
        out.append(f'<rect x="{x}" y="128" width="30" height="18" rx="4" fill="none" stroke="{INK2}" stroke-width="1.8"/>')
        if k < 4:
            out.append(f'<path d="M{x + 30},137 H{x + 42}" stroke="{HV}" stroke-width="2.6" stroke-linecap="round"/>')
    return "".join(out)


def ill_dor() -> str:
    out = [f'<path d="M170,8 L196,34 L170,66 L144,34 Z M144,34 H196 M170,8 V66" fill="none" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>',
           f'<path d="M170,66 C150,96 110,90 98,112" fill="none" stroke="{HV}" stroke-width="2.4" stroke-linecap="round"/>']
    for i, (x, y) in enumerate([(30, 132), (98, 132), (166, 132)]):  # the middle carer owns this event
        color = HV if i == 1 else INK2
        out.append(f'<circle cx="{x}" cy="{y - 14}" r="7" fill="none" stroke="{color}" stroke-width="2"/>'
                   f'<path d="M{x - 13},{y + 10} Q{x},{y - 8} {x + 13},{y + 10}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>')
    return "".join(out)


def ill_voyance() -> str:
    demand = [52, 60, 74, 96, 118, 132, 126, 104, 84, 70, 64, 58]
    cap, base = 100, 150  # bookings stop at the sell-out cap; the orange line is the demand hidden above it
    out = [f'<path d="M0,150 H212 M0,150 V10" stroke="{INK3}" stroke-width="1.4"/>']
    for i, d in enumerate(demand):
        h = min(d, cap)
        out.append(f'<rect x="{6 + i * 17}" y="{base - h}" width="12" height="{h}" rx="2" fill="{INK2}" fill-opacity=".55"/>')
    out.append(f'<path d="M0,{base - cap} H212" stroke="{INK}" stroke-width="1.6" stroke-dasharray="4 4"/>')
    pts = " ".join(f"{12 + i * 17},{base - d}" for i, d in enumerate(demand))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{HV}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>')
    return "".join(out)


CARDS = [
    dict(slug="rescuelens", title="RescueLens", sub="Identifies cars at crash sites", art=ill_rescuelens,
         desc="Names a car’s make, model and year from one photo and shows rescuers where its high voltage runs. When it isn’t sure, it says so instead of guessing.",
         cells=[("Built for", "CV Hackathon 2026"), ("Key result", "94.55% top-1"), ("Built with", "PyTorch, YOLO11, ONNX")]),
    dict(slug="query2diagnose", title="Query2Diagnose", sub="LLM agent research, co-author", art=ill_query2diagnose,
         desc="Diagnoses appliance faults from code-mixed Kannada/Hindi–English messages. It asks follow-up questions and answers only when the answer is grounded.",
         cells=[("Built for", "RV University"), ("Key result", "0% unsafe answers"), ("Built with", "LLM agents, RAG")]),
    dict(slug="neralu", title="Neralu", native=("ನೆರಳು", KANNADA), sub="Heatwave check-ins for older people", art=ill_neralu,
         desc="Calls people who live alone when the heat crosses their own threshold, in Kannada, Hindi or English. A worrying answer sends a volunteer to the door.",
         cells=[("Built for", "Hack4SDG 2026 finale"), ("Key result", "287 tests"), ("Built with", "FastAPI, Twilio, React")]),
    dict(slug="ultron", title="ULTRON", sub="A personal AI system that runs locally", art=ill_ultron,
         desc="19 Rust and Python processes share one authenticated WebSocket bus, each its own failure domain. Every event lands in a hash-chained audit log.",
         cells=[("Built for", "Personal project"), ("Key result", "337 tests"), ("Built with", "Rust, Python, Ollama")]),
    dict(slug="dor", title="Dor", native=("डोर", DEVANAGARI), sub="Care coordination for families", art=ill_dor,
         desc="Every missed dose, refill and doctor visit gets one responsible person, with escalation and duplicate-medicine checks. The elder approves changes.",
         cells=[("Built for", "Elder-care hackathon"), ("Key result", "Accessibility 100"), ("Built with", "Next.js, Postgres, Gemini")]),
    dict(slug="voyance", title="Voyance", sub="Hotel inventory planning", art=ill_voyance,
         desc="Decides which hotel-weeks to pre-buy on a budget. It recovers demand hidden by sell-outs and weighs profit against the risk of unsold rooms.",
         cells=[("Built for", "TBO VoyageHack 4.0"), ("Key result", "+14–24% (sim.)"), ("Built with", "Python, SciPy, FastAPI")]),
]


def card(c: dict) -> str:
    W, H, pad = 600, 372, 34
    s = Svg(W, H, f'{c["title"]}: {c["sub"]}. {c["desc"]} ' + " ".join(f"{k}: {v}." for k, v in c["cells"]))
    paper(s)
    s.raw(f'<g transform="translate(356,30)">{c["art"]()}</g>')
    s.text(pad, 78, c["title"], 36, weight=800)
    y = 108
    if c.get("native"):
        word, family = c["native"]
        s.text(pad, y, word, 21, weight=600, family=family, fill=INK2)
        y += 30
    for i, line in enumerate(wrap(c["sub"], 16.5, 300, 500)):
        s.text(pad, y + i * 22, line, 16.5, weight=500, fill=INK2)
    desc = wrap_balanced(c["desc"], 16.5, W - 2 * pad)
    assert len(desc) <= 3, f'{c["slug"]}: description runs to {len(desc)} lines'
    for i, line in enumerate(desc):
        s.text(pad, 214 + i * 23, line, 16.5)
    bx, by, bw, bh = pad, 290, W - 2 * pad, 50
    s.raw(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{PAPER_B}" fill-opacity=".55" stroke="{INK2}" stroke-opacity=".8"/>')
    x = bx
    for (key, val), frac in zip(c["cells"], [.345, .29, .365]):
        cw = bw * frac
        if x > bx:
            s.raw(f'<path d="M{x:.1f},{by} V{by + bh}" stroke="{INK2}" stroke-opacity=".6"/>')
        s.text(x + 12, by + 19, key, 12.5, fill=INK2)
        s.text(x + 12, by + 40, val, 14.5, weight=700)
        assert measure(val, 14.5, 700) < cw - 18, f'{c["slug"]}: "{val}" too wide for its cell'
        x += cw
    return s.render()


# ------------------------------------------------------------------ toolbox and buttons
TOOLBOX = [
    ("Languages", "Python, TypeScript, Rust, Kotlin, Java, SQL"),
    ("ML and AI", "PyTorch, scikit-learn, XGBoost, LightGBM, YOLO, OpenCV, ONNX, LLM agents, RAG, Whisper"),
    ("Backend and web", "FastAPI, Flask, Next.js, React, Tailwind CSS, PostgreSQL, SQLite, Firebase, Twilio"),
    ("Ops and cloud", "Docker, GitHub Actions, pytest, Modal, Vercel, Hugging Face"),
    ("Finance", "DCF valuation, backtesting, CVaR, linear programming"),
]


def toolbox() -> str:
    row_h, top = 52, 26
    s = Svg(1200, top * 2 + row_h * len(TOOLBOX), "Toolbox. " + " ".join(f"{k}: {v}." for k, v in TOOLBOX))
    paper(s)
    for i, (key, val) in enumerate(TOOLBOX):
        y = top + i * row_h
        if i:
            s.raw(f'<path d="M44,{y} H1156" stroke="{INK2}" stroke-opacity=".22"/>')
        s.text(44, y + 33, key, 18, weight=700)
        s.text(240, y + 33, val, 18, fill=INK2)
        assert 240 + measure(val, 18) < 1156, f"toolbox row too long: {key}"
    return s.render()


def button(label: str, live: bool) -> str:
    w = measure(label, 17, 700) + (64 if live else 44)
    s = Svg(round(w), 52, label)
    s.raw(f'<rect width="{w:.0f}" height="52" rx="10" fill="url(#paper)"/>')
    s.raw(f'<rect x=".75" y=".75" width="{w - 1.5:.1f}" height="50.5" rx="9.5" fill="none" stroke="{HV if live else INK2}" stroke-width="1.5"/>')
    if live:
        s.raw(f'<circle cx="26" cy="26" r="5" fill="{HV}"/>')
    s.text(42 if live else 22, 32, label, 17, weight=700)
    return s.render()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    files = {"hero.svg": hero(), "results.svg": results(), "toolbox.svg": toolbox(),
             "btn-linkedin.svg": button("Connect on LinkedIn", False),
             "btn-rescuelens.svg": button("Try RescueLens live", True),
             "btn-dor.svg": button("Try Dor live", True)}
    files.update({f"card-{c['slug']}.svg": card(c) for c in CARDS})
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name} ({len(svg) / 1024:.0f} KB)")
