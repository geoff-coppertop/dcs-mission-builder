"""Draw theater map, target-area map and TOT timeline for the briefing PDF."""
import json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse
from global_land_mask import globe
from mission_times import *  # noqa: F401,F403

G = json.load(open("geom.json"))
grp = G["groups"]

# ---- palette (reference instance, light mode) + map neutrals
BLUE, AQUA, VIOLET, RED, ORANGE = "#2a78d6", "#1baf7a", "#6250d6", "#e34948", "#eb6834"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
LAND, SEA, COAST, GRID = "#ece6d8", "#dde9f3", "#9a9890", "#c9c7c0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED,
                     "axes.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2})

NM = 1852.0
R_E = 6371000.0


def bearing_dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlo = lo2 - lo1
    x = math.sin(dlo) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo)
    brg = (math.degrees(math.atan2(x, y)) + 360) % 360
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return brg, 2 * R_E * math.asin(math.sqrt(h)) / NM


def dest(p, brg_deg, dist_m):
    la1, lo1 = math.radians(p[0]), math.radians(p[1])
    b, d = math.radians(brg_deg), dist_m / R_E
    la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(b))
    lo2 = lo1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(la1), math.cos(d) - math.sin(la1) * math.sin(la2))
    return [math.degrees(la2), math.degrees(lo2)]


def base_map(ax, ext, step):
    lo0, lo1, la0, la1 = ext
    lons = np.linspace(lo0, lo1, 900)
    lats = np.linspace(la0, la1, int(900 * (la1 - la0) / (lo1 - lo0) / math.cos(math.radians(42.6))) + 2)
    LO, LA = np.meshgrid(lons, lats)
    land = globe.is_land(LA, LO).astype(float)
    ax.set_facecolor(SEA)
    ax.contourf(LO, LA, land, levels=[0.5, 1.5], colors=[LAND], zorder=0)
    ax.contour(LO, LA, land, levels=[0.5], colors=[COAST], linewidths=0.7, zorder=1)
    ax.set_xlim(lo0, lo1); ax.set_ylim(la0, la1)
    ax.set_aspect(1 / math.cos(math.radians((la0 + la1) / 2)))
    xt = np.arange(math.ceil(lo0 / step) * step, lo1, step)
    yt = np.arange(math.ceil(la0 / step) * step, la1, step)
    ax.set_xticks(xt); ax.set_yticks(yt)
    ax.set_xticklabels([f"{v:.1f}°E" for v in xt]); ax.set_yticklabels([f"{v:.1f}°N" for v in yt])
    ax.grid(color=GRID, linewidth=0.4, zorder=0.5)
    ax.tick_params(length=0, labelsize=7)


def scale_bar(ax, ext, nm, y_frac=0.04, x_frac=0.04):
    lo0, lo1, la0, la1 = ext
    lat = la0 + (la1 - la0) * y_frac
    lon = lo0 + (lo1 - lo0) * x_frac
    end = dest([lat, lon], 90, nm * NM)
    ax.plot([lon, end[1]], [lat, lat], color=INK, lw=2, solid_capstyle="butt", zorder=9)
    ax.text((lon + end[1]) / 2, lat + (la1 - la0) * 0.012, f"{nm} nm", ha="center", va="bottom",
            fontsize=7, color=INK, zorder=9)


def north_arrow(ax, ext):
    lo0, lo1, la0, la1 = ext
    x, y = lo1 - (lo1 - lo0) * 0.05, la1 - (la1 - la0) * 0.12
    ax.annotate("N", xy=(x, y + (la1 - la0) * 0.07), xytext=(x, y), ha="center", va="center",
                fontsize=9, fontweight="bold", color=INK,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=9)


def ring(ax, center, r_m, **kw):
    lat, lon = center
    pts = [dest(center, b, r_m) for b in range(0, 361, 4)]
    ax.plot([p[1] for p in pts], [p[0] for p in pts], **kw)
    return pts


def ring_fill(ax, center, r_m, **kw):
    pts = [dest(center, b, r_m) for b in range(0, 361, 4)]
    ax.fill([p[1] for p in pts], [p[0] for p in pts], **kw)


