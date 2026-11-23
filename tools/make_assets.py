"""Build the SVG images used by the profile README.

Run:  python tools/make_assets.py   (writes assets/*.svg)
Every number here is taken from the resume; change it here, not in the SVGs.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

BG_A, BG_B = "#0a1424", "#10233f"
CARD, EDGE = "#0d1b30", "#1f3556"
TEXT, BODY, MUTED = "#eef3fa", "#c3d0e2", "#8ea3bf"
BLUE, TEAL, GOLD, CORAL = "#4f9dff", "#38d6c4", "#f0b45a", "#ff7a7a"


def text_width(s: str, size: float, bold: bool = False) -> float:
    """Rough rendered width; shortcut: per-glyph estimate, good enough to size chips and wrap lines."""
    narrow, wide = set("iljtfr.,:;|!' ()[]/·-"), set("mwMW%@")
    w = 0.0
    for ch in s:
        if ch in narrow:
            w += 0.32
        elif ch in wide:
            w += 0.86
        elif ch.isupper() or ch.isdigit():
            w += 0.64 if ch.isupper() else 0.57
        else:
            w += 0.53
    return w * size * (1.07 if bold else 1.0)


def wrap(s: str, size: float, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if text_width(trial, size) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def defs() -> str:
    return f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG_A}"/><stop offset="1" stop-color="{BG_B}"/></linearGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{TEAL}"/></linearGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#ffffff" opacity=".07"/></pattern>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{BLUE}" stop-opacity=".28"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
</defs>"""


def chip(x: float, y: float, label: str, color: str, size: float = 14, filled: bool = False) -> tuple[str, float]:
    w = text_width(label, size, bold=True) + 22
    fill = color if filled else "none"
    fill_op = ".16" if filled else "0"
    svg = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{size + 12}" rx="{(size + 12) / 2}" '
           f'fill="{fill}" fill-opacity="{fill_op}" stroke="{color}" stroke-opacity=".55"/>'
           f'<text x="{x + w / 2:.1f}" y="{y + size + 4.5}" text-anchor="middle" font-size="{size}" '
           f'font-weight="600" fill="{color}">{escape(label)}</text>')
    return svg, w


def svg_doc(w: int, h: int, body: str, title: str, style: str = "") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}" font-family="{FONT}">\n<title>{escape(title)}</title>\n'
            f'{defs()}\n<style>{style}</style>\n{body}\n</svg>\n')


# ---------------------------------------------------------------- banner
CAR = ("M20,78 L20,62 Q22,56 45,54 L78,36 Q85,32 95,32 L150,32 Q160,32 168,38 L192,54 L238,58 "
       "Q252,60 254,68 L254,78 L224,78 A19,19 0 0 0 186,78 L89,78 A19,19 0 0 0 51,78 Z")


def verdict(cls: str, x: float, y: float, mark: str, label: str, color: str) -> str:
    c, _ = chip(x, y, f"{mark}  {label}", color, 15, filled=True)
    return f'<g class="{cls}">{c}</g>'


