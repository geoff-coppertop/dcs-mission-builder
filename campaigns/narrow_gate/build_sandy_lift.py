"""Build the Sandy Lift rescue missions: one per campaign mission that can lose a jet.

  Operation_Sandy_Lift.miz            after Narrow Gate: near the Ochamchire depot, 08:45
  Operation_Sandy_Lift_Long_Road.miz  after Long Road: by the coast road east of Ochamchire, 13:30
  Operation_Sandy_Lift_Inguri.miz     after Stone Ford (either): behind Red's line NW of Ganmukhuri, 12:00
"""
import datetime
from dcs import task, mapping
from dcs.helicopters import SH_60B
from missionbuilder.red_arms import arm
from dcs.planes import MiG_21Bis, MiG_29A
from dcs.point import MovingPoint, PointAction, PointProperties
from dcs.unit import Skill
from dcs.vehicles import AirDefence, Armor, Infantry
from missionbuilder.builder import Builder, W, FT, KTS, hms, hm, ZULU_OFFSET
from missionbuilder.paths import read_lua

SEARCH_SPEED = 2.0               # m/s, a search party on foot with its vehicles
VARIANTS = {
    "ochamchire": dict(
        file="Operation_Sandy_Lift.miz", title="Operation Sandy Lift", start=(8, 45), after="Narrow Gate",
        lz=(42.735, 41.466), search=(42.697, 41.482), hold=(42.700, 41.150), search_min=5, mig_min=25, mig=MiG_21Bis,
        ad_group="Depot AAA",
        ad=None,
        where_short="near Ochamchire",
    ),
    "longroad": dict(
        file="Operation_Sandy_Lift_Long_Road.miz", title="Operation Sandy Lift (Long Road)", start=(13, 30), after="Long Road",
        lz=(42.770, 41.335), search=(42.800, 41.362), hold=(42.720, 41.050), search_min=8, mig_min=25, mig=MiG_29A,
        ad_group="Rear Guard",
        ad=[("Rear ZSU-23-4", AirDefence.ZSU_23_4_Shilka, (42.792, 41.322)),
            ("Rear SA-13", AirDefence.Strela_10M3, (42.797, 41.338))],
        where_short="by the coast road east of Ochamchire",
    ),
    "inguri": dict(
        file="Operation_Sandy_Lift_Inguri.miz", title="Operation Sandy Lift (Inguri)", start=(12, 0), after="Stone Ford",
        lz=(42.455, 41.585), search=(42.476, 41.562), hold=(42.400, 41.350), search_min=14, mig_min=25, mig=MiG_21Bis,
        ad_group="Line AAA",
        ad=[("Line ZSU-23-4", AirDefence.ZSU_23_4_Shilka, (42.468, 41.600)),
            ("Line SA-9", AirDefence.Strela_1_9P31, (42.462, 41.572))],
        where_short="behind Red's line north-west of Ganmukhuri",
    ),
}