def label(ax, lon, lat, text, color=INK, dx=0, dy=0, ha="left", va="center", size=7.5, weight="normal"):
    t = ax.annotate(text, (lon, lat), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                    fontsize=size, color=color, fontweight=weight, zorder=12)
    t.set_path_effects([matplotlib.patheffects.withStroke(linewidth=2.6, foreground="white")])
    return t


import matplotlib.patheffects  # noqa: E402

route = grp["Enfield"]["route"]
WP = {w["name"] or "START": w["ll"] for w in route}
tgt = WP["TGT"]
sam_units = grp["Depot SAM"]["units"]
aaa_units = grp.get("Depot AAA", {"units": []})["units"]
sa6_launchers = [u for u in sam_units if "2P25" in u["type"]]
sam_center = [np.mean([u["ll"][0] for u in sam_units]), np.mean([u["ll"][1] for u in sam_units])]

# =================================================================== THEATER
ext = (39.95, 41.95, 41.98, 43.22)
fig, ax = plt.subplots(figsize=(7.4, 6.4), dpi=220)
base_map(ax, ext, 0.5)

towns = {"Sukhumi": (43.003, 41.023), "Gudauta": (43.105, 40.621), "Ochamchire": (42.712, 41.468),
         "Tkvarcheli": (42.851, 41.678), "Zugdidi": (42.509, 41.871), "Anaklia": (42.398, 41.563),
         "Poti": (42.146, 41.672)}
for n, (la, lo) in towns.items():
    ax.plot(lo, la, "s", ms=2.6, color=INK2, zorder=6)
    dx, dy = (4, -9) if n == "Ochamchire" else (4, -1)
    label(ax, lo, la, n, INK2, dx=dx, dy=dy, size=6.8)

# SA-6 threat ring
r_sa6 = 25000
ring_fill(ax, sam_center, r_sa6, color=RED, alpha=0.08, zorder=2, lw=0)
ring(ax, sam_center, r_sa6, color=RED, lw=1.0, ls=(0, (4, 2)), zorder=3)
label(ax, *dest(sam_center, 20, r_sa6)[::-1], f"SA-6 ~13.5 nm\njammed {T_SUP_ON}–{T_SUP_OFF}", RED, dx=4, size=6.8)

# FORD transit (jamming package passing through on its way north)
fr = {w["name"]: w["ll"] for w in grp["Ford"]["route"]}
f_all = [w["ll"] for w in grp["Ford"]["route"]]
ax.plot([p[1] for p in f_all], [p[0] for p in f_all], color="#127a55", lw=0.9, ls=(0, (1, 2)), zorder=5)
ax.plot([fr["JAM ON"][1], fr["CLOSEST"][1], fr["JAM OFF"][1]], [fr["JAM ON"][0], fr["CLOSEST"][0], fr["JAM OFF"][0]],
        color="#127a55", lw=2.0, ls=(0, (5, 1.5)), zorder=5)
_n = dest(fr["JAM OFF"], 320, 14000)
ax.annotate("", xy=(_n[1], _n[0]), xytext=(fr["JAM OFF"][1], fr["JAM OFF"][0]),
            arrowprops=dict(arrowstyle="-|>", color="#127a55", lw=1.0), zorder=5)
for k, t in [("JAM ON", T_SUP_ON), ("JAM OFF", T_SUP_OFF)]:
    ax.plot(fr[k][1], fr[k][0], "o", ms=3.5, color="#127a55", zorder=6)
    label(ax, fr[k][1], fr[k][0], f"{k.title()} {t[:5]}", "#127a55", dx=-5, dy=-2, ha="right", size=6.4)
_m = [(fr["JAM ON"][0] + fr["CLOSEST"][0]) / 2, (fr["JAM ON"][1] + fr["CLOSEST"][1]) / 2]
label(ax, _m[1], _m[0], "FORD ×2 F/A-18C\ntransiting north,\njamming the SA-6", "#127a55", dx=7, dy=-4, ha="left", va="top", size=6.6)

# MiG scramble
mig = grp["Red Scramble"]["units"][0]["ll"]
ax.plot(mig[1], mig[0], "^", ms=6, color=RED, zorder=8)
ax.annotate("", xy=(tgt[1] - 0.03, tgt[0] + 0.03), xytext=(mig[1], mig[0]),
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.0, ls=(0, (3, 2))), zorder=7)
label(ax, mig[1], mig[0], "MiG-21 alert ×2\nlaunch if LATE", RED, dx=6, dy=4, size=6.8)

