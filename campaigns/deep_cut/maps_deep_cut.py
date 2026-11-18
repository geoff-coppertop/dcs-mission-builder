"""Maps for Operation Deep Cut, drawn from the built .miz files.

python3 maps_deep_cut.py path/to/Operation_Deep_Cut*.miz   -> <stem>_theater.png and <stem>_gorge.png in the working dir

Red's ground sites are placed by the mission script on DCS terrain at start, so these maps show their planned
points and the radius each one is placed within.
"""
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import dcs.vehicles as V

from missionbuilder.mapkit import *  # noqa: F401,F403
from missionbuilder.mapkit import Line2D

from context import sites

PLACES = {"Jvari": (42.7189, 42.0458), "Enguri dam": (42.7592, 42.0319), "Khaishi (approx.)": (42.955, 42.200),
          "Zugdidi": (42.509, 41.871), "Anaklia": (42.398, 41.563), "Kutaisi": (42.176, 42.482), "Senaki": (42.267, 42.050)}


def rng(t):
    c = next((v for v in V.vehicle_map.values() if v.id == t), None)
    return getattr(c, "threat_range", 0) or 0


def draw_escape(miz):
    d = parse_miz(miz)
    g = d["groups"]
    stem = Path(miz).stem
    en = g["Enfield"]["route"]
    pts = [p["ll"] for p in en] + [g["Red South"]["route"][0]["ll"]]
    ext = ext_fit(pts, pad=0.08, min_span=1.0)
    fig, ax = plt.subplots(figsize=(7.4, 5.6), dpi=220)
    base_map(ax, ext, 0.25)
    for n_, (la, lo) in PLACES.items():
        if in_ext(ext, (la, lo), 0.02) and n_ not in ("Senaki", "Kutaisi"):
            ax.plot(lo, la, "s", ms=2.6, color=INK2, zorder=6)
            label(ax, lo, la, n_, INK2, dx=4, dy=-1, size=6.4)
    s0 = en[0]["ll"]
    ax.plot(s0[1], s0[0], "*", ms=12, color=BLUE, mec="white", mew=0.7, zorder=11)
    label(ax, s0[1], s0[0], "Senaki-Kolkhi: the Tomcat", BLUE, dx=8, dy=8, size=7, weight="bold")
    for gn in ("Senaki Guns North", "Senaki Guns South", "Senaki SA-13"):
        for u in g[gn]["units"]:
            ax.plot(u["ll"][1], u["ll"][0], "D", ms=3.5, color=ORANGE, zorder=9)
    r = g["Red South"]["route"]
    ax.plot(r[0]["ll"][1], r[0]["ll"][0], "^", ms=6, color=RED, zorder=8)
    arrow(ax, r[0]["ll"], r[1]["ll"], RED, lw=0.9, ls=(0, (3, 2)))
    label(ax, r[0]["ll"][1], r[0]["ll"][0], "Kutaisi alert: MiG-29S ×2\n(launches once you're seen)", RED, dx=-6, dy=-16, ha="right", size=6.4)
    st = [p for p in g["Chevy"]["route"] if p["name"] == "CAP STATION"][0]["ll"]
    ring(ax, st, 5000, color=VIOLET, lw=1.4, zorder=6)
    label(ax, *dest(st, 270, 5200)[::-1], "CHEVY CAP", VIOLET, dx=-4, ha="right", size=6.4)
    xs, ys = [p["ll"][1] for p in en], [p["ll"][0] for p in en]
    ax.plot(xs, ys, color=BLUE, lw=1.8, zorder=7)
    for i, p in enumerate(en[1:-1], start=1):
        ax.plot(p["ll"][1], p["ll"][0], "o", ms=8, color="white", mec=BLUE, mew=1.5, zorder=10)
        ax.text(p["ll"][1], p["ll"][0], str(i), ha="center", va="center", fontsize=5.6, color=BLUE, fontweight="bold", zorder=11)
        label(ax, p["ll"][1], p["ll"][0], p["name"], BLUE, dx=7, dy=-7, size=6.6)
    m_ = en[-1]["ll"]
    ax.plot(m_[1], m_[0], "D", ms=5.5, color=INK, zorder=9)
    label(ax, m_[1], m_[0], "MOTHER (est.)", INK, dy=-10, ha="center", va="top", size=6.4)
    scale_bar(ax, ext, 10)
    north_arrow(ax, ext)
    ax.set_title("THE WAY HOME", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=6)
    fig.tight_layout()
    fig.savefig(f"{stem}_theater.png", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print("maps", stem)


def draw(miz):
    if "Escape" in Path(miz).stem:
        return draw_escape(miz)
    d = parse_miz(miz)
    c = d["cfg"]
    g = d["groups"]
    stem = Path(miz).stem
    tgt = cfg_pt(c, "TGT")
    det_r, pop_r = cfg_num(c, "DET_R"), cfg_num(c, "POP_R")
    st = sites(c)
    canyon = [xz_to_ll(float(x), float(z)) for x, z in re.findall(r'\{ name = "[A-Z ]+", x = (-?[\d.]+), z = (-?[\d.]+), r = 1500 \}', c)]
    en = g["Enfield"]["route"]

    def site_ll(s):
        name, kind, x, z, r, types = s
        if kind == "guard":
            return dest(tgt, 0, 0)
        return xz_to_ll(x, z)

    # ------------------------------------------------------------ theater
    pts = [p["ll"] for p in en] + [p["ll"] for p in g["Red South"]["route"][:1]] + [p["ll"] for p in g["Red North"]["route"][:1]]
    ext = ext_fit(pts, pad=0.05, min_span=1.2)
    fig, ax = plt.subplots(figsize=(7.4, 6.2), dpi=220)
    base_map(ax, ext, 0.25)
    ring(ax, tgt, det_r, color=RED, lw=1.0, ls=(0, (4, 2)), zorder=3)
    ring_fill(ax, tgt, det_r, color=RED, alpha=0.05, zorder=2, lw=0)
    label(ax, *dest(tgt, 250, det_r)[::-1], f"Radar floor zone, {det_r / NM:.0f} nm", RED, dx=-4, ha="right", size=6.6)
    for n_, (la, lo) in PLACES.items():
        if in_ext(ext, (la, lo), 0.02):
            ax.plot(lo, la, "s", ms=2.6, color=INK2, zorder=6)
            label(ax, lo, la, n_, INK2, dx=4, dy=-1, size=6.4)
    for s in st:
        if s[1] == "sam":
            r = max(rng(t) for t in s[5])
            ring(ax, site_ll(s), r, color=ORANGE, lw=0.9, zorder=4)
    for gn, col, lab in (("Red South", RED, "Kutaisi alert"), ("Red North", RED, "Northern alert")):
        r = g[gn]["route"]
        a, b2 = r[0]["ll"], r[1]["ll"]
        ax.plot(a[1], a[0], "^", ms=6, color=col, zorder=8)
        arrow(ax, a, b2, col, lw=0.9, ls=(0, (3, 2)))
        label(ax, a[1], a[0], f"{lab}: {g[gn]['units'][0]['type']} ×{len(g[gn]['units'])}", col, dx=-6, dy=5, ha="right", size=6.4)
    if "Arco" in g:
        r = g["Arco"]["route"]
        a, b2 = r[1]["ll"], dest(r[1]["ll"], 230, 30000)
        ax.plot([a[1], b2[1]], [a[0], b2[0]], color=AQUA, lw=3.0, solid_capstyle="round", zorder=5)
        label(ax, *dest(a, 230, 15000)[::-1], "ARCO 251.0 · 60Y", "#127a55", dx=-6, ha="right", size=6.4)
    k = [p["name"] for p in en].index("TGT")
    xs, ys = [p["ll"][1] for p in en], [p["ll"][0] for p in en]
    ax.plot(xs[:k + 1], ys[:k + 1], color=BLUE, lw=1.8, zorder=7)
    ax.plot(xs[k:], ys[k:], color=BLUE, lw=1.6, ls=(0, (5, 2)), zorder=7)
    for i, p in enumerate(en):
        if i == 0 or p["name"] in ("MOTHER", "GATE OUT", "FEET WET", "DAM", "RESERVOIR", "NARROWS", "BEND"):
            continue
        la, lo = p["ll"]
        ax.plot(lo, la, "o", ms=8, color="white", mec=BLUE, mew=1.5, zorder=10)
        ax.text(lo, la, str(i), ha="center", va="center", fontsize=5.6, color=BLUE, fontweight="bold", zorder=11)
        label(ax, lo, la, p["name"], BLUE, dx=7, dy=-7, size=6.6, weight="bold" if p["name"] == "TGT" else "normal")
    c0 = en[0]["ll"]
    ax.plot(c0[1], c0[0], "D", ms=5.5, color=INK, zorder=9)
    label(ax, c0[1], c0[0], "CVN-74\nTACAN 74X", INK, dy=-12, ha="center", va="top", size=6.4)
    scale_bar(ax, ext, 20)
    north_arrow(ax, ext)
    ax.legend(handles=[Line2D([], [], color=BLUE, lw=2, label="Strike route (solid in, dashed out)"),
                       Line2D([], [], color=RED, lw=1, ls="--", label="Radar floor zone"),
                       Line2D([], [], color=ORANGE, lw=1, label="Climb-out SAM reach (planned)"),
                       Line2D([], [], color=AQUA, lw=3, label="Tanker track")],
              loc="upper left", fontsize=6.2, framealpha=0.92, edgecolor=GRID)
    ax.set_title("THEATER  ·  route and threats", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=6)
    fig.tight_layout()
    fig.savefig(f"{stem}_theater.png", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)

    # ------------------------------------------------------------ gorge
    cen = [(canyon[0][0] + tgt[0]) / 2 + 0.01, (canyon[0][1] + tgt[1]) / 2 + 0.02]
    ext = ext_around(cen, 19, aspect=1.0)
    fig, ax = plt.subplots(figsize=(7.4, 7.0), dpi=220)
    base_map(ax, ext, 0.05)
    ax.set_facecolor(LAND)
    ring(ax, tgt, pop_r, color=ORANGE, lw=1.2, zorder=4)
    label(ax, *dest(tgt, 150, pop_r)[::-1], f"Attack zone, {pop_r / NM:.1f} nm:\npop-up allowed", ORANGE, dx=4, size=6.6)
    ring(ax, tgt, det_r, color=RED, lw=0.9, ls=(0, (4, 2)), zorder=4)
    label(ax, *dest(tgt, 205, det_r)[::-1], "Radar floor zone begins", RED, dx=6, size=6.6)
    ax.plot([p[1] for p in canyon], [p[0] for p in canyon], color=BLUE, lw=2.2, zorder=7)
    names = re.findall(r'\{ name = "([A-Z ]+)", x = -?[\d.]+, z = -?[\d.]+, r = 1500 \}', c)
    for nm_, p in zip(names, canyon):
        ax.plot(p[1], p[0], "o", ms=6, color="white", mec=BLUE, mew=1.4, zorder=9)
        if nm_ != "PORTAL":
            label(ax, p[1], p[0], nm_, BLUE, dx=-7, ha="right", size=6.8, weight="bold")
    ring(ax, tgt, cfg_num(c, "TGT_R"), color=INK2, lw=0.7, ls=(0, (1, 1.5)), zorder=5)
    ring(ax, tgt, cfg_num(c, "TEAM_R_MAX"), color=GREEN, lw=0.8, ls=(0, (2, 2)), zorder=5)
    label(ax, *dest(tgt, 330, cfg_num(c, "TEAM_R_MAX"))[::-1], "HATCHET: highest ground in this ring\nthat sees the door", GREEN, dx=-4, dy=6, ha="right", size=6.4)
    ax.plot(tgt[1], tgt[0], "*", ms=13, color=RED, mec="white", mew=0.8, zorder=11)
    label(ax, tgt[1], tgt[0], "PORTAL (planned)\nplaced on the floor within the dotted ring", RED, dx=9, dy=12, size=6.8, weight="bold")
    styles = {}
    for s in st:
        name, kind, x, z, r, types = s
        if kind == "guard":
            continue
        p = site_ll(s)
        if kind == "sam":
            mk, col = "P", RED
            reach = max(rng(t) for t in types)
            ring(ax, p, min(reach, 15000), color=RED, lw=0.6, alpha=0.45, zorder=3)
            lab = name.replace("Climb-out ", "") + " (high ground)"
            styles["Climb-out SAM: on the high ground within the dotted ring"] = (mk, col)
        else:
            mk, col = "D", ORANGE
            lab = name if "MANPADS" in name else name + " (guns + MANPADS)"
            styles["Guns / MANPADS: on the gorge floor within the dotted ring"] = (mk, col)
        ring(ax, p, r, color=col, lw=0.7, ls=(0, (1, 1.5)), zorder=5)
        ax.plot(p[1], p[0], mk, ms=7, color=col, mec="white", mew=0.6, zorder=10)
        label(ax, p[1], p[0], lab, col, dx=7, dy=(-7 if kind == "valley" and "MANPADS" in name else 6), size=6.4)
    for n_, (la, lo) in PLACES.items():
        if in_ext(ext, (la, lo), 0.005) and not n_.startswith("Khaishi"):
            ax.plot(lo, la, "s", ms=3, color=INK2, zorder=6)
            label(ax, lo, la, n_, INK2, dx=6, dy=-6, size=6.6)
    handles = [Line2D([], [], color=BLUE, lw=2.2, label="Gorge run (planned checkpoints)"),
               Line2D([], [], color=RED, lw=0.6, alpha=0.45, label="SAM reach (capped at 15 km here)")]
    handles += [Line2D([], [], marker=m_, ls="", color=c_, ms=7, label=l_) for l_, (m_, c_) in styles.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=6.2, framealpha=0.92, edgecolor=GRID)
    scale_bar(ax, ext, 5, y_frac=0.05)
    north_arrow(ax, ext)
    ax.set_title("THE GORGE  ·  planned points; the mission places everything on DCS terrain at start",
                 loc="left", fontsize=9, color=INK, fontweight="bold", pad=6)
    fig.tight_layout()
    fig.savefig(f"{stem}_gorge.png", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print("maps", stem)


if __name__ == "__main__":
    for f in sys.argv[1:]:
        draw(f)
