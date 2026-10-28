"""Build the Long Road missions (Narrow Gate success branch, interdiction):

  Operation_Long_Road.miz           Narrow Gate on time: CAG assigns COLT (AI HARM pair) to your package
  Operation_Long_Road_Own_SEAD.miz  Narrow Gate destroyed the depot but late: no COLT, your section does its own SEAD
"""
import datetime
from dcs import task, mapping
from missionbuilder.red_arms import arm
from dcs.planes import MiG_29A, FA_18C_hornet as HN
from dcs.unit import Skill
from dcs.vehicles import AirDefence, Armor, Unarmed
from missionbuilder.builder import Builder, W, FT, KTS, hms, hm, ZULU_OFFSET
from missionbuilder.paths import read_lua

START = datetime.datetime(2026, 10, 26, 11, 30, 0)
RESTART_MIN = 40          # column moves at start + 40:00
MIG_MIN = 20              # Red CAP launches at start + 20:00
SUPPRESS_S = 90

VARIANTS = {"colt": dict(file="Operation_Long_Road.miz", colt=True),
            "own": dict(file="Operation_Long_Road_Own_SEAD.miz", colt=False)}


def build(key, v):
    b = Builder("Operation Long Road", START, v["file"])
    P = b.P
    start_s = b.start_s
    RESTART = start_s + RESTART_MIN * 60
    MIG_TIME = start_s + MIG_MIN * 60

    # ------------------------------------------------------------------ geography
    COL = P(42.788, 41.310)                     # column centre, coast road ~1.5 km inland
    COL_HDG = 120                               # facing south-east, the way it was going
    SA6 = P(42.814, 41.345)                     # brigade SA-6, inland of the column
    TURN = P(42.803, 41.362)
    COVER = P(42.826, 41.398)                   # wooded hills inland: vehicles reaching here are gone
    HARM_PT = SA6.point_from_heading(232, 20 * 1852)   # Magnum point, over the water ~20 nm from the radar
    IP = COL.point_from_heading(235, 12 * 1852)
    EGRESS = COL.point_from_heading(250, 20 * 1852)
    TANKER = P(42.420, 40.860)
    MIG_SPAWN = P(43.10, 40.62)

    b.carrier(recovery_min=55)
    cvn = b.cvn_start

    # ------------------------------------------------------------------ players
    # lead: SEAD/DEAD plus bombs (so a single player can do the whole job)
    lead = {1: W["9X_1"], 2: W["HARM_2"], 3: W["GBU12x2_3"], 4: W["LITENING"], 5: W["TANK_5"],
            6: W["120_6"], 7: W["MK20x2_7"], 8: W["HARM_8"], 9: W["9X_9"]}
    if v["colt"]:   # wing: the striker
        wing = {1: W["9X_1"], 2: W["MK20_2"], 3: W["GBU12x2_3"], 4: W["LITENING"], 5: W["TANK_5"],
                6: W["120_6"], 7: W["MK20x2_7"], 8: W["MK20_8"], 9: W["9X_9"]}
    else:           # no COLT: both jets carry HARMs
        wing = dict(lead)
    route = [("DEPART", cvn.point_from_heading(45, 18_000), 5000, 350),
             ("MAGNUM", HARM_PT, 22000, 420),
             ("IP", IP, 20000, 420),
             ("TGT", COL, 20000, 420),
             ("EGRESS", EGRESS, 20000, 420),
             ("TANKER", TANKER, 15000, 300)]
    b.enfield([lead, wing], route)

    b.tanker(TANKER)
    b.awacs()
    b.cap(P(42.300, 40.850), commit_point=COL.point_from_heading(240, 8 * 1852))
    b.drone(COL.point_from_heading(30, 2500))

    if v["colt"]:
        # COLT: AI SEAD pair the CAG has assigned to your package. Holds outside SA-6 reach until you push it (flag 53).
        COLT_HOLD = HARM_PT.point_from_heading(250, 6 * 1852)
        colt = b.m.flight_group_inflight(b.usa, "Colt", HN, COLT_HOLD.point_from_heading(250, 6000), altitude=22000 * FT,
                                           speed=420 * KTS, maintask=task.SEAD, group_size=2)
        colt.points[0].tasks = [t for t in colt.points[0].tasks if not isinstance(t, task.SEADTaskAction)]
        w_lo = {1: W["9X_1"], 2: W["HARM_2"], 3: W["HARM_3"], 5: W["TANK_5"], 6: W["120_6"], 7: W["HARM_7"], 8: W["HARM_8"], 9: W["9X_9"]}
        for i, u in enumerate(colt.units, start=1):
            u.name = f"Colt 1-{i}"
            u.skill = Skill.Excellent
            u.callsign_dict = {1: 4, 2: 1, 3: i, "name": f"Colt1{i}"}     # DCS callsign COLT 1-x
            u.pylons.clear()
            for st, store in w_lo.items():
                u.load_pylon(store, st)
        wh = colt.add_waypoint(COLT_HOLD, 22000 * FT, 420 * KTS, name="COLT HOLD")
        w_hold = task.ControlledTask(task.OrbitAction(altitude=22000 * FT, speed=420 * KTS, pattern=task.OrbitAction.OrbitPattern.Circle))
        w_hold.stop_if_user_flag(53, True)
        wh.tasks.append(w_hold)
        wp_push = colt.add_waypoint(HARM_PT, 22000 * FT, 450 * KTS, name="COLT MAGNUM")
        wp_push.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(SA6.x, SA6.y), radius=15_000,
                                                      targets=[task.Targets.All.GroundUnits.AirDefence]))
        wp_push.tasks.append(task.OrbitAction(altitude=22000 * FT, speed=420 * KTS, pattern=task.OrbitAction.OrbitPattern.Circle))


    # ------------------------------------------------------------------ red: the stalled column (10 vehicles nose to tail)
    types = [Armor.T_72B, Armor.BMP_2, Unarmed.ATZ_10, Armor.BMP_2, Unarmed.ATZ_10,
             Unarmed.Ural_375, Armor.BMP_2, Unarmed.ATZ_10, Armor.T_72B, Unarmed.Ural_375]
    names = ["T-72 1", "BMP 1", "Fuel truck 1", "BMP 2", "Fuel truck 2", "Ammo truck 1", "BMP 3", "Fuel truck 3", "T-72 2", "Ammo truck 2"]
    units = []
    for i, (n, t) in enumerate(zip(names, types)):
        along = (4.5 - i) * 60                  # head of column to the south-east
        units.append((f"Column {n}", t, COL.point_from_heading(COL_HDG, along) if along >= 0 else COL.point_from_heading(COL_HDG + 180, -along)))
    column = b.vgroup(b.rus, "Column", units, heading=COL_HDG)
    column.points[0].tasks.append(task.OptROE(task.OptROE.Values.ReturnFire))

    ad = b.vgroup(b.rus, "Column AD", [
        ("Column SA-8", AirDefence.Osa_9A33_ln, COL.point_from_heading(COL_HDG + 70, 250)),
        ("Column ZSU 1", AirDefence.ZSU_23_4_Shilka, COL.point_from_heading(COL_HDG, 400)),
        ("Column ZSU 2", AirDefence.ZSU_23_4_Shilka, COL.point_from_heading(COL_HDG + 180, 400)),
    ], heading=COL_HDG)

    sam = b.vgroup(b.rus, "Brigade SA-6", [("SA-6 Straight Flush", AirDefence.Kub_1S91_str, SA6)] +
                   [(f"SA-6 Launcher {i}", AirDefence.Kub_2P25_ln, b.off(SA6, dx, dy))
                    for i, (dx, dy) in enumerate([(250, -150), (-200, -250), (-300, 250), (300, 300)], start=1)],
                   heading=230)

    migs = b.m.flight_group_inflight(b.rus, "Red CAP", MiG_29A, MIG_SPAWN, altitude=6000, speed=850,
                                     maintask=task.CAP, group_size=2)
    migs.late_activation = True
    arm(migs)
    for u in migs.units:
        u.skill = Skill.Average
    w1 = migs.add_waypoint(COL, 6000, 850, name="Column")
    w1.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(COL.x, COL.y), radius=40_000,
                                             targets=[task.Targets.All.Air]))
    w1.tasks.append(task.OrbitAction(altitude=6000, speed=750, pattern=task.OrbitAction.OrbitPattern.Circle))

    # ------------------------------------------------------------------ scripts
    cfg = f"""T.cfg = {{
      START = {start_s}, RESTART = {RESTART},
      COLUMN_GROUP = "Column", COLUMN_AD = "Column AD", SAM_GROUP = "Brigade SA-6", SAM_RADAR = "SA-6 Straight Flush",
      MIG_GROUP = "Red CAP", MIG_TIME = {MIG_TIME},
      CAP_GROUP = "Chevy", CAP_FLAG = "51",
      JTAC_UNIT = "Pontiac", LASER_CODE = 1688,
      ROUTE = {{ {{ x = {TURN.x:.1f}, z = {TURN.y:.1f} }} }},
      COVER = {{ x = {COVER.x:.1f}, z = {COVER.y:.1f} }}, COVER_R = 1500,
      SUPPRESS_S = {SUPPRESS_S}, HARM_KILL_R = 150,
      JETS = {{ "Enfield 1-1", "Enfield 1-2" }},
      COLT_PREFIX = "Colt", COLT_FLAG = "53", COLT = {"true" if v["colt"] else "false"},
      NEXT_RESCUE = "Operation_Sandy_Lift_Long_Road.miz",
    }}
    """
    b.add_cap_scripts("the column", fleet_only=False)
    b.add_script(read_lua("common.lua"))
    b.add_script(read_lua("long_road.lua"), cfg, keep_copy=f"long_road_{key}_built.lua")

    # ------------------------------------------------------------------ briefing
    sa6_brg, sa6_nm = b.brg_nm(COL, SA6)
    cov_brg, cov_nm = b.brg_nm(COL, COVER)
    T_RESTART = hms(RESTART)
    # Briefing text comes from briefings/*.md: build.py renders it and writes it into the .miz.
    desc = tasktext = "See the mission briefing."
    b.save("Operation Long Road", desc, tasktext)
    print("restart", T_RESTART, "SA-6", f"{sa6_nm:.1f} nm brg {sa6_brg:.0f}", "cover", f"{cov_nm:.1f} nm")


for key, v in VARIANTS.items():
    build(key, v)
