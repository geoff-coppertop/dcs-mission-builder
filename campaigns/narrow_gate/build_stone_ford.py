"""Build Operation_Stone_Ford.miz (partial branch) and Operation_Stone_Ford_Hard.miz (failure branch).

python3 build_stone_ford.py          -> both variants
"""
import datetime
import sys
from dcs import task, mapping
from dcs.point import PointAction
from missionbuilder.red_arms import arm
from dcs.planes import MiG_21Bis, MiG_29A
from dcs.unit import Skill
from dcs.vehicles import AirDefence, Armor, Infantry
from missionbuilder.builder import Builder, W, FT, KTS, hms, hm, ZULU_OFFSET
from missionbuilder.paths import read_lua

START = datetime.datetime(2026, 10, 26, 10, 30, 0)
LOST_AT, HELD_MAX = 3, 1

VARIANTS = {
    "partial": dict(
        file="Operation_Stone_Ford.miz", title="Operation Stone Ford", tag="",
        cap_mode="commit",
        waves=[  # (minutes after start, bearing from bridge, km out, [types])
            (20, 325, 9.5, [Armor.BMP_2, Armor.BMP_2, Armor.BMP_2, Armor.T_72B]),
            (26, 335, 10.5, [Armor.T_72B, Armor.T_72B, Armor.BMP_2, Armor.BMP_2, AirDefence.ZSU_23_4_Shilka]),
            (32, 315, 8.5, [Armor.BMP_2, Armor.BMP_2, Armor.BTR_80, AirDefence.Strela_1_9P31]),
        ],
        mig=(MiG_21Bis, 30, "two MiG-21s will come down from Gudauta about half an hour in, and MAGIC commits CHEVY when they "
                            "launch. A ZSU-23-4 and an SA-9 ride with the second and third waves."),
    ),
    "hard": dict(
        file="Operation_Stone_Ford_Hard.miz", title="Operation Stone Ford (Hard)", tag=" (HARD)",
        cap_mode="fleet",
        waves=[
            (18, 325, 9.5, [Armor.BMP_2, Armor.BMP_2, Armor.BMP_2, Armor.T_72B, Armor.T_72B]),
            (23, 335, 10.5, [Armor.T_72B, Armor.T_72B, Armor.T_72B, Armor.BMP_2, Armor.BMP_2, AirDefence.ZSU_23_4_Shilka]),
            (28, 315, 8.5, [Armor.BMP_2, Armor.BMP_2, Armor.BMP_2, Armor.BTR_80, AirDefence.Osa_9A33_ln]),
            (33, 325, 11.0, [Armor.T_72B, Armor.T_72B, Armor.BMP_2, Armor.BMP_2, AirDefence.Strela_10M3]),
        ],
        mig=(MiG_29A, 12, "two MiG-29s are expected over the Inguri early; an SA-8, an SA-13 and a ZSU-23-4 move with the waves."),
    ),
}