# Gudauta dawn patrol: up some mornings only
_pr = {w["name"]: w["ll"] for w in grp["Red Patrol 29"]["route"]}
po = _pr["PATROL"]
_pe = dest(po, 180, 12000)   # drawn south of the anchor so the legend does not hide it
ax.plot([po[1], _pe[1]], [po[0], _pe[0]], color=RED, lw=2.6, alpha=0.45, solid_capstyle="round", zorder=5)
ax.plot([po[1], _pe[1]], [po[0], _pe[0]], color=RED, lw=0.8, ls=(0, (2, 2)), zorder=5)
label(ax, _pe[1], _pe[0], "Gudauta dawn patrol\nsome mornings only\nMiG-21s or MiG-29s", RED, dx=-6, dy=-2, ha="right", va="top", size=6.6)

# Carrier track
cvn = grp["CVN-74 Stennis"]
c0 = route[0]["ll"]; c1 = WP["MOTHER"]
ax.annotate("", xy=(c1[1] + 0.03, c1[0] - 0.0004), xytext=(c0[1], c0[0]),
            arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.0, ls=(0, (2, 2))), zorder=4)
for p, t, dy in [(c0, f"CVN-74 at {T_START_HM}\nTACAN 74X · ICLS 11", -14), (c1, f"MOTHER ~{T_REC_HM} (est.)\n27 kt, heading 270", -14)]:
    ax.plot(p[1], p[0], "D", ms=5.5, color=INK, zorder=9)
    label(ax, p[1], p[0], t, INK, dy=dy, ha="center", va="top", size=6.8)

# Tanker racetrack
arco = grp["Arco"]["route"]
a_anchor = WP["TANKER"]
a_end = dest(a_anchor, 230, 30000)
ax.plot([a_anchor[1], a_end[1]], [a_anchor[0], a_end[0]], color=AQUA, lw=3.2, alpha=0.9,
        solid_capstyle="round", zorder=5)
label(ax, a_end[1], a_end[0], "ARCO S-3B\n251.0 · 60Y · 15k", "#127a55", dx=-4, dy=-6, ha="right", va="top", size=6.8)

# AWACS
mg = grp["Magic"]["route"]
m_anchor = [mg[1]["ll"][0], mg[1]["ll"][1]] if len(mg) > 1 else mg[0]["ll"]
m_end = dest(m_anchor, 0, 40000)
ax.plot([m_anchor[1], m_end[1]], [m_anchor[0], m_end[0]], color=MUTED, lw=3.0, solid_capstyle="round", zorder=5)
label(ax, m_end[1], m_end[0], "MAGIC E-2C\n255.0", INK2, dx=5, size=6.8)

# CAP station and commit
chevy = grp["Chevy"]["route"]
cap = [w for w in chevy if w["name"] == "CAP STATION"][0]["ll"]
ring(ax, cap, 5000, color=VIOLET, lw=1.6, zorder=6)
ax.annotate("", xy=(WP["EGRESS"][1] - 0.02, WP["EGRESS"][0] - 0.02), xytext=(cap[1] + 0.02, cap[0] + 0.045),
            arrowprops=dict(arrowstyle="-|>", color=VIOLET, lw=1.0, ls=(0, (3, 2))), zorder=6)
ax.annotate("", xy=(cap[1] + 0.065, cap[0] + 0.005), xytext=(41.07, 42.33),
            arrowprops=dict(arrowstyle="-", color=VIOLET, lw=0.6), zorder=6)
label(ax, 41.07, 42.33, "CHEVY CAP · 2× F/A-18C · 20k\nMAGIC commits (FORD / EGRESS / boat)", VIOLET, dx=2, size=6.8)

# JTAC
ring(ax, tgt, 4500, color=INK2, lw=0.8, ls=(0, (1, 1.5)), zorder=6)
# Secondary: bridge (estimate = BRIDGE zone centre)
BR = G.get("bridge")
if BR:
    ax.plot(BR[1], BR[0], marker="X", ms=7, color=ORANGE, mec="white", mew=0.8, zorder=11)
    label(ax, BR[1], BR[0], "SEC 1: Mokvi bridge", "#b5481e", dx=-6, dy=8, ha="right", size=6.8)

