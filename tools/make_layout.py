"""Generates docs/img/protoboard-layout.svg: hole-level protoboard layout, top view."""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "img" / "protoboard-layout.svg"

def x(c): return 120 + 28 * c
def y(r): return 40 + 28 * r

BLUE, ORANGE, RED, CHAIN, LEG = "#1f6feb", "#d9822b", "#cf222e", "#4a4a4a", "#8a8a8a"
s = []
add = s.append

add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 760" width="820" height="760" '
    'font-family="Segoe UI, Arial, sans-serif">')
add('<rect width="820" height="760" fill="#ffffff"/>')

# titles
add('<text x="40" y="38" font-size="20" font-weight="600" fill="#111">Protoboard layout, top view</text>')
add('<text x="40" y="60" font-size="13" fill="#444">ESP32 antenna up, its pin-32 row on the left. '
    'Every dot is a hole, 2.54 mm apart.</text>')

# zones
add(f'<rect x="{x(0.5)}" y="104" width="{x(7.5)-x(0.5)}" height="460" fill="#fdf3e7"/>')
add(f'<rect x="{x(11.5)}" y="104" width="{x(17.5)-x(11.5)}" height="460" fill="#eaf2fd"/>')
for label, cx in (("GAME BOY SIDE", (x(0.5)+x(7.5))/2), ("ISOLATION", (x(7.5)+x(11.5))/2),
                  ("ESP32 SIDE", (x(11.5)+x(17.5))/2)):
    add(f'<text x="{cx}" y="96" font-size="12" font-weight="600" fill="#555" text-anchor="middle" '
        f'letter-spacing="1">{label}</text>')

# hole grid
for c in range(1, 18):
    for r in range(3, 19):
        add(f'<circle cx="{x(c)}" cy="{y(r)}" r="3" fill="#c4c4c4"/>')

def poly(points, color, width=3.5, dash=None):
    d = " ".join(f"{px},{py}" for px, py in points)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linejoin="round" stroke-linecap="round"{da}/>')

def dot(px, py, color, r=4.5):
    add(f'<circle cx="{px}" cy="{py}" r="{r}" fill="{color}"/>')

add(f'<rect x="{x(18)-16}" y="108" width="190" height="452" rx="8" fill="#1d2d44"/>')
# copper side: ground chains (dashed)
poly([(x(2), y(5)), (x(6), y(5)), (x(6), y(15))], CHAIN, 4, "9 6")           # SP GND chain
for r in (7, 9, 12, 15):
    poly([(x(6), y(r)), (x(8), y(r))], CHAIN, 4, "9 6")
poly([(x(18), y(14)), (x(13), y(14))], CHAIN, 4, "9 6")                       # ESP32 GND chain
poly([(x(13), y(7)), (x(13), y(15))], CHAIN, 4, "9 6")
for r in (7, 9, 12, 15):
    poly([(x(11), y(r)), (x(13), y(r))], CHAIN, 4, "9 6")

# copper side: resistor legs bent onto chip pin 1
for r in (10, 13, 16):
    poly([(x(11), y(r)), (x(12), y(r))], LEG, 5)

# header (socket for the tail plug)
add(f'<rect x="{x(2)-14}" y="{y(5)-14}" width="28" height="{y(10)-y(5)+28}" rx="3" fill="#222"/>')
for i, r in enumerate(range(5, 11), start=1):
    add(f'<rect x="{x(2)-4}" y="{y(r)-4}" width="8" height="8" fill="#d4af37"/>')
    name = ["GND", "3.3V", "A", "B", "START", "empty"][i - 1]
    col = "#999" if name == "empty" else "#111"
    add(f'<text x="{x(2)-22}" y="{y(r)+4}" font-size="12" text-anchor="end" fill="{col}">'
        f'<tspan font-weight="600">{i}</tspan> {name}</text>')
add(f'<text x="{x(2)}" y="{y(4)+2}" font-size="11" text-anchor="middle" fill="#555">plug socket</text>')

# chips
chips = [  # (label, top row, rotated)
    ("#1 POWER DETECT", 6, False),
    ("#2 A", 9, True),
    ("#3 B", 12, True),
    ("#4 START", 15, True),
]
for label, r1, rot in chips:
    r2 = r1 + 1
    add(f'<rect x="{x(8)-14}" y="{y(r1)-14}" width="{x(11)-x(8)+28}" height="{y(r2)-y(r1)+28}" '
        f'rx="3" fill="#2b2b2b"/>')
    for c in (8, 11):
        for r in (r1, r2):
            add(f'<rect x="{x(c)-4}" y="{y(r)-4}" width="8" height="8" fill="#c8c8c8"/>')
    pins = {(8, r1): 1, (8, r2): 2, (11, r1): 4, (11, r2): 3} if not rot else \
           {(8, r1): 3, (8, r2): 4, (11, r1): 2, (11, r2): 1}
    for (c, r), n in pins.items():
        tx = x(c) + 14 if c == 8 else x(c) - 14
        add(f'<text x="{tx}" y="{y(r)+4}" font-size="11" fill="#fff" text-anchor="middle">{n}</text>')
    if rot:
        dot(x(11) - 30, y(r2), "#fff", 4)
    else:
        dot(x(8) + 30, y(r1), "#fff", 4)
    add(f'<text x="{(x(8)+x(11))/2}" y="{y(r1-1)+4}" font-size="11" font-weight="600" fill="#222" '
        f'text-anchor="middle">{label}</text>')

