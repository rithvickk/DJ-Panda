"""
The animated dancer.

The dancer is a simple, abstract figure (circle head, rounded body and limbs).
ALL the movement and colors live in assets/dancer.css. This file only:
  1. picks the world's color palette and move set,
  2. works out the beat length from the song's tempo,
  3. glues the CSS and a tiny SVG figure together for Streamlit to show.

Try it on its own:  python dancer.py   (writes dancer_preview.html you can open)
"""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# ---------------------------------------------------------------------------
# EDIT ME: colors and move set for each world.
# "moves" must match a .moves-<name> section in assets/dancer.css.
# ---------------------------------------------------------------------------
WORLD_STYLES = {
    "India": {
        "moves": "bollywood",
        "colors": {"bg1": "#2a0a3a", "bg2": "#a3124a", "body": "#ffb627", "accent": "#ff3d7f", "glow": "#ffd166"},
    },
    "South Korea": {
        "moves": "kpop",
        "colors": {"bg1": "#0b1030", "bg2": "#3a1f7a", "body": "#f2f4ff", "accent": "#ff4fd8", "glow": "#52e5ff"},
    },
    "Latin America": {
        "moves": "salsa",
        "colors": {"bg1": "#3b0d12", "bg2": "#c7391f", "body": "#ffd23f", "accent": "#00c2a8", "glow": "#ff8c42"},
    },
    "Europe": {
        "moves": "eurodance",
        "colors": {"bg1": "#06121f", "bg2": "#0d4a6b", "body": "#e0f7ff", "accent": "#3df2a0", "glow": "#7a5cff"},
    },
    "West Africa": {
        "moves": "afrobeats",
        "colors": {"bg1": "#10280f", "bg2": "#a85f00", "body": "#ffcc33", "accent": "#19c37d", "glow": "#ff7a1a"},
    },
}

DANCE_SECONDS = 30  # about the length of a song preview
BEATS_PER_MOVE = 2  # one full move cycle lasts this many beats

# Spotify sometimes reports double or half the "felt" tempo. Keep the dance
# in a comfortable range by halving/doubling until it fits.
MIN_DANCE_BPM, MAX_DANCE_BPM = 70, 150


def dance_bpm(tempo):
    """Squeeze a song tempo into a comfortable dancing range."""
    bpm = float(tempo) if tempo and tempo > 0 else 120.0
    while bpm > MAX_DANCE_BPM:
        bpm /= 2
    while bpm < MIN_DANCE_BPM:
        bpm *= 2
    return bpm


# The figure. Each body part is its own <g> group so the CSS can move it.
FIGURE_SVG = """
<svg class="dancer" viewBox="0 0 240 300" role="img" aria-label="{label}">
  <ellipse class="shadow" cx="120" cy="284" rx="52" ry="8"/>
  <g class="figure">
    <g class="leg leg-l"><rect x="100" y="176" width="16" height="100" rx="8"/></g>
    <g class="leg leg-r"><rect x="124" y="176" width="16" height="100" rx="8"/></g>
    <g class="bow">
      <g class="upper">
        <g class="arm arm-l"><rect x="74" y="104" width="16" height="80" rx="8"/></g>
        <g class="arm arm-r"><rect x="150" y="104" width="16" height="80" rx="8"/></g>
        <rect class="torso" x="94" y="98" width="52" height="90" rx="24"/>
        <g class="head"><circle cx="120" cy="70" r="24"/></g>
      </g>
    </g>
  </g>
</svg>
"""


def build_dancer_html(world, tempo):
    """Return a full HTML page (CSS + SVG) for st.iframe()."""
    style = WORLD_STYLES.get(world, WORLD_STYLES["Europe"])
    bpm = dance_bpm(tempo)
    beat_seconds = 60 / bpm
    move_seconds = beat_seconds * BEATS_PER_MOVE
    repeats = max(1, round(DANCE_SECONDS / move_seconds))

    # CSS variables: the stylesheet reads these for colors and timing.
    css_vars = {f"--{name}": value for name, value in style["colors"].items()}
    css_vars["--beat"] = f"{beat_seconds:.3f}s"
    css_vars["--move"] = f"{move_seconds:.3f}s"
    css_vars["--repeats"] = str(repeats)
    css_vars["--total"] = f"{move_seconds * repeats:.2f}s"
    inline_vars = "; ".join(f"{k}: {v}" for k, v in css_vars.items())

    css = (ASSETS_DIR / "dancer.css").read_text(encoding="utf-8")
    label = f"Abstract dancer doing {style['moves']}-inspired moves at {bpm:.0f} BPM"
    bars = "".join('<span class="bar"></span>' for _ in range(9))

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
  <div class="stage moves-{style['moves']}" style="{inline_vars}">
    <div class="spot spot-l"></div><div class="spot spot-r"></div>
    <div class="floor-ring"></div>
    {FIGURE_SVG.format(label=label)}
    <div class="eq">{bars}</div>
    <div class="bpm-tag">{bpm:.0f} BPM</div>
    <div class="progress"><div class="progress-fill"></div></div>
    <div class="finale">Take a bow!</div>
  </div>
</body></html>"""


if __name__ == "__main__":
    # Build a preview page per world so you can check the moves in a browser.
    preview = Path(__file__).resolve().parent / "dancer_preview.html"
    frames = "".join(
        f'<h3 style="font-family:sans-serif">{world}</h3>'
        f'<iframe srcdoc="{build_dancer_html(world, 120).replace(chr(34), "&quot;")}" '
        f'width="420" height="420" style="border:0"></iframe>'
        for world in WORLD_STYLES
    )
    preview.write_text(f"<html><body>{frames}</body></html>", encoding="utf-8")
    print(f"Wrote {preview} - open it in a browser")
    for tempo in [60, 95, 128, 174]:
        print(f"  song tempo {tempo} -> dance tempo {dance_bpm(tempo):.0f} BPM")