# Enfield route
order = ["START", "DEPART", "PUSH", "IP", "TGT", "EGRESS", "TANKER", "MOTHER"]
xs = [WP[k][1] for k in order]; ys = [WP[k][0] for k in order]
ax.plot(xs[:5], ys[:5], color=BLUE, lw=2.0, zorder=7, solid_joinstyle="round")
ax.plot(xs[4:], ys[4:], color=BLUE, lw=2.0, zorder=7, ls=(0, (5, 2)))
offs = {"DEPART": (7, -4, "left"), "PUSH": (8, -2, "left"), "IP": (8, -10, "left"),
        "TGT": (9, 9, "left"), "EGRESS": (0, 13, "center"), "TANKER": (-8, 10, "right")}
for i, k in enumerate(order):
    if k in ("START", "MOTHER"):
        continue
    la, lo = WP[k]
    ax.plot(lo, la, "o", ms=8.5, color="white", mec=BLUE, mew=1.6, zorder=10)
    ax.text(lo, la, str(i), ha="center", va="center", fontsize=6, color=BLUE, fontweight="bold", zorder=11)
    dx, dy, ha = offs[k]
    extra = {"PUSH": " · hold", "TGT": f"  TOT {T_TOT}L", "IP": " · 20,000 ft"}.get(k, "")
    label(ax, lo, la, f"{k}{extra}", BLUE if k != "TGT" else INK, dx=dx, dy=dy, ha=ha, size=7,
          weight="bold" if k == "TGT" else "normal")
ax.plot(tgt[1], tgt[0], marker=(4, 1, 0), ms=11, color=RED, mew=1.4, zorder=11)

scale_bar(ax, ext, 20)
north_arrow(ax, ext)
ax.set_title("THEATER  ·  route, support and threats", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=6)

# legend (direct labels carry identity; legend repeats it)
from matplotlib.lines import Line2D
handles = [Line2D([], [], color=BLUE, lw=2, label="Enfield route (solid in, dashed out)"),
           Line2D([], [], color=AQUA, lw=3, label="Tanker track"),
           Line2D([], [], color=VIOLET, lw=1.6, label="CAP orbit / commit"),
           Line2D([], [], color="#127a55", lw=2.0, ls=(0, (5, 1.5)), label="FORD transit (heavy = jamming)"),
           Line2D([], [], color=RED, lw=1, ls="--", label="Threat"),
           Line2D([], [], color=INK2, lw=1, ls=":", label="Carrier track / JTAC orbit")]
lg = ax.legend(handles=handles, loc="upper left", fontsize=6.6, frameon=True, framealpha=0.92,
               edgecolor=GRID, borderpad=0.6)
fig.tight_layout()
fig.savefig("map_theater.png", bbox_inches="tight", pad_inches=0.08)
plt.close(fig)

# =================================================================== TARGET AREA
half_km = 9.0
dlat = half_km * 1000 / 111320
dlon = dlat / math.cos(math.radians(tgt[0]))
ext2 = (tgt[1] - dlon * 1.15, tgt[1] + dlon * 1.15, tgt[0] - dlat, tgt[0] + dlat)
fig, ax = plt.subplots(figsize=(7.4, 6.6), dpi=220)
base_map(ax, ext2, 0.05)
ax.set_xticklabels([f"{v:.2f}°E" for v in ax.get_xticks()])
ax.set_yticklabels([f"{v:.2f}°N" for v in ax.get_yticks()])

# scoring ring
ring(ax, tgt, 2500, color=INK, lw=0.9, ls=(0, (5, 3)), zorder=4)
label(ax, *dest(tgt, 135, 2500)[::-1], "2.5 km scoring radius", INK2, dx=4, dy=-4, size=6.8)
# ZSU ring
zsus = [u["ll"] for u in aaa_units if "ZSU" in u["type"]]
for zsu in zsus:
    ring_fill(ax, zsu, 2500, color=ORANGE, alpha=0.10, lw=0, zorder=2)
    ring(ax, zsu, 2500, color=ORANGE, lw=0.9, zorder=3)
