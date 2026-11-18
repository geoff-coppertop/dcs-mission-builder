"""Briefing context for Operation Deep Cut: every number the Markdown needs, read from the built .miz."""
import re
from pathlib import Path

import mgrs as mgrslib

from missionbuilder.mapkit import parse_miz, cfg_num, cfg_pt, bearing_dist, ddm, hms, hm, store_name, NM

ZULU = 4 * 3600


def sites(cfg):
    """[(name, kind, x, z, r, [unit types])] from the script's SITES table."""
    out = []
    for m in re.finditer(r'\{ name = "([^"]+)", kind = "(\w+)", x = (-?[\d.]+), z = (-?[\d.]+), r = (\d+), '
                         r'heading = \d+, units = \{ (.*?) \} \},', cfg):
        types = re.findall(r'\{ "([^"]+)", -?\d+, -?\d+ \}', m.group(6))
        out.append((m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), int(m.group(5)), types))
    return out


def route(d, group, times=None):
    pts = d["groups"][group]["route"]
    rows = []
    for i, p in enumerate(pts):
        name = "CVN-74 (deck)" if i == 0 else ("MOTHER (land)" if p["name"] == "MOTHER" else p["name"])
        if i == 0 or p["name"] == "MOTHER":
            alt = "deck"
        elif p.get("alt_type") == "RADIO":
            alt = f"{round(p['alt'] / 0.3048, -1):,.0f} ft AGL"
        else:
            alt = f"{round(p['alt'] / 0.3048, -2):,.0f} ft"
        leg = crs = ""
        if i:
            b, dist = bearing_dist(pts[i - 1]["ll"], p["ll"])
            leg, crs = f"{dist:.1f} nm", f"{b:03.0f}°"
        rows.append(dict(wp=i, name=name, coords=ddm(*p["ll"]), alt=alt, leg=leg, course=crs,
                         time=(times or {}).get(p["name"], "")))
    return rows


def loadout(d, group):
    u = d["groups"][group]["units"][0]
    return [store_name(u["pylons"][s]) if u.get("pylons", {}).get(s) else "—" for s in range(1, 11)]


def deep_cut(miz, work):
    d = parse_miz(miz)
    c = d["cfg"]
    hard = "(HARD)" in c
    n = {k: cfg_num(c, k) for k in ("START", "TOT", "WINDOW", "HAMMER", "REPAIR", "SAM_UP", "REACT", "KILL_WINDOW",
                                   "FLOOR_FT", "GRACE", "DET_R", "POP_R", "ALERT_REACT", "BREACH_R", "TEAM_R_MIN", "TEAM_R_MAX",
                                   "PTS_BREACH", "PTS_KILL", "PTS_ONTIME", "PTS_UNSEEN", "PTS_SURVIVAL")}
    tot = n["TOT"]
    en = d["groups"]["Enfield"]["route"]
    wp = {p["name"]: p for p in en}
    tgt = cfg_pt(c, "TGT")
    m = mgrslib.MGRS().toMGRS(tgt[0], tgt[1], MGRSPrecision=5)
    gate_tgt = bearing_dist(wp["GATE"]["ll"], tgt)[1]
    canyon = sum(bearing_dist(a["ll"], b["ll"])[1] for a, b in zip(en[4:9], en[5:10]))    # GATE..TGT along the waypoints
    coast_gate = sum(bearing_dist(a["ll"], b["ll"])[1] for a, b in zip(en[2:4], en[3:5]))
    run_min = (coast_gate + canyon) / 470 * 60
    st = sites(c)
    sam = [s for s in st if s[1] == "sam"]
    valley = [s for s in st if s[1] in ("valley", "guard")]
    south_kind = re.search(r'SOUTH_KIND = "([^"]+)"', c).group(1)
    north_kind = re.search(r'NORTH_KIND = "([^"]+)"', c).group(1)
    times = {"PUSH": "~" + hms(tot - (run_min + 1) * 60) + " push", "GATE": "~" + hms(tot - canyon / 460 * 3600),
             "TGT": f"**{hms(tot)}**"}
    return dict(
        miz=Path(miz).name, hard=hard, start=hm(n["START"]), start_z=hms(n["START"] - ZULU),
        tot=hms(tot), tot_hm=hm(tot), tot_z=hms(tot - ZULU), tot_min=round((tot - n["START"]) / 60),
        window=int(n["WINDOW"]), win_on=hms(tot - n["WINDOW"]), win_off=hms(tot + n["WINDOW"]),
        hammer=hms(n["HAMMER"]), hammer_lead=round((tot - n["HAMMER"]) / 60), repair_min=round(n["REPAIR"] / 60),
        south_up=hms(n["HAMMER"] + n["REPAIR"]), sam_up=hms(tot + n["SAM_UP"]), sam_up_s=int(n["SAM_UP"]),
        react=int(n["REACT"]), kill_window=int(n["KILL_WINDOW"]), floor_ft=int(n["FLOOR_FT"]), grace=int(n["GRACE"]),
        warn="WARN = true" in c, hit_r=int(n["BREACH_R"]), det_nm=f"{n['DET_R'] / NM:.0f}", pop_nm=f"{n['POP_R'] / NM:.1f}",
        alert_react=int(n["ALERT_REACT"]), team_km=f"{n['TEAM_R_MIN'] / 1000:.1f}–{n['TEAM_R_MAX'] / 1000:.0f}",
        south_kind=south_kind, north_kind=north_kind,
        sam_names=[s[0].replace("Climb-out ", "") for s in sam], valley=[(s[0], s[5]) for s in valley],
        gun2="ZSU-23-4" if any("ZSU" in t for s in valley for t in s[5]) else "ZU-23",
        tgt_ddm=ddm(*tgt), tgt_mgrs=f"{m[:3]} {m[3:5]} {m[5:10]} {m[10:]}",
        gate_tgt_nm=f"{gate_tgt:.0f}", canyon_nm=f"{canyon:.0f}", coast_gate_nm=f"{coast_gate:.0f}", run_min=f"{run_min:.0f}",
        pts=dict(breach=int(n["PTS_BREACH"]), kill=int(n["PTS_KILL"]), ontime=int(n["PTS_ONTIME"]),
                 unseen=int(n["PTS_UNSEEN"]), survival=int(n["PTS_SURVIVAL"])),
        route=route(d, "Enfield", times), strike_load=loadout(d, "Enfield"),
    )


def escape(miz, work):
    d = parse_miz(miz)
    c = d["cfg"]
    start, disc, react = cfg_num(c, "START"), cfg_num(c, "DISCOVER"), cfg_num(c, "ALERT_REACT")
    en = d["groups"]["Enfield"]
    fuel_lb = None
    return dict(miz=Path(miz).name, start=hm(start), start_z=hms(start - ZULU), discover=hms(start + disc),
                discover_min=round(disc / 60), react=int(react), notice=int(cfg_num(c, "TAKEOFF_NOTICE")),
                route=route(d, "Enfield"), load=loadout(d, "Enfield"))
