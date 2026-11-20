"""Build Operation_Deep_Cut.miz and Operation_Deep_Cut_Hard.miz (Caucasus; F/A-18C strike; 1-2 players).

python3 build_deep_cut.py            -> both variants
python3 build_deep_cut.py hard       -> one

A low-level strike up the Enguri gorge on a tunnel portal near Khaishi. The target and every Red ground site are
spawned by the mission script at start, placed on the real gorge floor (or high ground for the SAMs) with DCS's
own terrain, starting from the planned points below. The planned points follow the river from published
coordinates for Jvari and the Enguri dam; points above the dam are estimates and may be a kilometre or two off.
"""
import datetime
import sys

from dcs import task, mapping
from dcs.planes import FA_18C_hornet as HN, MiG_21Bis, MiG_29S, Su_27
from dcs.ships import Stennis, CVN_71
from dcs.unit import Skill

from missionbuilder.builder import Builder, W, FT, KTS
from missionbuilder.paths import read_lua
from missionbuilder.red_arms import arm

START = datetime.datetime(2027, 1, 14, 10, 0, 0)     # winter, mid-morning (Caucasus local = Z+4)
TOT_OFFSET = 40 * 60                                 # cold start, ~60 nm to PUSH, the run in

VARIANTS = {
    "standard": dict(file="Operation_Deep_Cut.miz", title="Operation Deep Cut", tag="",
                     window=45, repair=600, sam_up=90, react=45, kill_window=90, floor_ft=500, grace=4, warn=True,
                     hit_r=15, south=(MiG_29S, Skill.Average, "two MiG-29s"), north=(MiG_21Bis, Skill.Average, "two MiG-21s"),
                     sam_w=[("Kub 1S91 str", 0, 0), ("Kub 2P25 ln", 140, 60), ("Kub 2P25 ln", -120, 90)],
                     sam_w_label="SA-6", sam_e=[("Osa 9A33 ln", 0, 0)], sam_e_label="SA-8",
                     gun2="ZU-23 Emplacement"),
    "hard": dict(file="Operation_Deep_Cut_Hard.miz", title="Operation Deep Cut (Hard)", tag=" (HARD)",
                 window=30, repair=420, sam_up=60, react=30, kill_window=60, floor_ft=300, grace=2, warn=False,
                 hit_r=12, south=(MiG_29S, Skill.Good, "two MiG-29s"), north=(Su_27, Skill.Good, "two Su-27s"),
                 sam_w=[("SA-11 Buk SR 9S18M1", 0, 0), ("SA-11 Buk CC 9S470M1", 90, -70),
                        ("SA-11 Buk LN 9A310M1", 160, 60), ("SA-11 Buk LN 9A310M1", -140, 100)],
                 sam_w_label="SA-11", sam_e=[("Tor 9A331", 0, 0), ("Osa 9A33 ln", 150, -80)], sam_e_label="SA-15 and SA-8",
                 gun2="ZSU-23-4 Shilka"),
}

# planned geography (lat, lon)
FEET_DRY = (42.391, 41.559)        # Enguri mouth
RIVER = (42.560, 41.880)           # the lower Enguri, north-west of Zugdidi
GATE = (42.7189, 42.0458)          # Jvari, where the river leaves the gorge (published)
DAM = (42.7592, 42.0319)           # Enguri dam (published)
RESERVOIR = (42.800, 42.052)       # estimates from here up
NARROWS = (42.850, 42.090)
BEND = (42.900, 42.140)
TGT = (42.952, 42.195)             # planned portal, near Khaishi
PUSH = (42.320, 41.250)            # over the sea, short of the coast
CVN_START = (42.150, 39.900)       # ~75 nm off the coast, steaming west: ~110 nm out by recovery (stand-off from coastal missiles)
CAP = (42.300, 41.150)             # CHEVY's station, over the water off the Enguri mouth
TANKER = (42.300, 40.950)
NORTH_SPAWN = (43.150, 42.450)     # over the main range


def lua_pt(p):
    return f"x = {p.x:.1f}, z = {p.y:.1f}"


SC_SHIP = CVN_71                    # the Supercarrier versions: CVN-71 Theodore Roosevelt (players need the module)
HOLD_FT = 3000                      # the hold at PUSH: left racetrack, inbound on the course to FEET DRY
HOLD_LEG_NM = 5


def sc_file(f, sc):
    return f.replace(".miz", "_SC.miz") if sc else f


