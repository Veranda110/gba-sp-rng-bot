"""Parse a Ten Lines FRLG seed table (non-NX format) into {key: [(frame, seed), ...]}.

Format (ten-lines src/wasm/src/initial_seed.hpp): repeated blocks of
key (C string), starting_frame u16, frame_size u8, count u32, then count x (seed u16, invalid u8).
Entry i belongs to frame starting_frame + i // frame_size.
"""
import struct
import sys


def load(path):
    data = open(path, "rb").read()
    p = 0
    tables = {}
    while p < len(data):
        end = data.index(b"\0", p)
        key = data[p:end].decode()
        p = end + 1
        start, size = struct.unpack_from("<HB", data, p)
        p += 3
        (count,) = struct.unpack_from("<I", data, p)
        p += 4
        rows = []
        for i in range(count):
            seed, invalid = struct.unpack_from("<HB", data, p)
            p += 3
            if not invalid:
                rows.append((start + i // size, seed))
        tables[key] = (start, size, rows)
    return tables


if __name__ == "__main__":
    t = load(sys.argv[1])
    for key, (start, size, rows) in t.items():
        print("%-14s start frame %5d  per frame %d  entries %6d  frames %d..%d"
              % (key, start, size, len(rows), rows[0][0], rows[-1][0]))