def banner() -> str:
    style = """
    .scan{animation:scan 3.4s ease-in-out infinite alternate}
    @keyframes scan{from{transform:translateY(0)}to{transform:translateY(164px)}}
    .v1,.v2,.v3{animation:cycle 9s linear infinite}
    .v2,.v3{opacity:0}
    .v2{animation-delay:-6s}.v3{animation-delay:-3s}
    @keyframes cycle{0%,28%{opacity:1}33%,95%{opacity:0}100%{opacity:1}}
    .rise{animation:rise 1s ease-out both}
    @keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
    @media (prefers-reduced-motion:reduce){.scan,.v1,.v2,.v3,.rise{animation:none}}"""
    fx, fy, fw, fh = 812, 58, 330, 196  # detection frame
    b = 18  # bracket length
    brackets = "".join(
        f'<path d="M{x},{y + dy * b} L{x},{y} L{x + dx * b},{y}" fill="none" stroke="{TEAL}" stroke-width="3" stroke-linecap="round"/>'
        for x, y, dx, dy in [(fx, fy, 1, 1), (fx + fw, fy, -1, 1), (fx, fy + fh, 1, -1), (fx + fw, fy + fh, -1, -1)])
    body = f"""
<rect width="1200" height="320" rx="20" fill="url(#bg)"/>
<rect width="1200" height="320" rx="20" fill="url(#dots)"/>
<circle cx="980" cy="150" r="260" fill="url(#glow)"/>
<rect x="1" y="1" width="1198" height="318" rx="19" fill="none" stroke="{EDGE}"/>
<g class="rise">
  <text x="64" y="86" font-size="15" font-weight="600" letter-spacing="3" fill="{MUTED}">HI, I'M</text>
  <text x="62" y="138" font-size="46" font-weight="700" fill="{TEXT}">Priyanshu Kumar Senapati</text>
  <text x="64" y="180" font-size="23" font-weight="600" fill="url(#accent)">AI/ML &amp; Software Engineer</text>
  <text x="64" y="222" font-size="23" fill="{BODY}">I build AI that knows when it’s wrong.</text>
  <text x="64" y="262" font-size="16" fill="{MUTED}">B.Tech CSE (AI &amp; ML) · RV University ’28 · Bengaluru, India</text>
</g>
<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="6" fill="#0b1a2e" fill-opacity=".55"/>
{brackets}
<g transform="translate(842,96) scale(1.0)">
  <path d="{CAR}" fill="none" stroke="{BODY}" stroke-width="2.4" stroke-linejoin="round"/>
  <path d="M84,52 L99,38 L146,38 L160,52 Z" fill="none" stroke="{MUTED}" stroke-width="1.8" stroke-linejoin="round"/>
  <line x1="122" y1="38" x2="122" y2="52" stroke="{MUTED}" stroke-width="1.8"/>
  <circle cx="70" cy="78" r="14" fill="none" stroke="{BODY}" stroke-width="2.4"/>
  <circle cx="205" cy="78" r="14" fill="none" stroke="{BODY}" stroke-width="2.4"/>
  <path d="M232,66 L246,64" stroke="{GOLD}" stroke-width="2.4" stroke-linecap="round"/>
</g>
<g class="scan"><rect x="{fx + 4}" y="{fy + 14}" width="{fw - 8}" height="2" fill="{TEAL}" opacity=".85"/>
  <rect x="{fx + 4}" y="{fy + 4}" width="{fw - 8}" height="12" fill="{TEAL}" opacity=".08"/></g>
{verdict("v1", 866, 214, "✓", "identified · 94.55%", TEAL)}
{verdict("v2", 896, 214, "?", "not certain", GOLD)}
{verdict("v3", 880, 214, "✕", "not recognised", CORAL)}
<text x="{fx + fw}" y="{fy - 14}" text-anchor="end" font-size="12" letter-spacing="2" fill="{MUTED}">RESCUELENS · LIVE INFERENCE</text>"""
    return svg_doc(1200, 320, body, "Priyanshu Kumar Senapati, AI/ML and Software Engineer. I build AI that knows when it's wrong.", style)


# ---------------------------------------------------------------- stats strip
STATS = [
    ("94.55%", "top-1 accuracy, 196 car classes", "RescueLens"),
    ("0% unsafe", "answers vs 43–70% for LLM baselines", "Query2Diagnose"),
    ("Top 30", "Asian Hackathon for Green Future", "SETHU · finale in Vietnam"),
    ("10", "hackathons & build sprints", "2 finales"),
]