# resistors 220 ohm: red red brown gold
for r in (10, 13, 16):
    poly([(x(12), y(r)), (x(16), y(r))], "#9a9a9a", 2.5)
    add(f'<rect x="{x(12)+20}" y="{y(r)-8}" width="{x(16)-x(12)-40}" height="16" rx="6" '
        f'fill="#e8d3a8" stroke="#a0845c"/>')
    for bx, bc in ((x(12)+30, "#c62828"), (x(12)+39, "#c62828"), (x(12)+48, "#6d4c41"), (x(16)-30, "#c9a227")):
        add(f'<rect x="{bx}" y="{y(r)-8}" width="5" height="16" fill="{bc}"/>')
    dot(x(12), y(r), "#9a9a9a", 3.5)
    dot(x(16), y(r), "#9a9a9a", 3.5)
    add(f'<text x="{(x(12)+x(16))/2}" y="{y(r)-13}" font-size="10" fill="#555" text-anchor="middle">220 &#937;</text>')

# Game Boy side wires (top of board)
poly([(x(2), y(6)), (x(8), y(6))], RED)                                         # 3.3 V to #1 pin 1
poly([(x(2), y(7)), (260, y(7)), (260, y(10)), (x(8), y(10))], ORANGE)          # A to #2 pin 4
poly([(x(2), y(8)), (245, y(8)), (245, y(13)), (x(8), y(13))], ORANGE)          # B to #3 pin 4
poly([(x(2), y(9)), (230, y(9)), (230, y(16)), (x(8), y(16))], ORANGE)          # Start to #4 pin 4
for px, py, col in ((x(8), y(6), RED), (x(8), y(10), ORANGE), (x(8), y(13), ORANGE), (x(8), y(16), ORANGE)):
    dot(px, py, col)

# ESP32 side wires (top of board)
poly([(x(18), y(7)), (600, y(7)), (600, y(6)), (x(11), y(6))], BLUE)            # GPIO 32 to #1 pin 4
poly([(x(18), y(8)), (576, y(8)), (576, y(10)), (x(16), y(10))], BLUE)          # GPIO 33 to R_A
poly([(x(18), y(10)), (588, y(10)), (588, y(13)), (x(16), y(13))], BLUE)        # GPIO 26 to R_B
poly([(x(18), y(11)), (600, y(11)), (600, y(16)), (x(16), y(16))], BLUE)        # GPIO 27 to R_Start
for px, py in ((x(11), y(6)), (x(16), y(10)), (x(16), y(13)), (x(16), y(16))):
    dot(px, py, BLUE)

# ESP32 board
names = ["VP", "VN", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "D2", "D3", "CMD"]
used = {"32", "33", "26", "27", "GND"}
for r, n in zip(range(3, 19), names):
    on = n in used
    add(f'<circle cx="{x(18)}" cy="{y(r)}" r="5.5" fill="{"#d4af37" if on else "#7c7c5c"}"/>')
    add(f'<text x="{x(18)+14}" y="{y(r)+4}" font-size="12" fill="{"#fff" if on else "#7f93ad"}" '
        f'font-weight="{600 if on else 400}">{n}</text>')
add(f'<text x="{x(18)+110}" y="{y(10)}" font-size="13" fill="#9fb3cc" text-anchor="middle">ESP32</text>')
add(f'<text x="{x(18)+110}" y="{y(10)+18}" font-size="11" fill="#7f93ad" text-anchor="middle">DevKit</text>')
add(f'<text x="{x(18)+110}" y="126" font-size="11" fill="#9fb3cc" text-anchor="middle">antenna up</text>')
add(f'<text x="{x(18)+110}" y="550" font-size="11" fill="#9fb3cc" text-anchor="middle">USB down</text>')

# legend
ly = 600
items = [
    (BLUE, None, "insulated wire on top, ESP32 side"),
    (ORANGE, None, "insulated wire on top, Game Boy side"),
    (RED, None, "3.3 V wire, already through the 330 &#937; in the tail"),
    (CHAIN, "9 6", "bare wire on the copper side: ground chain"),
    (LEG, None, "resistor leg bent onto the chip pad"),
]
for i, (col, dash, text) in enumerate(items):
    lx = 40 if i < 3 else 430
    yy = ly + (i if i < 3 else i - 3) * 24
    poly([(lx, yy), (lx + 34, yy)], col, 4 if dash or col == LEG else 3.5, dash)
    add(f'<text x="{lx+44}" y="{yy+4}" font-size="12" fill="#222">{text}</text>')
add(f'<circle cx="{447}" cy="{ly+48}" r="4" fill="#2b2b2b"/><circle cx="{447}" cy="{ly+48}" r="2.5" fill="#fff"/>')
add(f'<text x="{474}" y="{ly+52}" font-size="12" fill="#222">white dot = pin 1 mark on the chip</text>')
add(f'<text x="40" y="{ly+90}" font-size="12" fill="#444">The two ground chains never touch. '
    f'Chip #1 is turned around compared to #2, #3 and #4.</text>')
add(f'<text x="40" y="{ly+110}" font-size="12" fill="#444">30-pin ESP32 boards have pin 13 between 12 and GND: '
    f'follow the labels printed on your board.</text>')
add(f'<text x="40" y="{ly+130}" font-size="12" fill="#444">Crossings without a dot are not connected: '
    f'top wires pass over the copper-side chains.</text>')

add("</svg>")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(s), encoding="utf-8")
print("wrote", OUT)

