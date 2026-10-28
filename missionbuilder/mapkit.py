"""Map drawing and mission-file parsing shared by the campaign briefing PDFs."""
import math
import re
import zipfile

import lupa
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from global_land_mask import globe
import dcs
from dcs import mapping
import dcs.vehicles as V
import dcs.weapons_data as WD

BLUE, AQUA, VIOLET, RED, ORANGE, GREEN = "#2a78d6", "#1baf7a", "#6250d6", "#e34948", "#eb6834", "#008300"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
LAND, SEA, COAST, GRID = "#ece6d8", "#dde9f3", "#9a9890", "#c9c7c0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED,
                     "axes.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2})
NM = 1852.0
R_E = 6371000.0
TERRAIN = dcs.terrain.Caucasus()
TOWNS = {"Sukhumi": (43.003, 41.023), "Gudauta": (43.105, 40.621), "Ochamchire": (42.712, 41.468),
         "Tkvarcheli": (42.851, 41.678), "Zugdidi": (42.509, 41.871), "Anaklia": (42.398, 41.563),
         "Poti": (42.146, 41.672), "Gali": (42.627, 41.735), "Ganmukhuri": (42.4253, 41.6283)}


# ------------------------------------------------------------------ geometry
def xz_to_ll(x, z):
    p = mapping.Point(x, z, TERRAIN).latlng()
    return [p.lat, p.lng]


def bearing_dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlo = lo2 - lo1
    brg = (math.degrees(math.atan2(math.sin(dlo) * math.cos(la2),
           math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo))) + 360) % 360
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return brg, 2 * R_E * math.asin(math.sqrt(h)) / NM


def dest(p, brg_deg, dist_m):
    la1, lo1 = math.radians(p[0]), math.radians(p[1])
    b, d = math.radians(brg_deg), dist_m / R_E
    la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(b))
    lo2 = lo1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(la1), math.cos(d) - math.sin(la1) * math.sin(la2))
    return [math.degrees(la2), math.degrees(lo2)]


