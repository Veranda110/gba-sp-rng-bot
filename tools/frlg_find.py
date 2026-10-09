"""Find every (seed, advance) that gives a method 1 Pokemon with this nature and these stats.

Usage: py -I frlg_find.py <species> <level> <nature> <hp> <atk> <def> <spa> <spd> <spe> <adv_min> <adv_max>
Convention (verified on Emerald): at advance n, PID low = output n+1, PID high = n+2,
IV word 1 = n+3, IV word 2 = n+4, outputs being the upper 16 bits of each LCRNG state.
"""
import sys
import numpy as np

BASE = {
    "abra": (25, 20, 15, 105, 55, 90),
    "snorlax": (160, 110, 65, 65, 110, 30),
    "treecko": (40, 45, 35, 65, 55, 70),
}
NATURES = ['hardy', 'lonely', 'brave', 'adamant', 'naughty', 'bold', 'docile', 'relaxed', 'impish', 'lax',
           'timid', 'hasty', 'serious', 'jolly', 'naive', 'modest', 'mild', 'quiet', 'bashful', 'rash',
           'calm', 'gentle', 'sassy', 'careful', 'quirky']
ORDER = ['atk', 'def', 'spe', 'spa', 'spd']   # nature increase/decrease order

species, level, nature = sys.argv[1].lower(), int(sys.argv[2]), sys.argv[3].lower()
target = tuple(int(x) for x in sys.argv[4:10])
adv_min, adv_max = int(sys.argv[10]), int(sys.argv[11])
b = BASE[species]
n_idx = NATURES.index(nature)
up, dn = ORDER[n_idx // 5], ORDER[n_idx % 5]


def stat_ok_ivs(i, value):
    """IVs 0..31 that give this stat value."""
    ok = []
    for iv in range(32):
        if i == 0:
            v = (2 * b[0] + iv) * level // 100 + level + 10
        else:
            v = (2 * b[i] + iv) * level // 100 + 5
            name = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'][i]
            if up != dn:
                if name == up: v = v * 110 // 100
                if name == dn: v = v * 90 // 100
        if v == value: ok.append(iv)
    return ok


allowed = [np.zeros(32, bool) for _ in range(6)]
for i in range(6):
    for iv in stat_ok_ivs(i, target[i]):
        allowed[i][iv] = True
if not all(a.any() for a in allowed):
    print("no IVs fit these stats for this species, level and nature")
    sys.exit(1)

A, C = 0x41C64E6D, 0x6073
M = 0xFFFFFFFF


def jump(n):
    a, c = 1, 0
    ma, mc = A, C
    while n:
        if n & 1:
            a, c = (a * ma) & M, (c * ma + mc) & M
        ma, mc = (ma * ma) & M, (mc * ma + mc) & M
        n >>= 1
    return a, c


seeds = np.arange(65536, dtype=np.uint64)
ja, jc = jump(adv_min)
s = (seeds * ja + jc) & M          # states after adv_min steps
a64, c64 = np.uint64(A), np.uint64(C)
nxt = lambda x: (x * a64 + c64) & np.uint64(M)
o1 = nxt(s); o2 = nxt(o1); o3 = nxt(o2); o4 = nxt(o3)
hits = []
for adv in range(adv_min, adv_max + 1):
    lo, hi = o1 >> np.uint64(16), o2 >> np.uint64(16)
    iv1, iv2 = o3 >> np.uint64(16), o4 >> np.uint64(16)
    pid = (hi << np.uint64(16)) | lo
    mask = (pid % np.uint64(25)) == np.uint64(n_idx)
    ivs = [iv1 & 31, (iv1 >> 5) & 31, (iv1 >> 10) & 31, (iv2 >> 5) & 31, (iv2 >> 10) & 31, iv2 & 31]
    for i in range(6):
        mask &= allowed[i][ivs[i].astype(np.int64)]
    for seed in np.nonzero(mask)[0]:
        hits.append((int(seed), adv, [int(v[seed]) for v in ivs]))
    o1, o2, o3, o4 = o2, o3, o4, nxt(o4)
if len(sys.argv) > 12:
    with open(sys.argv[12], "w") as f:
        for seed, adv, ivs in hits:
            f.write("%d,%d\n" % (seed, adv))
print(len(hits), "matches")
for seed, adv, ivs in hits[:40]:
    print("seed %04X  advance %d  IVs %s" % (seed, adv, "/".join(map(str, ivs))))
