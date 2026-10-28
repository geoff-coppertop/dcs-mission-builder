"""Maps for the Narrow Gate follow-on missions (Long Road, Stone Ford, Sandy Lift), drawn from the built .miz files.

python3 maps_followon.py path/to/Operation_X.miz ...   -> <stem>_theater.png and <stem>_area.png in the working dir
"""
import re
import sys
from pathlib import Path
from collections import OrderedDict

import matplotlib.pyplot as plt

from missionbuilder.mapkit import *  # noqa: F401,F403
from missionbuilder.mapkit import Line2D


# ====================================================================== what each map shows
def spec_long_road(d):
    c = d["cfg"]
    restart = cfg_num(c, "RESTART")
    cover, cover_r = cfg_pt(c, "COVER"), cfg_num(c, "COVER_R")
    col = d["groups"]["Column"]["units"]
    col_c = [sum(u["ll"][0] for u in col) / len(col), sum(u["ll"][1] for u in col) / len(col)]
    turn = cfg_pt(c, "ROUTE")
    return dict(title="Operation Long Road", objective="TGT", area_center=[col_c[0] + 0.012, col_c[1] + 0.03], area_half_km=6.0,
                zones=[(cover, cover_r, "COVER: vehicles that reach the trees escape", GREEN, 160)],
                moves=[("Column", [col_c, turn, cover], RED, "Column route at " + hm(restart))],
                drone="Pontiac")


def spec_stone_ford(d, hard):
    c = d["cfg"]
    waves = [(g, float(t)) for g, t in re.findall(r'group = "(Wave \d+)", time = (\d+)', c)]
    bridge, br_r, contact_r = cfg_pt(c, "BRIDGE"), cfg_num(c, "BRIDGE_R"), cfg_num(c, "CONTACT_R")
    return dict(title="Operation Stone Ford" + (" (Hard)" if hard else ""), objective="TGT",
                area_center=[bridge[0] + 0.028, bridge[1] - 0.025], area_half_km=7.5, legend="upper right",
                zones=[(bridge, br_r, f"Village edge, {br_r:.0f} m: THROUGH", BLUE, 165),
                       (bridge, contact_r, "Contact line: Red opens fire", MUTED, 75)],
                moves=[(g, [p["ll"] for p in d["groups"][g]["route"]], RED, f"{g} {hm(t)}") for g, t in waves],
                drone=None)


def spec_sandy(d):
    c = d["cfg"]
    title = re.search(r'TITLE = "([^"]+)"', c).group(1).title()
    lz = cfg_pt(c, "LZ")
    search_t = cfg_num(c, "SEARCH_TIME")
    sp = d["groups"]["Search Party"]["units"][0]["ll"]
    return dict(title=title, objective="LZ", area_center=[lz[0] - 0.008, lz[1] + 0.012], area_half_km=5.5,
                zones=[(lz, cfg_num(c, "CAPTURE_R"), "Capture: 300 m", RED, 100),
                       (lz, cfg_num(c, "THREAT_R"), "5 km: threats reported in LZ report", MUTED, 150)],
                moves=[("Search Party", [sp, lz], RED, "Search party " + hm(search_t))],
                drone="Pontiac")

