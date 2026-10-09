"""FRLG Secret ID candidates from the Trainer ID.

The Trainer ID is the RNG seed set when the player name screen closes; the SID is the
next RNG call at "advance N" in the community tools' numbering, i.e. the upper 16 bits
of the state after N + 1 LCRNG steps (verified on Emerald: TID 3387, advance 1000 -> 29177).
Usage: py frlg_sid.py <TID> [center advance, default 1150] [half width, default 10]
"""
import sys

tid = int(sys.argv[1])
center = int(sys.argv[2]) if len(sys.argv) > 2 else 1150
half = int(sys.argv[3]) if len(sys.argv) > 3 else 10

M = 0xFFFFFFFF
s = tid
out = {}
for step in range(1, center + half + 2):
    s = (s * 0x41C64E6D + 0x6073) & M
    adv = step - 1
    if center - half <= adv <= center + half:
        out[adv] = s >> 16
print('TID %d (hex %04X)' % (tid, tid))
for adv in sorted(out, key=lambda a: (abs(a - center), a)):
    print('advance %d  SID %5d' % (adv, out[adv]))