def build(key, v):
    START = datetime.datetime(2026, 10, 26, *v["start"], 0)
    SEARCH_MIN, MIG_MIN = v["search_min"], v["mig_min"]
    b = Builder(v["title"], START, v["file"])
    P = b.P
    s0 = b.start_s
    LZ = P(*v["lz"])                           # survivor
    DEPOT = P(42.740, 41.505)
    SEARCH = P(*v["search"])                   # where the search party sets out
    HOLD = P(*v["hold"])                       # Dodge holds over the water
    IP = LZ.point_from_heading(245, 18 * 1852)
    EGRESS = LZ.point_from_heading(260, 20 * 1852)
    TANKER = P(42.420, 40.860)

    b.carrier(recovery_min=60)
    cvn = b.cvn_start
    lo = {1: W["9X_1"], 2: W["MAV_2"], 3: W["MK20x2_3"], 4: W["LITENING"], 5: W["TANK_5"],
          6: W["120_6"], 7: W["GBU12x2_7"], 8: W["MAV_8"], 9: W["9X_9"]}
    b.enfield([lo, lo], [("DEPART", cvn.point_from_heading(45, 18_000), 5000, 350),
                         ("IP", IP, 15000, 400),
                         ("LZ", LZ, 15000, 400),
                         ("EGRESS", EGRESS, 15000, 400),
                         ("TANKER", TANKER, 15000, 300)])
    b.tanker(TANKER)
    b.awacs()
    b.cap(P(42.30, 40.85), commit_point=LZ.point_from_heading(270, 15_000))
    b.drone(LZ.point_from_heading(60, 1500))

    # survivor (Blue, hidden from Red AI so the search party has to walk up to him)
    sv = b.m.vehicle_group(b.usa, "Survivor", Infantry.Soldier_M4, LZ, heading=0, group_size=1)
    sv.units[0].name = "Survivor"

    # Red: short-range air defence still standing, and a search party
    if v["ad"] is None:
        b.vgroup(b.rus, "Depot AAA", [
            ("Depot ZSU North", AirDefence.ZSU_23_4_Shilka, b.off(P(42.749, 41.506), -300, 200)),
            ("Depot ZSU South", AirDefence.ZSU_23_4_Shilka, DEPOT.point_from_heading(200, 600)),
            ("Depot SA-13", AirDefence.Strela_10M3, DEPOT.point_from_heading(95, 500)),
        ], heading=220)
    else:
        b.vgroup(b.rus, v["ad_group"], [(n, t, P(*ll)) for n, t, ll in v["ad"]], heading=220)
    b.vgroup(b.rus, "Search Party", [
        ("Search BTR-80", Armor.BTR_80, SEARCH),
        ("Search ZU-23 truck", AirDefence.Ural_375_ZU_23, SEARCH.point_from_heading(180, 40)),
        ("Search Igla", AirDefence.SA_18_Igla_manpad, SEARCH.point_from_heading(90, 25)),
    ] + [(f"Search rifleman {i}", Infantry.Soldier_AK, SEARCH.point_from_heading(30 * i, 20 + 5 * i)) for i in range(1, 5)],
        heading=330)

    # Dodge: SH-60B holding over the water until flag 52, then pickup and home
    dodge = b.m.flight_group_inflight(b.usa, "Dodge", SH_60B, HOLD.point_from_heading(270, 2000), altitude=150, speed=200,
                                      maintask=task.Transport, group_size=1)
    dodge.units[0].name = "Dodge 1-1"
    dodge.units[0].callsign_dict = {1: 5, 2: 1, 3: 1, "name": "Dodge11"}
    dodge.units[0].skill = Skill.Excellent
    dodge.points[0].tasks.clear()
    hw = dodge.add_waypoint(HOLD, 150, 200, name="HOLD")
    hold = task.ControlledTask(task.OrbitAction(altitude=150, speed=200, pattern=task.OrbitAction.OrbitPattern.Circle))
    hold.stop_if_user_flag(52, True)
    hw.tasks.append(hold)
    lzw = dodge.add_waypoint(LZ, 60, 220, name="PICKUP")
    lzw.tasks.append(task.Land(mapping.Vector2(LZ.x, LZ.y), duration=120))
    dodge.add_waypoint(EGRESS, 150, 220, name="OUT")
    home = MovingPoint(b.cvn_start.point_from_heading(270, 50 * 1000 * 60 / 60))
    home.type, home.action = "Land", PointAction.Landing
    home.helipad_id = home.link_unit = b.cvn.units[0].id
    home.alt = home.speed = 0
    home.ETA_locked = False
    home.name = "MOTHER"
    home.properties = PointProperties()
    dodge.add_point(home)

    migs = b.m.flight_group_inflight(b.rus, "Red CAP", v["mig"], P(43.10, 40.62), altitude=5000, speed=850,
                                     maintask=task.CAP, group_size=2)
    migs.late_activation = True
    arm(migs)
    for u in migs.units:
        u.skill = Skill.Average
    mw = migs.add_waypoint(LZ, 5000, 850, name="LZ")
    mw.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(LZ.x, LZ.y), radius=40_000, targets=[task.Targets.All.Air]))
    mw.tasks.append(task.OrbitAction(altitude=5000, speed=750, pattern=task.OrbitAction.OrbitPattern.Circle))

    cfg = f"""T.cfg = {{
      START = {s0}, SURVIVOR = "Survivor", SURVIVOR_GROUP = "Survivor",
      HELO_GROUP = "Dodge", HELO_UNIT = "Dodge 1-1", HELO_FLAG = "52",
      SEARCH_GROUP = "Search Party", SEARCH_TIME = {s0 + SEARCH_MIN * 60}, SEARCH_SPEED = {SEARCH_SPEED},
      THREAT_GROUPS = {{ "{v['ad_group']}", "Search Party" }}, MIG_GROUP = "Red CAP", MIG_TIME = {s0 + MIG_MIN * 60},
      CAP_GROUP = "Chevy", CAP_FLAG = "51", JTAC_UNIT = "Pontiac", LASER_CODE = 1688,
      LZ = {{ x = {LZ.x:.1f}, z = {LZ.y:.1f} }}, CAPTURE_R = 300, PICKUP_R = 250, BOARD_S = 40, THREAT_R = 5000,
      HOLD = {{ x = {HOLD.x:.1f}, z = {HOLD.y:.1f} }}, HELO_MS = 60, JETS = {{ "Enfield 1-1", "Enfield 1-2" }},
  WHERE = "{v['where_short']}", TITLE = "{v['title'].upper()}",
  MIG_KIND = "{'MiG-29s' if v['mig'] is MiG_29A else 'MiG-21s'}",
    }}
    """
    b.add_cap_scripts("the survivor's area", fleet_only=False)
    b.add_script(read_lua("common.lua"))
    b.add_script(read_lua("sandy_lift.lua"), cfg, keep_copy=f"sandy_lift_{key}_built.lua")

    search_km = LZ.distance_to_point(SEARCH) / 1000
    capture_min = SEARCH_MIN + (LZ.distance_to_point(SEARCH) - 300) / SEARCH_SPEED / 60
    hold_nm = LZ.distance_to_point(HOLD) / 1852
    # Briefing text comes from briefings/*.md: build.py renders it and writes it into the .miz.
    desc = tasktext = "See the mission briefing."
    b.save(v["title"], desc, tasktext)
    print(v["file"], f"search {search_km:.1f} km, capture ~{hm(s0 + capture_min * 60)}, hold {hold_nm:.1f} nm")


for key, v in VARIANTS.items():
    build(key, v)