def build(key):
    v = VARIANTS[key]
    b = Builder(v["title"], START, v["file"])
    P = b.P
    s0 = b.start_s
    BRIDGE = P(42.4253, 41.6283)                     # Ganmukhuri, north bank of the Inguri
    JTAC = BRIDGE.point_from_heading(330, 700)        # Axeman, forward edge of the village
    IP = BRIDGE.point_from_heading(255, 22_000)       # over the water
    EGRESS = BRIDGE.point_from_heading(270, 30_000)
    TANKER = P(42.30, 40.95)
    MID = BRIDGE.point_from_heading(325, 4500)

    b.carrier(recovery_min=55)
    cvn = b.cvn_start
    lo = {1: W["9X_1"], 2: W["MAV_2"], 3: W["GBU12x2_3"], 4: W["LITENING"], 5: W["TANK_5"],
          6: W["120_6"], 7: W["MK20x2_7"], 8: W["MAV_8"], 9: W["9X_9"]}
    b.enfield([lo, lo], [("DEPART", cvn.point_from_heading(45, 18_000), 5000, 350),
                         ("IP", IP, 18000, 400),
                         ("TGT", MID, 18000, 400),
                         ("EGRESS", EGRESS, 18000, 400),
                         ("TANKER", TANKER, 15000, 300)])
    b.tanker(TANKER)
    b.awacs()
    if v["cap_mode"] == "fleet":   # fleet defence: station over the boat, engages only threats within ~22 nm of it
        b.cap(P(42.25, 40.80), commit_point=P(42.25, 40.80))
    else:
        b.cap(P(42.30, 40.85), commit_point=BRIDGE.point_from_heading(300, 15_000))

    # Blue: light infantry holding the village and the bridge approaches (immortal, return fire only)
    blue_pts = [BRIDGE.point_from_heading(br, d) for br, d in
                [(320, 500), (340, 450), (300, 550), (0, 400), (280, 600), (20, 350), (330, 250), (310, 300)]]
    bg = b.m.vehicle_group(b.usa, "Bridgehead", Infantry.Soldier_M4, blue_pts[0], heading=325, group_size=1)
    for i, pt in enumerate(blue_pts[1:], start=2):
        s = b.m.vehicle(f"Bridgehead {i}", Infantry.Soldier_M249 if i % 3 == 0 else Infantry.Soldier_M4)
        s.position = pt
        s.heading = 325
        bg.add_unit(s)
    wg = b.m.vehicle_group(b.usa, "Axeman", Infantry.Soldier_M4, JTAC, heading=325, group_size=1)
    wg.units[0].name = "Axeman"

    # Red waves: late-activated, drive to the bridge
    waves_cfg = []
    for i, (mins, brg, km, types) in enumerate(v["waves"], start=1):
        start_pt = BRIDGE.point_from_heading(brg, km * 1000)
        heading = (brg + 180) % 360
        units = [(f"Wave {i} {j + 1}", t, start_pt.point_from_heading(brg, j * 70)) for j, t in enumerate(types)]
        g = b.vgroup(b.rus, f"Wave {i}", units, heading=heading)
        g.late_activation = True
        g.points[0].speed = 6
        g.add_waypoint(MID.point_from_heading(brg - 325 + 90, (i - 2) * 400), PointAction.OffRoad, speed=22)
        g.add_waypoint(BRIDGE, PointAction.OffRoad, speed=22)
        waves_cfg.append((f"Wave {i}", s0 + mins * 60))

    mig_type, mig_min, mig_text = v["mig"]
    migs = b.m.flight_group_inflight(b.rus, "Red CAP", mig_type, P(43.10, 40.62), altitude=6000, speed=850,
                                     maintask=task.CAP, group_size=2)
    migs.late_activation = True
    arm(migs)
    for u in migs.units:
        u.skill = Skill.Average
    w1 = migs.add_waypoint(BRIDGE, 6000, 850, name="Inguri")
    w1.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(BRIDGE.x, BRIDGE.y), radius=40_000,
                                             targets=[task.Targets.All.Air]))
    w1.tasks.append(task.OrbitAction(altitude=6000, speed=750, pattern=task.OrbitAction.OrbitPattern.Circle))

    waves_lua = ", ".join(f'{{ group = "{g}", time = {t} }}' for g, t in waves_cfg)
    cfg = f"""T.cfg = {{
  NAME = "OPERATION STONE FORD{v['tag']}", START = {s0},
  WAVES = {{ {waves_lua} }},
  BLUE_GROUP = "Bridgehead", JTAC_UNIT = "Axeman", LASER_CODE = 1688,
  BRIDGE = {{ x = {BRIDGE.x:.1f}, z = {BRIDGE.y:.1f} }}, BRIDGE_R = 800, CONTACT_R = 3000, DANGER_R = 1000, FRAT_R = 150,
  LOST_AT = {LOST_AT}, HELD_MAX = {HELD_MAX},
  FAH_TEXT = "020-070 or 200-250", FAH = {{ {{ 20, 70 }}, {{ 200, 250 }} }},
  IP = {{ x = {IP.x:.1f}, z = {IP.y:.1f} }}, MIG_GROUP = "Red CAP", MIG_TIME = {s0 + mig_min * 60},
  MIG_TEXT = "{mig_text}",
  CAP_GROUP = "Chevy", CAP_FLAG = "51", CAP_MODE = "{v['cap_mode']}", JETS = {{ "Enfield 1-1", "Enfield 1-2" }},
  VIS_NM = 8, NEXT_RESCUE = "Operation_Sandy_Lift_Inguri.miz",
}}
"""
    b.add_cap_scripts("the Inguri", fleet_only=(v["cap_mode"] == "fleet"))
    b.add_script(read_lua("common.lua"))
    b.add_script(read_lua("stone_ford.lua"), cfg, keep_copy=f"stone_ford_{key}_built.lua")

    n_veh = sum(len(w[3]) for w in v["waves"])
    wave_lines = "\n".join(f"Wave {i}: moves {hm(s0 + w[0] * 60)}L, {len(w[3])} vehicles" for i, w in enumerate(v["waves"], start=1))
    # Briefing text comes from briefings/*.md: build.py renders it and writes it into the .miz.
    desc = tasktext = "See the mission briefing."
    b.save(v["title"], desc, tasktext)
    return b


if __name__ == "__main__":
    for k in (sys.argv[1:] or ["partial", "hard"]):
        build(k)