def stats() -> str:
    tile_w = 1200 / 4
    parts = ['<rect width="1200" height="150" rx="18" fill="url(#bg)"/>',
             f'<rect x=".5" y=".5" width="1199" height="149" rx="17.5" fill="none" stroke="{EDGE}"/>']
    for i, (num, label, src) in enumerate(STATS):
        x = i * tile_w + 40
        if i:
            parts.append(f'<line x1="{i * tile_w}" y1="30" x2="{i * tile_w}" y2="120" stroke="{EDGE}"/>')
        parts.append(f'<text x="{x}" y="66" font-size="38" font-weight="700" fill="url(#accent)">{escape(num)}</text>')
        parts.append(f'<text x="{x}" y="96" font-size="17" fill="{BODY}">{escape(label)}</text>')
        parts.append(f'<text x="{x}" y="122" font-size="15.5" font-weight="600" fill="{MUTED}">{escape(src)}</text>')
    return svg_doc(1200, 150, "\n".join(parts), "Highlights: " + "; ".join(f"{n} {l} ({s})" for n, l, s in STATS))


# ---------------------------------------------------------------- project cards
CARDS = [
    dict(slug="rescuelens", kicker="COMPUTER VISION · CV HACKATHON 2026", title="RescueLens", badge=("LIVE", TEAL),
         desc="Names a crashed car’s make, model and year from one photo, then shows rescuers where EV high voltage runs. Says “not certain” instead of guessing.",
         metric="94.55%", mlabel=["top-1 accuracy", "across 196 car classes"],
         stack=["PyTorch", "YOLO11", "ONNX INT8", "FastAPI", "React"]),
    dict(slug="query2diagnose", kicker="LLM AGENTS · RESEARCH, CO-AUTHOR", title="Query2Diagnose", badge=("MANUSCRIPT", BLUE),
         desc="Diagnoses appliance faults from code-mixed Kannada/Hindi–English text. Asks follow-up questions and answers only when grounded.",
         metric="0%", mlabel=["unsafe answers", "LLM baselines: 43–70%"],
         stack=["LLM agents", "RAG", "Python", "Evaluation"]),
    dict(slug="neralu", kicker="PUBLIC HEALTH · HACK4SDG 2026", title="Neralu", badge=("FINALE", GOLD),
         desc="Phones older people who live alone when the heat crosses their own threshold. A worrying keypad answer sends a volunteer to the door.",
         metric="287", mlabel=["tests, and no model", "in the safety loop"],
         stack=["FastAPI", "Twilio Voice", "Sarvam AI", "React 19"]),
    dict(slug="ultron", kicker="SYSTEMS · LOCAL-FIRST AI", title="ULTRON", badge=None,
         desc="19 Rust and Python processes on one authenticated WebSocket bus, each its own failure domain, with a hash-chained audit log.",
         metric="337", mlabel=["tests across", "Rust and Python"],
         stack=["Rust", "Python", "WebSockets", "Ollama", "Whisper"]),
    dict(slug="dor", kicker="HEALTHTECH · ELDER CARE", title="Dor", badge=("LIVE", TEAL),
         desc="Every missed dose, refill and doctor visit gets one responsible person, with escalation and duplicate-medicine checks. The elder stays in control.",
         metric="100", mlabel=["Lighthouse", "accessibility score"],
         stack=["Next.js", "Postgres", "Gemini", "Vercel"]),
    dict(slug="voyance", kicker="OPERATIONS RESEARCH · TBO VOYAGEHACK 4.0", title="Voyance", badge=None,
         desc="Decides which hotel-weeks to pre-buy on a budget. Recovers demand hidden by sell-outs; a CVaR-aware LP trades profit against unsold risk.",
         metric="+14–24%", mlabel=["expected profit vs", "last year’s bookings (sim.)"],
         stack=["Python", "SciPy HiGHS", "CVaR", "FastAPI"]),
]


