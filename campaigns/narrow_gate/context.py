"""Briefing contexts: the numbers each Markdown briefing needs, read from the built .miz (and the map step's
timing.json for Narrow Gate), so the prose can never disagree with the mission."""
import json
import re
from pathlib import Path

import mgrs as mgrslib

import mission_times as MT
from missionbuilder.mapkit import (parse_miz, cfg_num, cfg_pt, bearing_dist, ddm, hms, hm, compass, store_name, NM)

ZULU = 4 * 3600


def _z(s):
    return hms(s - ZULU)


def _route(d, plan_times=None):
    """Route card rows from the Enfield flight plan."""
    en = d["groups"]["Enfield"]["route"]
    rows = []
    for i, p in enumerate(en):
        name = "CVN-74 (deck)" if i == 0 else ("MOTHER (land)" if p["name"] == "MOTHER" else p["name"])
        alt = "deck" if i == 0 or p["name"] == "MOTHER" else f"{round(p['alt'] / 0.3048, -2):,.0f} ft"
        leg = crs = ""
        if i:
            b, dist = bearing_dist(en[i - 1]["ll"], p["ll"])
            leg, crs = f"{dist:.1f} nm", f"{b:03.0f}°"
        rows.append(dict(wp=i, name=name, coords=ddm(*p["ll"]), alt=alt, leg=leg, course=crs,
                         time=(plan_times or {}).get(p["name"] or "START", "")))
    return rows


def _loadout(d):
    """Per-jet store list by station, and whether both jets match."""
    jets = d["groups"]["Enfield"]["units"]
    rows = []
    for j, u in enumerate(jets, start=1):
        rows.append(dict(jet=f"1-{j}", stations=[store_name(u["pylons"][s]) if u.get("pylons", {}).get(s) else "—"
                                                for s in range(1, 10)]))
    same = len(rows) == 2 and rows[0]["stations"] == rows[1]["stations"]
    return rows, same


def _common(d, miz):
    load, same = _loadout(d)
    return dict(miz=Path(miz).name, start=hm(d["start"]), start_hms=hms(d["start"]), start_z=_z(d["start"]),
                route=_route(d), loadout=load, loadout_same=same)


# ------------------------------------------------------------------ Narrow Gate
def narrow_gate(miz, work):
    d = parse_miz(miz)
    tm = json.loads((Path(work) / "timing.json").read_text())
    g = d["groups"]
    wp = {(w["name"] or "START"): w for w in g["Enfield"]["route"]}
    tgt = wp["TGT"]["ll"]
    m = mgrslib.MGRS().toMGRS(tgt[0], tgt[1], MGRSPrecision=5)
    tot = MT.TOT_S
    eg = bearing_dist(tgt, wp["EGRESS"]["ll"])[1]
    tk = bearing_dist(wp["EGRESS"]["ll"], wp["TANKER"]["ll"])[1]
    plan = {"START": f"{MT.T_START} cold", "PUSH": hms(tm["t_push"]) + " depart", "IP": hms(tm["t_ip"]),
            "TGT": f"**{MT.T_TOT} TOT**", "EGRESS": "~" + hms(tot + eg / 420 * 3600),
            "TANKER": "~" + hms(tot + (eg + tk) / 420 * 3600), "MOTHER": f"~{MT.T_REC_A}–{MT.T_REC_B}"}
    cfg = d["cfg"]
    ford = {w["name"]: w["ll"] for w in g["Ford"]["route"]}
    sam = cfg_pt(cfg, "SAM_POINT")
    ctx = _common(d, miz)
    ctx.update(
        route=_route(d, plan),
        tot=MT.T_TOT, tot_hm=MT.T_TOT_HM, tot_z=MT.T_TOT_Z, tot_offset_min=MT.TOT_OFFSET // 60,
        win_on=MT.T_WIN_ON, win_off=MT.T_WIN_OFF, win_on_hm=MT.T_WIN_ON_HM, win_off_hm=MT.T_WIN_OFF_HM,
        window_s=MT.WINDOW, jam_on=MT.T_SUP_ON, jam_off=MT.T_SUP_OFF, in_earliest=MT.T_IN_EARLIEST,
        push_time=hms(tm["t_push"]), ip_time=hms(tm["t_ip"]),
        ip_hdg=f"{tm['brg_in']:03.0f}", egress_hdg=f"{tm['brg_out']:03.0f}",
        ip_dist=f"{bearing_dist(wp['IP']['ll'], tgt)[1]:.1f}",
        tgt_mgrs=f"{m[:3]} {m[3:5]} {m[5:10]} {m[10:]}", tgt_ddm=ddm(*tgt),
        rec_hm=MT.T_REC_HM, rec_a=MT.T_REC_A, rec_b=MT.T_REC_B,
        jam_r_nm=f"{cfg_num(cfg, 'JAM_R') / NM:.0f}", ford_cpa_nm=f"{bearing_dist(sam, ford['CLOSEST'])[1]:.0f}",
        ford_inbound=hm(cfg_num(cfg, "FORD_SPAWN")),
        patrol_pct=20, alert_min=round((300 + 420) / 60),
    )
    return ctx