zn = max(zsus, key=lambda p: p[0])
label(ax, *dest(zn, 0, 2500)[::-1], "2× ZSU-23-4 ~1.3 nm, below ~8,000 ft · NOT jammed", "#b5481e", dy=7, ha="center", size=6.8)
for u in aaa_units:
    if "Strela" in u["type"]:
        ring(ax, u["ll"], 5000, color=ORANGE, lw=1.0, ls=(0, (6, 3)), zorder=3)
        label(ax, *dest(u["ll"], 345, 5000)[::-1], "SA-13 (IR) ~2.7 nm, below ~16,000 ft · NOT jammed",
              "#b5481e", dx=-2, dy=7, ha="right", size=6.8)
# SA-6 edge note
label(ax, ext2[0] + (ext2[1]-ext2[0])*0.02, ext2[3] - (ext2[3]-ext2[2])*0.05,
      "Entire map is inside SA-6 coverage (~13.5 nm)", RED, size=7, weight="bold")

# Inbound / outbound
ip, eg = WP["IP"], WP["EGRESS"]
brg_in, _ = bearing_dist(ip, tgt)
brg_out, _ = bearing_dist(tgt, eg)
p_in = dest(tgt, (brg_in + 180) % 360, 8500)
ax.annotate("", xy=(tgt[1] - 0.004, tgt[0] - 0.003), xytext=(p_in[1], p_in[0]),
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.0), zorder=7)
label(ax, p_in[1], p_in[0], f"Inbound from IP\n{brg_in:03.0f}° true", BLUE, dx=4, dy=-12, size=7, weight="bold")
p_out = dest(tgt, brg_out, 8500)
ax.annotate("", xy=(p_out[1], p_out[0]), xytext=(tgt[1] - 0.006, tgt[0] - 0.001),
            arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.6, ls=(0, (4, 2))), zorder=7)
label(ax, p_out[1], p_out[0], f"Egress\n{brg_out:03.0f}° true", BLUE, dx=-4, dy=8, ha="right", size=7)

# JTAC orbit
ring(ax, tgt, 4500, color=INK2, lw=0.9, ls=(0, (1, 1.5)), zorder=5)
label(ax, *dest(tgt, 300, 4500)[::-1], "PONTIAC MQ-9 orbit · laser 1688", INK2, dx=-4, dy=6, ha="right", size=6.8)

# Secondary bridge
if G.get("bridge"):
    BR = G["bridge"]
    ring(ax, BR, G.get("bridge_r", 600), color=ORANGE, lw=0.8, ls=(0, (2, 2)), zorder=5)
    ax.plot(BR[1], BR[0], marker="X", ms=9, color=ORANGE, mec="white", mew=0.9, zorder=10)
    b_brg, b_nm = bearing_dist(tgt, BR)
    label(ax, BR[1], BR[0], f"SECONDARY: coast-road bridge\nover the Mokvi ({b_nm:.1f} nm, {b_brg:03.0f}° from depot)\n"
          "dashed ring = BRIDGE search zone", "#b5481e", dx=0, dy=-16, ha="center", va="top", size=6.6)

# Units
for u in grp["Depot Targets"]["units"]:
    la, lo = u["ll"]
    is_tank = "T-72" in u["type"]
    ax.plot(lo, la, "s" if is_tank else "o", ms=4.2 if is_tank else 3.4, color=RED, mec="white", mew=0.6, zorder=9)
for u in sam_units + aaa_units:
    la, lo = u["ll"]
    mk = {"Kub 1S91 str": "P", "Kub 2P25 ln": "^", "ZSU-23-4 Shilka": "D", "Strela-10M3": "v"}[u["type"]]
    ax.plot(lo, la, mk, ms=5.2, color=RED if "Kub" in u["type"] else ORANGE, mec="white", mew=0.6, zorder=9)
label(ax, tgt[1], tgt[0], "DEPOT", INK, dx=10, dy=-14, ha="left", size=7.2, weight="bold")
label(ax, sam_center[1], sam_center[0], "SA-6 battery", RED, dx=9, dy=4, size=7)

scale_bar(ax, ext2, 2, y_frac=0.05)