def card(c: dict) -> str:
    W, H, pad = 600, 330, 32
    parts = [f'<rect width="{W}" height="{H}" rx="18" fill="{CARD}"/>',
             f'<rect width="{W}" height="{H}" rx="18" fill="url(#dots)"/>',
             f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="{EDGE}"/>',
             f'<rect x="{pad}" y="0" width="64" height="4" rx="2" fill="url(#accent)"/>',
             f'<text x="{pad}" y="44" font-size="13.5" font-weight="600" letter-spacing="1.5" fill="{MUTED}">{escape(c["kicker"])}</text>',
             f'<text x="{pad}" y="86" font-size="31" font-weight="700" fill="{TEXT}">{escape(c["title"])}</text>']
    if c["badge"]:
        label, color = c["badge"]
        bw = text_width(label, 12.5, bold=True) + 22
        chip_svg, _ = chip(W - pad - bw, 66, label, color, 12.5, filled=True)
        parts.append(chip_svg)
    for i, line in enumerate(wrap(c["desc"], 16.5, W - 2 * pad)[:3]):
        parts.append(f'<text x="{pad}" y="{122 + i * 24}" font-size="16.5" fill="{BODY}">{escape(line)}</text>')
    parts.append(f'<line x1="{pad}" y1="206" x2="{W - pad}" y2="206" stroke="{EDGE}"/>')
    parts.append(f'<text x="{pad}" y="254" font-size="36" font-weight="700" fill="url(#accent)">{escape(c["metric"])}</text>')
    mx = pad + text_width(c["metric"], 36, bold=True) + 18
    for i, line in enumerate(c["mlabel"]):
        parts.append(f'<text x="{mx:.1f}" y="{236 + i * 19}" font-size="15.5" fill="{MUTED}">{escape(line)}</text>')
    x = pad
    for s in c["stack"]:
        svg, w = chip(x, 276, s, BLUE, 14.5)
        parts.append(svg)
        x += w + 8
    return svg_doc(W, H, "\n".join(parts), f'{c["title"]}: {c["desc"]} {c["metric"]} {" ".join(c["mlabel"])}.')


# ---------------------------------------------------------------- toolbox
TOOLBOX = [
    ("Languages", ["Python", "TypeScript", "Rust", "Kotlin", "Java", "SQL"]),
    ("ML & AI", ["PyTorch", "scikit-learn", "XGBoost", "LightGBM", "YOLO", "OpenCV", "ONNX", "LLM agents", "RAG", "Whisper"]),
    ("Backend & web", ["FastAPI", "Flask", "Next.js", "React", "Tailwind CSS", "PostgreSQL", "SQLite", "Firebase", "Twilio"]),
    ("Ops & cloud", ["Docker", "GitHub Actions", "pytest", "Modal", "Vercel", "Hugging Face"]),
    ("Finance", ["DCF valuation", "Backtesting", "CVaR", "Linear programming"]),
]


def toolbox() -> str:
    row_h, top = 52, 36
    H = top * 2 + row_h * len(TOOLBOX) - 14
    parts = [f'<rect width="1200" height="{H}" rx="18" fill="url(#bg)"/>',
             f'<rect x=".5" y=".5" width="1199" height="{H - 1}" rx="17.5" fill="none" stroke="{EDGE}"/>']
    for r, (label, items) in enumerate(TOOLBOX):
        y = top + r * row_h
        parts.append(f'<text x="40" y="{y + 19}" font-size="17" font-weight="700" fill="{TEXT}">{escape(label)}</text>')
        x = 200
        for it in items:
            svg, w = chip(x, y, it, TEAL if label == "ML & AI" else BLUE, 15.5, filled=True)
            parts.append(svg)
            x += w + 8
        assert x < 1180, f"toolbox row '{label}' overflows ({x:.0f}px)"
    return svg_doc(1200, H, "\n".join(parts), "Toolbox: " + "; ".join(f"{l}: {', '.join(i)}" for l, i in TOOLBOX))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = {"banner.svg": banner(), "stats.svg": stats(), "toolbox.svg": toolbox()}
    files.update({f"card-{c['slug']}.svg": card(c) for c in CARDS})
    for c in CARDS:
        assert len(wrap(c["desc"], 16.5, 600 - 64)) <= 3, f"{c['slug']}: description wraps past 3 lines"
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote assets/{name} ({len(svg):,} bytes)")