# ------------------------------------------------------------------ Long Road (both variants)
def long_road(miz, work):
    d = parse_miz(miz)
    c = d["cfg"]
    g = d["groups"]
    restart, mig, sup = cfg_num(c, "RESTART"), cfg_num(c, "MIG_TIME"), int(cfg_num(c, "SUPPRESS_S"))
    col = g["Column"]["units"]
    col_c = [sum(u["ll"][0] for u in col) / len(col), sum(u["ll"][1] for u in col) / len(col)]
    sa6 = [u for u in g["Brigade SA-6"]["units"] if "1S91" in u["type"]][0]["ll"]
    sb, sd = bearing_dist(col_c, sa6)
    cb, cd = bearing_dist(col_c, cfg_pt(c, "COVER"))
    ctx = _common(d, miz)
    ctx.update(
        colt="COLT = true" in c, restart=hm(restart), restart_hms=hms(restart), restart_z=_z(restart),
        restart_min=round((restart - d["start"]) / 60), mounting=hm(restart - 600), last_cover=hm(restart + 17 * 60),
        mig=hm(mig), suppress_s=sup, sa6_nm=f"{sd:.1f}", sa6_dir=compass(sb), cover_nm=f"{cd:.1f}",
        cover_dir=compass(cb), harms=sum(1 for u in g["Enfield"]["units"] for v in u.get("pylons", {}).values() if "AGM_88" in v
                                         or "B06DD79A" in v or store_name(v).startswith("AGM-88")),
    )
    return ctx


# ------------------------------------------------------------------ Stone Ford (both variants)
def stone_ford(miz, work):
    d = parse_miz(miz)
    c = d["cfg"]
    g = d["groups"]
    waves = []
    for name, t in re.findall(r'group = "(Wave \d+)", time = (\d+)', c):
        units = g[name]["units"]
        kinds = {}
        for u in units:
            k = {"BMP-2": "BMP-2", "T-72B": "T-72", "BTR-80": "BTR-80", "ZSU-23-4 Shilka": "ZSU-23-4",
                 "Osa 9A33 ln": "SA-8", "Strela-1 9P31": "SA-9", "Strela-10M3": "SA-13"}.get(u["type"], u["type"])
            kinds[k] = kinds.get(k, 0) + 1
        waves.append(dict(name=name, time=hm(float(t)), n=len(units),
                          mix=", ".join(f"{n}× {k}" if n > 1 else k for k, n in kinds.items())))
    ctx = _common(d, miz)
    mig_t = cfg_num(c, "MIG_TIME")
    ctx.update(
        hard='CAP_MODE = "fleet"' in c, waves=waves, n_waves=len(waves), n_veh=sum(w["n"] for w in waves),
        lost_at=int(cfg_num(c, "LOST_AT")), held_max=int(cfg_num(c, "HELD_MAX")), bridge_r=int(cfg_num(c, "BRIDGE_R")),
        contact_km=cfg_num(c, "CONTACT_R") / 1000, danger_r=int(cfg_num(c, "DANGER_R")), frat_r=int(cfg_num(c, "FRAT_R")),
        vis_nm=int(cfg_num(c, "VIS_NM")), mig=hm(mig_t), mig_type="MiG-29s" if g["Red CAP"]["units"][0]["type"].startswith("MiG-29") else "MiG-21s",
        mig_before_first=mig_t < float(re.findall(r'time = (\d+)', c)[0]),
    )
    return ctx


# ------------------------------------------------------------------ Sandy Lift (three variants)
def sandy_lift(miz, work):
    d = parse_miz(miz)
    c = d["cfg"]
    g = d["groups"]
    lz = cfg_pt(c, "LZ")
    hold = cfg_pt(c, "HOLD")
    search_t, mig = cfg_num(c, "SEARCH_TIME"), cfg_num(c, "MIG_TIME")
    sp = g["Search Party"]["units"][0]["ll"]
    _, dist_nm = bearing_dist(sp, lz)
    capture = search_t + (dist_nm * NM - cfg_num(c, "CAPTURE_R")) / cfg_num(c, "SEARCH_SPEED")
    hold_brg, hold_nm = bearing_dist(lz, hold)
    transit_min = hold_nm * NM / cfg_num(c, "HELO_MS") / 60
    stem = Path(miz).stem
    variant = {"Operation_Sandy_Lift": "narrow_gate", "Operation_Sandy_Lift_Long_Road": "long_road",
               "Operation_Sandy_Lift_Inguri": "inguri"}[stem]
    ctx = _common(d, miz)
    ctx.update(
        variant=variant, search=hm(search_t), capture=hm(capture), search_km=f"{dist_nm * NM / 1000:.1f}",
        mig=hm(mig), mig_kind=re.search(r'MIG_KIND = "([^"]+)"', c).group(1),
        hold_nm=f"{hold_nm:.0f}", hold_dir=compass((hold_brg + 0) % 360), transit_min=f"{transit_min:.0f}",
        latest_call=hm(capture - (transit_min + 1) * 60), board_s=int(cfg_num(c, "BOARD_S")),
        capture_r=int(cfg_num(c, "CAPTURE_R")), threat_km=int(cfg_num(c, "THREAT_R") / 1000),
    )
    return ctx
