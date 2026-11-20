"""Parse SURVEY lines from a dcs.log into survey_caucasus.npz (heights, surface types, grid origin/step)."""
import pathlib
import re
import sys

import numpy as np

LINE = re.compile(r"SURVEY (\w+) ?(.*)$")


def parse(log_path):
    grid, anchors, H, T, done = None, [], None, None, False
    for raw in pathlib.Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE.search(raw)
        if not m:
            continue
        kind, rest = m.group(1), m.group(2).split()
        if kind == "GRID":
            x0, z0, step, nx, nz = map(int, rest)
            grid = dict(x0=x0, z0=z0, step=step, nx=nx, nz=nz)
            H = np.full((nx, nz), np.nan, dtype=np.float32)
            T = np.zeros((nx, nz), dtype=np.int8)
        elif kind == "LL":
            anchors.append(tuple(map(float, rest)))
        elif kind == "H":
            r, c0 = int(rest[0]), int(rest[1])
            v = [int(s) for s in rest[2].split(",")]
            H[r, c0:c0 + len(v)] = v
        elif kind == "T":
            r, c0 = int(rest[0]), int(rest[1])
            T[r, c0:c0 + len(rest[2])] = [int(ch) for ch in rest[2]]
        elif kind == "DONE":
            done = True
    if grid is None:
        raise SystemExit("no SURVEY GRID line in the log")
    missing = int(np.isnan(H).sum())
    return grid, np.array(anchors), H, T, done, missing


def main(log_path, out="survey_caucasus.npz"):
    grid, anchors, H, T, done, missing = parse(log_path)
    np.savez_compressed(out, H=H, T=T, anchors=anchors, **grid)
    print(f"grid {grid['nx']}x{grid['nz']} @ {grid['step']} m, done={done}, missing={missing}, "
          f"h {np.nanmin(H):.0f}..{np.nanmax(H):.0f} m -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