# inset: depot and SAM detail (~1.6 km box)
ins = ax.inset_axes([0.64, 0.06, 0.34, 0.40])
ins.set_facecolor(LAND)
allu = grp["Depot Targets"]["units"] + sam_units + aaa_units
cl = np.mean([u["ll"][0] for u in allu]); cn = np.mean([u["ll"][1] for u in allu])
h = 1150 / 111320; w = h / math.cos(math.radians(cl))
ins.set_xlim(cn - w, cn + w); ins.set_ylim(cl - h, cl + h)
ins.set_aspect(1 / math.cos(math.radians(cl)))
ins.set_xticks([]); ins.set_yticks([])
for sp in ins.spines.values():
    sp.set_color(MUTED); sp.set_linewidth(0.8)
for u in grp["Depot Targets"]["units"]:
    la, lo = u["ll"]; tank = "T-72" in u["type"]
    ins.plot(lo, la, "s" if tank else "o", ms=6.5 if tank else 5.5, color=RED, mec="white", mew=0.8, zorder=5)
for u in sam_units + aaa_units:
    la, lo = u["ll"]
    mk = {"Kub 1S91 str": "P", "Kub 2P25 ln": "^", "ZSU-23-4 Shilka": "D", "Strela-10M3": "v"}[u["type"]]
    ins.plot(lo, la, mk, ms=7, color=RED if "Kub" in u["type"] else ORANGE, mec="white", mew=0.8, zorder=5)
e0 = dest([cl - h * 0.82, cn - w * 0.9], 90, 200)
ins.plot([cn - w * 0.9, e0[1]], [cl - h * 0.82] * 2, color=INK, lw=1.6)
ins.text((cn - w * 0.9 + e0[1]) / 2, cl - h * 0.76, "200 m", ha="center", fontsize=6, color=INK)
ins.set_title("Depot detail", fontsize=7, color=INK, loc="left", pad=2)
lab = ins.annotate("Targets", (tgt[1], tgt[0]), xytext=(-6, -14), textcoords="offset points", ha="right",
                   fontsize=6.5, color=INK, fontweight="bold")

north_arrow(ax, ext2)
handles = [Line2D([], [], marker="s", ls="", color=RED, ms=5, label="T-72B (target)"),
           Line2D([], [], marker="o", ls="", color=RED, ms=4, label="Ural-375 truck (target)"),
           Line2D([], [], marker="P", ls="", color=RED, ms=6, label="SA-6 radar"),
           Line2D([], [], marker="^", ls="", color=RED, ms=6, label="SA-6 launcher"),
           Line2D([], [], marker="D", ls="", color=ORANGE, ms=5, label="ZSU-23-4 (not jammed)"),
           Line2D([], [], marker="v", ls="", color=ORANGE, ms=6, label="SA-13 (not jammed)")]
ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.93, 0.99), fontsize=6.6, framealpha=0.92, edgecolor=GRID)
ax.set_title("TARGET AREA  ·  NE of Ochamchire", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=6)
fig.tight_layout()
fig.savefig("map_target.png", bbox_inches="tight", pad_inches=0.08)
plt.close(fig)

# =================================================================== TIMELINE
def hhmm(sec):
    sec = int(round(sec))
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}"

TOT = TOT_S
spd_kt = 420
_, d_push_ip = bearing_dist(WP["PUSH"], WP["IP"])
_, d_ip_tgt = bearing_dist(WP["IP"], WP["TGT"])
t_ip = TOT - d_ip_tgt / spd_kt * 3600
t_push = t_ip - d_push_ip / spd_kt * 3600