def compass(deg):
    return ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][int(((deg + 22.5) % 360) // 45)]


def ddm(lat, lon):
    def f(v, p, n, w):
        h = p if v >= 0 else n
        v = abs(v); d = int(v)
        return f"{h} {d:0{w}d}°{(v - d) * 60:06.3f}'"
    return f(lat, "N", "S", 2) + "  " + f(lon, "E", "W", 3)


def hms(s):
    s = int(round(s)) % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def hm(s):
    return hms(s)[:5]


# ------------------------------------------------------------------ mission parsing
def parse_miz(path):
    L = lupa.LuaRuntime(unpack_returned_tuples=True)
    with zipfile.ZipFile(path) as z:
        L.execute(z.read("mission").decode("utf-8"))
        L.execute(z.read("l10n/DEFAULT/dictionary").decode("utf-8"))
    mis, dic = L.globals().mission, L.globals().dictionary
    out = {"start": mis.start_time, "groups": {}, "desc": dic[mis.descriptionText], "task": dic[mis.descriptionBlueTask],
           "sortie": dic[mis.sortie]}
    for side in ("blue", "red"):
        for _, c in mis.coalition[side].country.items():
            for cat in ("plane", "helicopter", "ship", "vehicle"):
                if not c[cat]:
                    continue
                for _, g in c[cat].group.items():
                    units = []
                    for ui in range(1, len(g.units) + 1):      # index order, not pairs() order
                        u = g.units[ui]
                        d = {"name": u.name, "type": u.type, "ll": xz_to_ll(u.x, u.y), "x": u.x, "z": u.y}
                        if u.payload and u.payload.pylons:
                            d["pylons"] = {int(k): v.CLSID for k, v in u.payload.pylons.items()}
                        units.append(d)
                    pts = g.route.points
                    route = [{"name": pts[i].name or "", "type": pts[i].type, "ll": xz_to_ll(pts[i].x, pts[i].y),
                              "alt": pts[i].alt, "speed": pts[i].speed} for i in range(1, len(pts) + 1)]
                    out["groups"][g.name] = {"side": side, "cat": cat, "units": units, "route": route,
                                             "late": bool(g.lateActivation)}
    # the mission script is the DO SCRIPT that carries the "T.cfg = {" block
    out["cfg"], out["scripts"] = "", []
    for ti in range(1, len(mis.trigrules) + 1):
        acts = mis.trigrules[ti].actions
        for ai in range(1, len(acts) + 1):
            a = acts[ai]
            if a.predicate == "a_do_script" and a.text and dic[a.text]:
                txt = dic[a.text]
                out["scripts"].append(txt)
                if "T.cfg = {" in txt:
                    out["cfg"] = txt
    return out


def cfg_num(cfg, key):
    m = re.search(rf"\b{key}\s*=\s*(-?[\d.]+)", cfg)
    return float(m.group(1)) if m else None


def cfg_pt(cfg, key):
    m = re.search(rf"\b{key}\s*=\s*\{{\s*(?:\{{\s*)?x\s*=\s*(-?[\d.]+),\s*z\s*=\s*(-?[\d.]+)", cfg)
    return xz_to_ll(float(m.group(1)), float(m.group(2))) if m else None


def store_name(clsid):
    n = WD.weapon_ids.get(clsid, {}).get("name", clsid)
    n = re.sub(r"\s*-\s*(Active Radar AAM|IR AAM|Targeting Pod|High Speed Anti-Radiation Missile|500lb Laser Guided Bomb)$", "", n)
    n = n.replace("LAU-115 with 1 x LAU-127 ", "").replace("BRU-33 with ", "")
    n = n.replace("Mk-20 Rockeye - 490lbs CBU, 247 x HEAT Bomblets", "Mk-20 Rockeye")
    n = n.replace("LAU-117 with AGM-65F - Maverick F (IIR ASM)", "AGM-65F Maverick").replace("LAU-117 AGM-65F", "AGM-65F Maverick")
    n = n.replace("FPU-8A Fuel Tank 330 gallons", "FPU-8A tank 330 gal").replace("AN/AAQ-28 LITENING", "LITENING")
    if "AGM-65F" in n: n = "AGM-65F Maverick"
    if "AGM-88C" in n: n = "AGM-88C HARM"
    if n.startswith("AIM-9X"): n = "AIM-9X"
    if "AIM-120C" in n: n = "AIM-120C"
    if "LITENING" in n: n = "LITENING pod"
    return n


AD_LABELS = {"SA-6 radar", "SA-6 launcher", "SA-8", "SA-13 (IR)", "SA-9 (IR)", "MANPADS", "AAA"}


def threat_range(type_id):
    c = V.vehicle_map.get(type_id)
    return getattr(c, "threat_range", 0) or 0 if c else 0


def unit_style(t):
    """(marker, color, size, legend label) for a DCS ground type id."""
    if "1S91" in t: return "P", RED, 7, "SA-6 radar"
    if "2P25" in t: return "^", RED, 6, "SA-6 launcher"
    if "Osa" in t: return "^", RED, 7, "SA-8"
    if "Strela-10" in t: return "v", ORANGE, 7, "SA-13 (IR)"
    if "Strela-1" in t: return "v", ORANGE, 7, "SA-9 (IR)"
    if "Igla" in t: return "1", ORANGE, 8, "MANPADS"
    if "ZSU" in t or "ZU-23" in t: return "D", ORANGE, 5.5, "AAA"
    if "T-72" in t: return "s", RED, 5, "Tank"
    if "BMP" in t or "BTR" in t: return "s", "#b23332", 4.5, "IFV / APC"
    if "ATZ" in t or "Ural" in t: return "o", RED, 4, "Truck"
    if "Soldier" in t or "Paratrooper" in t: return ".", RED, 4, "Infantry"
    return "x", RED, 5, "Other"


# ------------------------------------------------------------------ drawing
def base_map(ax, ext, step):
    lo0, lo1, la0, la1 = ext
    lons = np.linspace(lo0, lo1, 900)
    lats = np.linspace(la0, la1, int(900 * (la1 - la0) / (lo1 - lo0) / math.cos(math.radians((la0 + la1) / 2))) + 2)
    LO, LA = np.meshgrid(lons, lats)
    land = globe.is_land(LA, LO).astype(float)
    ax.set_facecolor(SEA)
    if land.max() > 0:
        ax.contourf(LO, LA, land, levels=[0.5, 1.5], colors=[LAND], zorder=0)
        ax.contour(LO, LA, land, levels=[0.5], colors=[COAST], linewidths=0.7, zorder=1)
    ax.set_xlim(lo0, lo1); ax.set_ylim(la0, la1)
    ax.set_aspect(1 / math.cos(math.radians((la0 + la1) / 2)))
    xt = np.arange(math.ceil(lo0 / step) * step, lo1, step)
    yt = np.arange(math.ceil(la0 / step) * step, la1, step)
    dec = 1 if step >= 0.1 else 2
    ax.set_xticks(xt); ax.set_yticks(yt)
    ax.set_xticklabels([f"{v:.{dec}f}°E" for v in xt]); ax.set_yticklabels([f"{v:.{dec}f}°N" for v in yt])
    ax.grid(color=GRID, linewidth=0.4, zorder=0.5)
    ax.tick_params(length=0, labelsize=7)


def ext_around(center, half_km, aspect=1.15):
    dlat = half_km * 1000 / 111320
    dlon = dlat / math.cos(math.radians(center[0])) * aspect
    return (center[1] - dlon, center[1] + dlon, center[0] - dlat, center[0] + dlat)


def ext_fit(points, pad=0.12, min_span=0.6):
    lats = [p[0] for p in points]; lons = [p[1] for p in points]
    la0, la1, lo0, lo1 = min(lats), max(lats), min(lons), max(lons)
    la_c, lo_c = (la0 + la1) / 2, (lo0 + lo1) / 2
    span_la = max(la1 - la0, min_span * 0.6) * (1 + pad * 2)
    span_lo = max(lo1 - lo0, min_span) * (1 + pad * 2)
    k = math.cos(math.radians(la_c))
    if span_lo * k < span_la * 1.05:      # keep a landscape-ish frame
        span_lo = span_la * 1.05 / k
    if span_la < span_lo * k * 0.74:      # but not a letterbox
        span_la = span_lo * k * 0.74
    return (lo_c - span_lo / 2, lo_c + span_lo / 2, la_c - span_la / 2, la_c + span_la / 2)


def ring(ax, center, r_m, **kw):
    pts = [dest(center, b, r_m) for b in range(0, 361, 4)]
    ax.plot([p[1] for p in pts], [p[0] for p in pts], **kw)


def ring_fill(ax, center, r_m, **kw):
    pts = [dest(center, b, r_m) for b in range(0, 361, 4)]
    ax.fill([p[1] for p in pts], [p[0] for p in pts], **kw)


def label(ax, lon, lat, text, color=INK, dx=0, dy=0, ha="left", va="center", size=7.2, weight="normal"):
    t = ax.annotate(text, (lon, lat), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                    fontsize=size, color=color, fontweight=weight, zorder=12)
    t.set_path_effects([pe.withStroke(linewidth=2.6, foreground="white")])
    return t


def arrow(ax, a, b, color, lw=1.2, ls="-", z=7):
    ax.annotate("", xy=(b[1], b[0]), xytext=(a[1], a[0]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls), zorder=z)


def scale_bar(ax, ext, nm, y_frac=0.05, x_frac=0.04):
    lo0, lo1, la0, la1 = ext
    lat = la0 + (la1 - la0) * y_frac
    lon = lo0 + (lo1 - lo0) * x_frac
    end = dest([lat, lon], 90, nm * NM)
    ax.plot([lon, end[1]], [lat, lat], color=INK, lw=2, solid_capstyle="butt", zorder=9)
    ax.text((lon + end[1]) / 2, lat + (la1 - la0) * 0.012, f"{nm:g} nm", ha="center", va="bottom", fontsize=7, color=INK, zorder=9)


def north_arrow(ax, ext):
    lo0, lo1, la0, la1 = ext
    x, y = lo1 - (lo1 - lo0) * 0.05, la1 - (la1 - la0) * 0.12
    ax.annotate("N", xy=(x, y + (la1 - la0) * 0.07), xytext=(x, y), ha="center", va="center",
                fontsize=9, fontweight="bold", color=INK, arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=9)


def in_ext(ext, p, m=0.0):
    lo0, lo1, la0, la1 = ext
    return lo0 + m <= p[1] <= lo1 - m and la0 + m <= p[0] <= la1 - m
