"""Generates docs/img/soldering-methods.svg: three ways to connect a wire to an ESP32 pin on a protoboard."""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "img" / "soldering-methods.svg"

BOARD, COPPER, SOLDER, PIN, GOLD = "#2f7d4a", "#c8742a", "#b8bcc2", "#9ea3a8", "#d4af37"
WIRE_BLUE, WIRE_RED, BARE, DARK = "#1f6feb", "#cf222e", "#d4883a", "#222"
W, H = 920, 400
s = []
add = s.append

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    'font-family="Segoe UI, Arial, sans-serif">')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
add('<text x="20" y="30" font-size="19" font-weight="600" fill="#111">Three ways to connect a wire to an ESP32 pin</text>')
add('<text x="20" y="52" font-size="12.5" fill="#444">Side view through the protoboard, copper pads on the underside.</text>')


def text(x, y, t, size=12.5, color="#222", weight=400, anchor="start"):
    add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{t}</text>')


def board(px, holes):
    add(f'<rect x="{px + 20}" y="210" width="240" height="22" fill="{BOARD}"/>')
    for hx in holes:
        add(f'<rect x="{hx - 18}" y="232" width="36" height="5" fill="{COPPER}"/>')
        add(f'<rect x="{hx - 5}" y="210" width="10" height="27" fill="#ffffff"/>')


def esp_pin(hx, bottom=246):
    add(f'<rect x="{hx - 45}" y="150" width="90" height="34" rx="3" fill="#1d2d44"/>')
    text(hx, 172, "ESP32", 11, "#9fb3cc", anchor="middle")
    add(f'<rect x="{hx - 9}" y="196" width="18" height="14" fill="{DARK}"/>')
    add(f'<rect x="{hx - 2.5}" y="184" width="5" height="{bottom - 184}" fill="{PIN}"/>')


def joint(x1, x2, y=237, depth=11):
    add(f'<path d="M{x1},{y} L{x2},{y} Q{x2 - 4},{y + depth} {(x1 + x2) / 2},{y + depth + 2} '
        f'Q{x1 + 4},{y + depth} {x1},{y} Z" fill="{SOLDER}"/>')


def label(px, lines, verdict, color):
    for i, t in enumerate(lines):
        text(px + 10, 86 + i * 17, t, 13.5 if i == 0 else 12.5, "#111" if i == 0 else "#333", 600 if i == 0 else 400)
    add(f'<rect x="{px + 10}" y="318" width="270" height="44" rx="6" fill="{color}" opacity="0.13"/>')
    for i, t in enumerate(verdict):
        text(px + 20, 336 + i * 17, t, 12.5, "#222")


# 1. wire through the next hole, bent onto the pin's pad
px = 10
h1, h2 = px + 105, px + 165
board(px, (h1, h2))
esp_pin(h1)
add(f'<path d="M{px + 265},140 C{px + 230},150 {h2},160 {h2},204" fill="none" stroke="{WIRE_BLUE}" stroke-width="6" stroke-linecap="round"/>')
add(f'<path d="M{h2},204 L{h2},243 L{h1 + 10},243" fill="none" stroke="{BARE}" stroke-width="3"/>')
joint(h1 - 18, h1 + 26)
label(px, ["1. Through the next hole", "bare end bent onto the pin's pad,", "then one joint over both"],
      ["Easy: the wire lies flat on the pad", "and cannot roll off"], "#2da44e")

# 2. header pin next to it, bridged, Dupont jumper on top
px = 310
h1, h2 = px + 105, px + 165
board(px, (h1, h2))
esp_pin(h1)
add(f'<rect x="{h2 - 2.5}" y="150" width="5" height="96" fill="{GOLD}"/>')
add(f'<rect x="{h2 - 9}" y="196" width="18" height="14" fill="{DARK}"/>')
add(f'<rect x="{h2 - 9}" y="140" width="18" height="38" rx="2" fill="{DARK}"/>')
add(f'<path d="M{h2},140 C{h2},132 {h2 + 30},134 {px + 268},134" fill="none" stroke="{WIRE_RED}" stroke-width="6" stroke-linecap="round"/>')
text(h2 + 16, 158, "Dupont", 11, "#555")
text(h2 + 16, 171, "jumper", 11, "#555")
text(h2 + 16, 205, "header", 11, "#555")
joint(h1 - 18, h2 + 18)
label(px, ["2. Header pin next to it", "one solder blob joins both pads,", "a Dupont jumper plugs on top"],
      ["Easy and detachable: unplug the", "jumper, no desoldering"], "#2da44e")

# 3. straight onto the pin
px = 610
h1 = px + 125
board(px, (h1,))
esp_pin(h1, bottom=262)
add(f'<path d="M{px + 270},282 L{h1 + 16},282" fill="none" stroke="{WIRE_BLUE}" stroke-width="6" stroke-linecap="round"/>')
add(f'<path d="M{h1 + 16},282 L{h1 + 6},270" fill="none" stroke="{BARE}" stroke-width="3"/>')
for y in (252, 258, 264):
    add(f'<ellipse cx="{h1}" cy="{y}" rx="7" ry="2.6" fill="none" stroke="{BARE}" stroke-width="2.5"/>')
joint(h1 - 18, h1 + 18)
add(f'<rect x="{h1 - 6}" y="248" width="12" height="20" rx="4" fill="{SOLDER}" opacity="0.75"/>')
label(px, ["3. Straight onto the pin", "bare end wrapped around the pin", "that sticks out underneath"],
      ["Works, but fiddly: tin both first,", "wrap once, use flux and a clamp"], "#d4a72c")

add("</svg>")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(s), encoding="utf-8")
print("wrote", OUT)