# ====================================================================== maps
def draw_theater(d, sp, path):
    g = d["groups"]
    en = g["Enfield"]["route"]
    ac = sp["area_center"]
    pts = [p["ll"] for p in en] + [dest(ac, b_, 28000) for b_ in (0, 90, 180, 270)]
    if "Arco" in g: pts += [p["ll"] for p in g["Arco"]["route"][:3]]
    ext = ext_fit(pts, pad=0.06, min_span=0.9)
    fig, ax = plt.subplots(figsize=(7.4, 6.2), dpi=220)
    base_map(ax, ext, 0.25 if ext[1] - ext[0] < 1.2 else 0.5)
    obj = [p["ll"] for p in en if p["name"] == sp["objective"]][0]
    for n, (la, lo) in TOWNS.items():
        if in_ext(ext, (la, lo), 0.02) and bearing_dist(obj, (la, lo))[1] > 3.0:
            ax.plot(lo, la, "s", ms=2.6, color=INK2, zorder=6)
            label(ax, lo, la, n, INK2, dx=4, dy=-1, size=6.6)
    # long-range SAM rings
    done = set()
    for gn, gg in g.items():
        if gg["side"] != "red" or gg["cat"] != "vehicle":
            continue
        for u in gg["units"]:
            r = threat_range(u["type"])
            if r >= 9000 and (gn, r) not in done:
                done.add((gn, r))
                us = [x["ll"] for x in gg["units"] if threat_range(x["type"]) == r]
                cen = [sum(p[0] for p in us) / len(us), sum(p[1] for p in us) / len(us)]
                ring_fill(ax, cen, r, color=RED, alpha=0.06, zorder=2, lw=0)
                ring(ax, cen, r, color=RED, lw=1.0, ls=(0, (4, 2)), zorder=3)
                nm_ = "SA-6" if "2P25" in u["type"] else ("SA-8" if "Osa" in u["type"] else u["type"])
                label(ax, *dest(cen, 30, r)[::-1], f"{nm_} ~{r / NM:.1f} nm", RED, dx=3, size=6.6)
    # red ground groups as one marker each
    for gn, gg in g.items():
        if gg["side"] == "red" and gg["cat"] == "vehicle" and gg["units"]:
            us = [u["ll"] for u in gg["units"]]
            cen = [sum(p[0] for p in us) / len(us), sum(p[1] for p in us) / len(us)]
            ax.plot(cen[1], cen[0], marker="X", ms=6, color=RED, mec="white", mew=0.7, zorder=8)
    for name, line, col, lab in sp["moves"]:
        for a, b in zip(line[:-1], line[1:]):
            arrow(ax, a, b, col, lw=1.0, ls=(0, (3, 2)))
    for z in sp["zones"]:
        c, r, lab, col = z[:4]
        if r < 2000:
            ring(ax, c, max(r, 900), color=col, lw=1.2, zorder=6)
    # blue ground
    for gn in ("Bridgehead", "Survivor"):
        if gn in g:
            u = g[gn]["units"][0]["ll"]
            ax.plot(u[1], u[0], marker="*", ms=10, color=GREEN if gn == "Survivor" else BLUE, mec="white", mew=0.7, zorder=10)
            if gn != "Survivor":
                label(ax, u[1], u[0], "Blue bridgehead", BLUE, dx=8, dy=-12, size=7, weight="bold")
    # carrier
    c0, cm = en[0]["ll"], en[-1]["ll"]
    arrow(ax, c0, [cm[0], cm[1] + 0.02], INK2, lw=1.0, ls=(0, (2, 2)))
    for p, t in [(c0, f"CVN-74 at {hm(d['start'])}\nTACAN 74X · ICLS 11"), (cm, "MOTHER (recovery, est.)\n27 kt, heading 270")]:
        ax.plot(p[1], p[0], "D", ms=5.5, color=INK, zorder=9)
        label(ax, p[1], p[0], t, INK, dy=-12, ha="center", va="top", size=6.6)
    # tanker / awacs / cap / helo
    if "Arco" in g:
        r = g["Arco"]["route"]
        a, b2 = r[1]["ll"], dest(r[1]["ll"], 230, 30000)
        ax.plot([a[1], b2[1]], [a[0], b2[0]], color=AQUA, lw=3.0, solid_capstyle="round", zorder=5)
        mid = dest(a, 230, 15000)
        label(ax, mid[1], mid[0], "ARCO 251.0 · 60Y · 15k", "#127a55", dx=-8, dy=2, ha="right", size=6.6)
    if "Magic" in g:
        a = g["Magic"]["route"][1]["ll"]; b2 = dest(a, 0, 40000)
        if in_ext(ext, a):
            ax.plot([a[1], b2[1]], [a[0], b2[0]], color=MUTED, lw=2.6, solid_capstyle="round", zorder=5)
            label(ax, b2[1], b2[0], "MAGIC E-2C 255.0", INK2, dx=5, size=6.6)
    if "Chevy" in g:
        r = g["Chevy"]["route"]
        st = [p for p in r if p["name"] == "CAP STATION"][0]["ll"]
        cm2 = [p for p in r if p["name"] == "COMMIT"][0]["ll"]
        ring(ax, st, 5000, color=VIOLET, lw=1.5, zorder=6)
        arrow(ax, dest(st, bearing_dist(st, cm2)[0], 5200), cm2, VIOLET, lw=0.9, ls=(0, (3, 2)))
        label(ax, *dest(st, 270, 5200)[::-1], "CHEVY CAP\nMAGIC commits", VIOLET, dx=-4, ha="right", size=6.6)
    if "Colt" in g:
        h = [p for p in g["Colt"]["route"] if p["name"] == "COLT HOLD"][0]["ll"]
        ax.plot(h[1], h[0], marker="o", ms=9, mfc="none", mec=VIOLET, mew=1.4, zorder=9)
        label(ax, h[1], h[0], "COLT holds\n(F10 push)", VIOLET, dx=-7, ha="right", size=6.6)
    if "Dodge" in g:
        h = [p for p in g["Dodge"]["route"] if p["name"] == "HOLD"][0]["ll"]
        ax.plot(h[1], h[0], marker="$H$", ms=9, color=BLUE, zorder=9)
        label(ax, h[1], h[0], "DODGE holds", BLUE, dx=0, dy=-10, ha="center", size=6.8)
        arrow(ax, h, g["Survivor"]["units"][0]["ll"], BLUE, lw=0.9, ls=(0, (2, 2)))
    for gn, gg in g.items():
        if gg["side"] == "red" and gg["cat"] == "plane":
            p = gg["units"][0]["ll"]
            if in_ext(ext, p):
                ax.plot(p[1], p[0], "^", ms=6, color=RED, zorder=8)
                label(ax, p[1], p[0], f"{gg['units'][0]['type']} ×{len(gg['units'])}", RED, dx=6, dy=4, size=6.6)
    # Enfield route
    names = [p["name"] or "START" for p in en]
    k = names.index(sp["objective"])
    xs, ys = [p["ll"][1] for p in en], [p["ll"][0] for p in en]
    ax.plot(xs[:k + 1], ys[:k + 1], color=BLUE, lw=2.0, zorder=7)
    ax.plot(xs[k:], ys[k:], color=BLUE, lw=2.0, ls=(0, (5, 2)), zorder=7)
    for i, p in enumerate(en):
        if i == 0 or p["name"] == "MOTHER":
            continue
        la, lo = p["ll"]
        ax.plot(lo, la, "o", ms=8.5, color="white", mec=BLUE, mew=1.6, zorder=10)
        ax.text(lo, la, str(i), ha="center", va="center", fontsize=6, color=BLUE, fontweight="bold", zorder=11)
        label(ax, lo, la, p["name"], BLUE, dx=7, dy=-7, size=6.8, weight="bold" if i == k else "normal")
    scale_bar(ax, ext, 10 if ext[1] - ext[0] < 1.2 else 20)
    north_arrow(ax, ext)
    handles = [Line2D([], [], color=BLUE, lw=2, label="Enfield route (solid in, dashed out)"),
               Line2D([], [], color=AQUA, lw=3, label="Tanker track"),
               Line2D([], [], color=VIOLET, lw=1.5, label="CAP station / commit"),
               Line2D([], [], color=RED, lw=1, ls="--", label="SAM coverage"),
               Line2D([], [], marker="X", ls="", color=RED, ms=6, label="Red ground group")]
    ax.legend(handles=handles, loc="upper left", fontsize=6.4, framealpha=0.92, edgecolor=GRID)
    ax.set_title("THEATER  ·  route, support and threats", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=6)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def draw_area(d, sp, path, title):
    g = d["groups"]
    ext = ext_around(sp["area_center"], sp["area_half_km"])
    fig, ax = plt.subplots(figsize=(7.4, 6.0), dpi=220)
    base_map(ax, ext, 0.05)
    for n, (la, lo) in TOWNS.items():
        if in_ext(ext, (la, lo), 0.005):
            ax.plot(lo, la, "s", ms=3, color=INK2, zorder=6)
            label(ax, lo, la, n, INK2, dx=5, dy=-2, size=7)
    for z in sp["zones"]:
        c, r, lab, col = z[:4]
        zb = z[4] if len(z) > 4 else 200
        ring(ax, c, r, color=col, lw=1.1, ls=(0, (5, 3)) if col == MUTED else "-", zorder=4)
        label(ax, *dest(c, zb, r)[::-1], lab, col if col != MUTED else INK2, dx=4, dy=0, ha="left", size=6.6)
    if sp["drone"] and sp["drone"] in g:
        o = [p for p in g[sp["drone"]]["route"] if p["name"] == "ORBIT"][0]["ll"]
        ring(ax, o, 4500, color=INK2, lw=0.8, ls=(0, (1, 1.5)), zorder=5)
        label(ax, *dest(o, 300, 4500)[::-1], f"{sp['drone'].upper()} MQ-9 orbit · laser 1688", INK2, dx=-4, dy=6, ha="right", size=6.6)
    styles = OrderedDict()
    big_rings = []
    for gn, gg in g.items():
        if gg["cat"] != "vehicle":
            continue
        for u in gg["units"]:
            p = u["ll"]
            if gg["side"] == "blue":
                if gn == "Survivor":
                    ax.plot(p[1], p[0], "*", ms=11, color=GREEN, mec="white", mew=0.7, zorder=10)
                    styles["Survivor"] = ("*", GREEN, 9)
                elif gn == "Axeman":
                    ax.plot(p[1], p[0], "*", ms=10, color=BLUE, mec="white", mew=0.7, zorder=10)
                    label(ax, p[1], p[0], "AXEMAN (JTAC)", BLUE, dx=6, dy=6, size=6.8, weight="bold")
                    styles["Blue JTAC"] = ("*", BLUE, 9)
                else:
                    ax.plot(p[1], p[0], "o", ms=3.2, color=BLUE, zorder=9)
                    styles["Blue infantry"] = ("o", BLUE, 4)
                continue
            if not in_ext(ext, p):
                continue
            mk, col, ms, lab = unit_style(u["type"])
            ax.plot(p[1], p[0], mk, ms=ms, color=col, mec="white" if mk not in ("1", ".") else col, mew=0.6, zorder=9)
            styles[lab] = (mk, col, ms)
            r = threat_range(u["type"]) if lab in AD_LABELS else 0
            if 0 < r < 9000:
                ring(ax, p, r, color=ORANGE, lw=0.8, zorder=3)
            elif r >= 9000:
                big_rings.append((u["type"], r, p))
    for name, line, col, lab in sp["moves"]:
        for a, b in zip(line[:-1], line[1:]):
            arrow(ax, a, b, col, lw=1.3, ls=(0, (4, 2)), z=8)
        label(ax, line[0][1], line[0][0], lab, col, dx=6, dy=8, size=6.8, weight="bold")
    if big_rings:
        kinds = sorted({("SA-6" if "2P25" in t else "SA-8") for t, _, _ in big_rings})
        label(ax, ext[0] + (ext[1] - ext[0]) * 0.02, ext[2] + (ext[3] - ext[2]) * 0.13,
              " and ".join(kinds) + " coverage reaches across this map", RED, size=7, weight="bold")
    handles = [Line2D([], [], marker=m, ls="", color=c, ms=s + 1, label=l) for l, (m, c, s) in styles.items()]
    handles.append(Line2D([], [], color=ORANGE, lw=0.8, label="Short-range air defence reach"))
    ax.legend(handles=handles, loc=sp.get("legend", "lower right"), fontsize=6.3, framealpha=0.92, edgecolor=GRID)
    scale_bar(ax, ext, 2, y_frac=0.05)
    north_arrow(ax, ext)
    ax.set_title(title, loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=6)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)



def draw(miz):
    d = parse_miz(miz)
    stem = Path(miz).stem
    if "Sandy_Lift" in stem:
        sp = spec_sandy(d)
    elif "Long_Road" in stem:
        sp = spec_long_road(d)
    else:
        sp = spec_stone_ford(d, "Hard" in stem)
    draw_theater(d, sp, f"{stem}_theater.png")
    draw_area(d, sp, f"{stem}_area.png", "OBJECTIVE AREA  ·  " + sp["title"])
    print("maps", stem)


if __name__ == "__main__":
    for f in sys.argv[1:]:
        draw(f)