fig, ax = plt.subplots(figsize=(7.4, 2.5), dpi=220)
t0, t1 = START_S, START_S + 40 * 60
ax.set_xlim(t0, t1); ax.set_ylim(0, 3)
SUP0, SUP1 = TOT - SUP_BEFORE, TOT + SUP_AFTER
ax.axvspan(t0, SUP0, color=RED, alpha=0.06, lw=0)
ax.axvspan(SUP0, SUP1, color=AQUA, alpha=0.13, lw=0)
ax.axvspan(TOT - 60, TOT + 60, color=AQUA, alpha=0.30, lw=0)
ax.axvspan(SUP1, t1, color=RED, alpha=0.06, lw=0)
ax.axvline(TOT, color=INK, lw=1.4)
ax.text(SUP1 + 20, 2.88, f"TOT {T_TOT}", ha="left", va="top", fontsize=7.5, fontweight="bold", color=INK)
ax.text(SUP1 + 20, 2.58, "Impact window ±60 s", ha="left", va="top", fontsize=6.8, color="#127a55", fontweight="bold")
ax.text(SUP1 + 20, 2.30, f"FORD jamming {T_SUP_ON}–{T_SUP_OFF}", ha="left", va="top", fontsize=6.8, color="#127a55")
ax.text((t0 + SUP0) / 2, 0.12, "EARLY: SA-6 live", ha="center", va="bottom", fontsize=7, color=RED)
ax.text(SUP1 + 20, 0.12, "LATE: SA-6 back up,\nMiG-21 alert launches\n(MAGIC commits CAP)", ha="left",
        va="bottom", fontsize=7, color=RED)

# estimated time inside SA-6 range (420 kt, release ~4 nm, ~40 s bomb fall, ~25 s turn, egress at 420 kt)
ring_nm = 13.2
t_in = 40 + (ring_nm - 4) / (spd_kt / 60) * 60
t_out = -40 + 25 + (ring_nm - 4) / (spd_kt / 60) * 60
for y, off, who in [(0.72, 0, "Lead"), (0.46, 30, "Wing")]:
    ax.barh(y, t_out + t_in, left=TOT + off - t_in, height=0.16, color=RED, alpha=0.75, edgecolor="white", lw=1)
    ax.text(TOT + off - t_in - 15, y, f"{who} in SA-6 range (est.)", ha="right", va="center", fontsize=6.3, color=INK2)

# lane: Enfield plan
bars = [(t0, t0 + 15 * 60, "Cold start · fast align · launch (~15 min)", MUTED),
        (t0 + 15 * 60, t_push, "Transit + hold at PUSH", "#9dbfe8"),
        (t_push, TOT, "", BLUE)]
for a, b, txt, col in bars:
    ax.barh(1.95, b - a, left=a, height=0.42, color=col, edgecolor="white", linewidth=2)
    if txt and b - a > 150:
        ax.text((a + b) / 2, 1.95, txt, ha="center", va="center", fontsize=6.6,
                color="white" if col in (BLUE, MUTED) else INK)
def hms_r(sec):
    sec = int(round(sec))
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"
for t, txt in [(t_push, f"PUSH {hms_r(t_push)}"), (t_ip, f"IP {hms_r(t_ip)}")]:
    ax.plot([t, t], [1.72, 2.18], color=INK, lw=0.8)
    ax.text(t, 1.66, txt, ha="right" if "PUSH" in txt else "center", va="top", fontsize=6.6, color=INK)
# radio calls
for t, txt, ha in [(TOT - 600, "MAGIC: 10 min", "right"), (TOT - SUP_BEFORE - 300, "FORD inbound", "left")]:
    ax.plot(t, 1.25, "v", ms=5, color=INK2)
    ax.text(t + (-15 if ha == "right" else 15), 1.1, txt, ha=ha, va="top", fontsize=6.4, color=INK2)
ax.set_yticks([])
ticks = list(range(t0, t1 + 1, 300))
ax.set_xticks(ticks); ax.set_xticklabels([hhmm(t) for t in ticks])
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
ax.tick_params(axis="x", labelsize=7, length=3, color=MUTED)
ax.set_xlabel("Mission local time (Zulu = local − 4 h)", fontsize=7, color=INK2)
ax.set_title("TIMELINE  ·  plan at 420 kt ground speed", loc="left", fontsize=9.5, color=INK, fontweight="bold", pad=4)
fig.tight_layout()
fig.savefig("timeline.png", bbox_inches="tight", pad_inches=0.08)
plt.close(fig)

# timing numbers for the PDF
json.dump({"t_push": t_push, "t_ip": t_ip, "brg_in": brg_in, "brg_out": brg_out}, open("timing.json", "w"))
print("push", t_push, "ip", t_ip, "inbound", round(brg_in), "outbound", round(brg_out))