def build(key, sc=False):
    v = VARIANTS[key]
    title = v["title"] + (" (Supercarrier)" if sc else "")
    b = Builder(title, START, sc_file(v["file"], sc))
    P = b.P
    b.m.weather.season_temperature = -4
    s0 = b.start_s
    tot = s0 + TOT_OFFSET
    hammer = tot - 180
    pts = {k: P(*ll) for k, ll in dict(FEET_DRY=FEET_DRY, RIVER=RIVER, GATE=GATE, DAM=DAM, RESERVOIR=RESERVOIR,
                                       NARROWS=NARROWS, BEND=BEND, TGT=TGT, PUSH=PUSH, CAP=CAP,
                                       TANKER=TANKER).items()}
    tgt = pts["TGT"]
    det_r = round(tgt.distance_to_point(pts["GATE"]) + 2000, -2)
    pop_r = 7000

    b.carrier(start=CVN_START, recovery_min=65, ship=SC_SHIP if sc else Stennis)
    cvn = b.cvn_start

    # ------------------------------------------------------------ Blue
    strike = {1: W["9X_1"], 2: W["HARM_2"], 3: W["GBU12_3"], 4: W["LITENING"], 5: W["TANK_5"],
              6: W["120_6"], 7: W["GBU12_7"], 8: W["HARM_8"], 9: W["9X_9"]}

    def strike_route(hold_ft=HOLD_FT):
        return [("DEPART", cvn.point_from_heading(45, 18_000), 5000, 350),
                ("PUSH", pts["PUSH"], hold_ft, 420),
                ("FEET DRY", pts["FEET_DRY"], 500, 480, "RADIO"),
                ("RIVER", pts["RIVER"], 500, 480, "RADIO"),
                ("GATE", pts["GATE"], 300, 480, "RADIO"),
                ("DAM", pts["DAM"], 300, 450, "RADIO"),
                ("RESERVOIR", pts["RESERVOIR"], 300, 450, "RADIO"),
                ("NARROWS", pts["NARROWS"], 300, 450, "RADIO"),
                ("BEND", pts["BEND"], 300, 450, "RADIO"),
                ("TGT", tgt, 300, 480, "RADIO"),
                ("GATE OUT", pts["GATE"], 500, 520, "RADIO"),
                ("FEET WET", pts["FEET_DRY"], 1000, 480),
                ("TANKER", pts["TANKER"], 15000, 300)]

    # every flyable slot is Client: Player slots can't be taken in multiplayer, and Client slots are
    # selectable in single player too
    b.flight("Enfield", HN, [strike, strike], strike_route(), 1, [Skill.Client, Skill.Client],
             eta={"TGT": TOT_OFFSET})
    # one two-ship: Enfield 1-2 trails its lead by 30 s on the same line to stay out of the fragments
    # PUSH time: TOT less the planned time from PUSH to TGT at each leg's planned speed; MAGIC calls it
    legs = strike_route()
    i0, i1 = [l[0] for l in legs].index("PUSH"), [l[0] for l in legs].index("TGT")
    run_s = sum(legs[i][1].distance_to_point(legs[i - 1][1]) / (legs[i][3] * 1852 / 3600)  # knots -> m/s
                for i in range(i0 + 1, i1 + 1))
    push_t = round(tot - run_s)
    b.tanker(pts["TANKER"])
    b.awacs()
    b.cap(pts["CAP"], commit_point=pts["FEET_DRY"])      # CHEVY: offshore, committed by MAGIC on the egress fighters

    # ------------------------------------------------------------ Red fighters (late-activated; the script launches them)
    def fighters(name, kind, at, alt_m, goal, radius):
        ptype, skill, _ = kind
        g = b.m.flight_group_inflight(b.rus, name, ptype, at, altitude=alt_m, speed=850, maintask=task.CAP, group_size=2)
        g.late_activation = True
        arm(g)
        g.points[0].tasks = [t for t in g.points[0].tasks if not isinstance(t, task.CAPTaskAction)]
        for i, u in enumerate(g.units, start=1):
            u.name, u.skill = f"{name} {i}", skill
        w = g.add_waypoint(goal, 5000, 900, name="Gorge mouth")
        w.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(goal.x, goal.y), radius=radius,
                                                targets=[task.Targets.All.Air]))
        w.tasks.append(task.OrbitAction(altitude=5000, speed=800, pattern=task.OrbitAction.OrbitPattern.Circle))
        return g

    kutaisi = b.terrain.airports["Kutaisi"].position
    fighters("Red South", v["south"], kutaisi.point_from_heading(300, 6000), 1500, pts["RIVER"], 60_000)
    fighters("Red North", v["north"], P(*NORTH_SPAWN), 5000, pts["GATE"], 50_000)

    # ------------------------------------------------------------ Red ground (spawned by the script)
    def site(name, kind, ll_or_off, r, units, heading=0):
        if kind == "guard":
            x, z = ll_or_off
        else:
            p = P(*ll_or_off)
            x, z = p.x, p.y
        us = ", ".join(f'{{ "{t}", {dx}, {dz} }}' for t, dx, dz in units)
        return f'    {{ name = "{name}", kind = "{kind}", x = {x:.1f}, z = {z:.1f}, r = {r}, heading = {heading}, units = {{ {us} }} }},'

    sites = [
        site("Gorge Guns 1", "valley", (42.870, 42.112), 1500,
             [("ZU-23 Emplacement", 0, 0), ("SA-18 Igla manpad", 35, 25), ("SA-18 Igla comm", 40, 30)], 200),
        site("Gorge Guns 2", "valley", (42.915, 42.155), 1500,
             [(v["gun2"], 0, 0), ("SA-18 Igla manpad", -30, 30), ("SA-18 Igla comm", -35, 35)], 200),
        site("Gorge MANPADS", "valley", (42.937, 42.177), 1200,
             [("SA-18 Igla manpad", 0, 0), ("SA-18 Igla manpad", 60, -40), ("SA-18 Igla comm", 30, -20)], 220),
        site("Portal Guard", "guard", (150, -120), 0,
             [("ZU-23 Emplacement Closed", 0, 0), ("SA-18 Igla manpad", 40, 30), ("SA-18 Igla comm", 45, 35)], 200),
        site(f"Climb-out {v['sam_w_label']}", "sam", (42.965, 42.150), 1200, v["sam_w"], 160),
        site(f"Climb-out {v['sam_e_label']}", "sam", (42.935, 42.240), 1200, v["sam_e"], 250),
    ]
    canyon = [("GATE", "GATE"), ("DAM", "DAM"), ("RESERVOIR", "RESERVOIR"), ("NARROWS", "NARROWS"),
              ("BEND", "BEND"), ("PORTAL", "TGT")]
    canyon_lua = ", ".join(f'{{ name = "{n}", {lua_pt(pts[k])}, r = 1500 }}' for n, k in canyon)

    cfg = f"""T.cfg = {{
  NAME = "OPERATION DEEP CUT{v['tag']}", START = {s0}, TOT = {tot}, WINDOW = {v['window']},
  HAMMER = {hammer}, REPAIR = {v['repair']}, SAM_UP = {v['sam_up']}, REACT = {v['react']}, KILL_WINDOW = {v['kill_window']},
  FLOOR_FT = {v['floor_ft']}, GRACE = {v['grace']}, WARN = {'true' if v['warn'] else 'false'},
  BREACH_R = {v['hit_r']}, KILL_R = {v['hit_r']}, AT_TARGET_R = 400,
  TGT = {{ {lua_pt(tgt)} }}, TGT_R = 2500, DET_R = {det_r:.0f}, POP_R = {pop_r},
  SITES = {{
{chr(10).join(sites)}
  }},
  CANYON = {{ {canyon_lua} }},
  SOUTH_GROUP = "Red South", NORTH_GROUP = "Red North", SOUTH_KIND = "{v['south'][2]}", NORTH_KIND = "{v['north'][2]}",
  SOUTH_BASE = "Kutaisi", ALERT_REACT = 90,
  TEAM = "Hatchet", TEAM_R_MIN = 1200, TEAM_R_MAX = 3000, LASER_CODE = 1688,
  JETS = {{ "Enfield 1-1", "Enfield 1-2" }},
  NEXT_ESCAPE = "{sc_file('Operation_Deep_Cut_Escape.miz', sc)}", RESCUE_FLAG = "91",
  CARRIER = "{b.cvn_name}", PUSH_T = {push_t},
  HOLD_FT = {HOLD_FT}, HOLD_LEG_NM = {HOLD_LEG_NM},
  PTS_BREACH = 15, PTS_KILL = 25, PTS_ONTIME = 12, PTS_UNSEEN = 8, PTS_SURVIVAL = 40,
  OUTCOME_FLAG = "90", SCORE_FLAG = "92",
}}
"""
    b.add_cap_scripts("the coast")
    b.add_script(read_lua("common.lua"))
    b.add_script(read_lua("deep_cut.lua"), cfg, keep_copy=f"deep_cut_{key}{'_sc' if sc else ''}_built.lua")
    # Briefing text comes from briefings/deep_cut.md: build.py renders it and writes it into the .miz.
    b.save(title, "See the mission briefing.", "See the mission briefing.")
    return b


if __name__ == "__main__":
    for k in (sys.argv[1:] or ["standard", "hard"]):
        for sc in (False, True):
            build(k, sc)
