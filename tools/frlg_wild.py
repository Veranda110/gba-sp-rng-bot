"""Search shiny wild encounters (FRLG Sweet Scent, land) over every seed of one Ten Lines table.

Call order from pokefirered wild_encounter.c / pokemon.c, starting at advance n:
out[n] % 100 = slot, out[n+1] = level roll, out[n+2] % 25 = nature,
then PID pairs (low, high) from out[n+3] until PID % 25 == nature, then two IV words.
This is method H-1; keep targets with few PID tries so no VBlank call lands inside (see doc 07).
Usage: py -I frlg_wild.py <TID> <SID> <table bin> <table key> <slot rolls, e.g. 40-49,80-84,94-97,99>
                          <adv_min> <adv_max> [natures, e.g. Timid,Modest]
"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tl_parse import load

N = ['Hardy', 'Lonely', 'Brave', 'Adamant', 'Naughty', 'Bold', 'Docile', 'Relaxed', 'Impish', 'Lax',
     'Timid', 'Hasty', 'Serious', 'Jolly', 'Naive', 'Modest', 'Mild', 'Quiet', 'Bashful', 'Rash',
     'Calm', 'Gentle', 'Sassy', 'Careful', 'Quirky']
A, C, M = 0x41C64E6D, 0x6073, 0xFFFFFFFF

TSV = (int(sys.argv[1]) ^ int(sys.argv[2])) >> 3
path, key, slots_arg = sys.argv[3], sys.argv[4], sys.argv[5]
adv_min, adv_max = int(sys.argv[6]), int(sys.argv[7])
want = set(sys.argv[8].split(",")) if len(sys.argv) > 8 else None
ok_roll = np.zeros(100, bool)
for part in slots_arg.split(","):
    lo, _, hi = part.partition("-")
    ok_roll[int(lo):int(hi or lo) + 1] = True

span = adv_max + 400
a = np.empty(span, np.uint64)
c = np.empty(span, np.uint64)
ai, ci = 1, 0
for i in range(span):          # state after i+1 steps = a[i] * seed + c[i]
    ai, ci = (ai * A) & M, (ci * A + C) & M
    a[i], c[i] = ai, ci

res = []
for frame, seed in load(path)[key][2]:
    out = (((a * np.uint64(seed) + c) & np.uint64(M)) >> np.uint64(16)).astype(np.int64)
    lo, hi = out[:-1], out[1:]
    pidnat = ((hi << 16) | lo) % 25
    for j in np.nonzero(((lo ^ hi) >> 3) == TSV)[0]:
        nat = int(pidnat[j])
        if want and N[nat] not in want:
            continue
        k = 0
        while True:
            n = j - 3 - 2 * k
            if n < adv_min:
                break
            if n <= adv_max and out[n + 2] % 25 == nat and ok_roll[out[n] % 100]:
                w1, w2 = int(out[j + 2]), int(out[j + 3])
                iv = [w1 & 31, (w1 >> 5) & 31, (w1 >> 10) & 31, (w2 >> 5) & 31, (w2 >> 10) & 31, w2 & 31]
                res.append((int(frame), int(seed), int(n), int(out[n] % 100), N[nat], iv))
            k += 1
            if pidnat[j - 2 * k] == nat:   # an earlier PID in this chain matches: loop would stop there
                break
print(len(res), "shiny encounters, best IV total first")
for frame, seed, n, roll, nat, iv in sorted(res, key=lambda r: -sum(r[5]))[:30]:
    print("frame %4d  seed %04X  advance %6d  slot roll %2d  %-8s %s"
          % (frame, seed, n, roll, nat, "/".join(map(str, iv))))
