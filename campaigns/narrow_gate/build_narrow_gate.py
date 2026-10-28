"""Build Operation_Narrow_Gate.miz (Caucasus, F/A-18C, 1-2 players)."""
import datetime
import re
from pathlib import Path

import dcs
from dcs import mapping, task, weather
from dcs.mapping import LatLng
from dcs.planes import FA_18C_hornet, S_3B_Tanker, E_2C, MQ_9_Reaper, MiG_21Bis, MiG_29S
from dcs import condition as dcs_condition, action as dcs_action
from missionbuilder.red_arms import arm
from missionbuilder.paths import out_dir, work_dir, read_lua
from dcs.ships import Stennis
from dcs.unit import Skill
from dcs.vehicles import AirDefence, Armor, Unarmed
from dcs.point import MovingPoint, PointAction, PointProperties
from dcs.triggers import TriggerStart
from dcs.action import DoScript
from dcs.translation import String
from mission_times import *  # noqa: F401,F403

OUT = out_dir() / "Operation_Narrow_Gate.miz"

m = dcs.Mission(dcs.terrain.Caucasus())
terrain = m.terrain


def P(lat, lon):
    return mapping.Point.from_latlng(LatLng(lat, lon), terrain)


# START, TOT_OFFSET, windows: see mission_times.py
TOT_ABS = START.hour * 3600 + START.minute * 60 + TOT_OFFSET
ZULU_OFFSET = 4 * 3600                    # Caucasus local = Z + 4
m.start_time = START

# Weather: clear, light wind
m.weather.clouds_preset = None
m.weather.clouds_density = 0
m.weather.wind_at_ground = weather.Wind(90, 3)
m.weather.wind_at_2000 = weather.Wind(90, 5)
m.weather.wind_at_8000 = weather.Wind(90, 8)

usa = m.country("USA")
rus = m.country("Russia")

# ------------------------------------------------------------------ geography
TGT = P(42.740, 41.505)                   # vehicle depot, coastal plain NE of Ochamchire
SAM = P(42.749, 41.506)                   # ~1 km north
CVN_START = P(42.150, 40.750)
PUSH = P(42.470, 41.030)                  # hold here to burn time
IP = P(42.630, 41.300)                    # ~21 km SW of target
EGRESS = P(42.640, 41.100)                # west over the coast
TANKER = P(42.420, 40.860)                # Arco track anchor
AWACS = P(42.300, 40.500)
MIG_SPAWN = P(43.080, 40.950)            # Gudauta alert pair, just airborne
PATROL_ORBIT = P(43.000, 40.500)          # Gudauta dawn patrol racetrack, offshore

# ------------------------------------------------------------------ carrier
cvn = m.ship_group(usa, "CVN-74 Stennis", Stennis, CVN_START, heading=270)
cvn.units[0].name = "CVN-74 Stennis"
cvn_unit = cvn.units[0]
CVN_SPEED_KMH = 50                         # ~27 kt into the wind
cvn_wp0 = cvn.points[0]
cvn_wp0.speed = CVN_SPEED_KMH / 3.6
cvn_wp0.tasks.append(task.ActivateBeaconCommand(channel=74, modechannel="X", callsign="STN",
                                                aa=False, unit_id=cvn_unit.id))
cvn_wp0.tasks.append(task.ActivateICLSCommand(channel=11, unit_id=cvn_unit.id))
cvn.add_waypoint(CVN_START.point_from_heading(270, 120_000), speed=CVN_SPEED_KMH)
cvn.set_frequency(127_500_000)
# where the boat will be ~50 min in (recovery, recovery time from mission_times)
CVN_RECOVERY = CVN_START.point_from_heading(270, CVN_SPEED_KMH * 1000 * RECOVERY_MIN / 60)

# ------------------------------------------------------------------ Enfield (players)
enfield = m.flight_group_from_unit(usa, "Enfield", FA_18C_hornet, cvn,
                                   maintask=task.GroundAttack,
                                   start_type=dcs.mission.StartType.Cold, group_size=2)
enfield.units[0].skill = Skill.Player      # flyable in single player; becomes a client slot in MP
enfield.units[1].skill = Skill.Client      # second human in MP (absent in SP)
enfield.units[0].name = "Enfield 1-1"
enfield.units[1].name = "Enfield 1-2"
enfield.set_frequency(251.0)
for i, u in enumerate(enfield.units, start=1):
    u.callsign_dict = {1: 1, 2: 1, 3: i, "name": f"Enfield1{i}"}

LOADOUT = {
    1: FA_18C_hornet.Pylon1.AIM_9X_Sidewinder_IR_AAM,
    2: FA_18C_hornet.Pylon2.LAU_115_2_x_LAU_127___1_x_AIM_120C_AMRAAM___Active_Radar_AAM,
    3: FA_18C_hornet.Pylon3.BRU_33_with_2_x_GBU_12___500lb_Laser_Guided_Bomb,
    4: FA_18C_hornet.Pylon4.AN_AAQ_28_LITENING___Targeting_Pod,
    5: FA_18C_hornet.Pylon5.FPU_8A_Fuel_Tank_330_gallons,
    6: FA_18C_hornet.Pylon6.AIM_120C_AMRAAM___Active_Radar_AAM,
    7: FA_18C_hornet.Pylon7.BRU_33_with_2_x_GBU_12___500lb_Laser_Guided_Bomb,
    8: FA_18C_hornet.Pylon8.LAU_115_2_x_LAU_127___1_x_AIM_120C_AMRAAM___Active_Radar_AAM_,
    9: FA_18C_hornet.Pylon9.AIM_9X_Sidewinder_IR_AAM,
}
for u in enfield.units:
    u.pylons.clear()
    for st, wpn in LOADOUT.items():
        u.load_pylon(wpn, st)
    u.fuel = FA_18C_hornet.fuel_max
    u.gun = 100
    u.chaff = 60
    u.flare = 30

FT = 0.3048
KTS = 1.852


def wp(group, point, alt_ft, kts, name):
    w = group.add_waypoint(point, alt_ft * FT, kts * KTS, name=name)
    return w


wp(enfield, CVN_START.point_from_heading(45, 18_000), 5000, 350, "DEPART")
wp(enfield, PUSH, 20000, 420, "PUSH")
wp(enfield, IP, 20000, 420, "IP")
tgt_wp = wp(enfield, TGT, 20000, 420, "TGT")
tgt_wp.ETA = TOT_OFFSET
tgt_wp.ETA_locked = True
wp(enfield, EGRESS, 20000, 420, "EGRESS")
wp(enfield, TANKER, 15000, 300, "TANKER")
land = MovingPoint(CVN_RECOVERY)
land.type = "Land"
land.action = PointAction.Landing
land.helipad_id = cvn_unit.id
land.link_unit = cvn_unit.id
land.alt = 0
land.speed = 0
land.ETA_locked = False
land.name = "MOTHER"
land.properties = PointProperties()
enfield.add_point(land)

# ------------------------------------------------------------------ support
arco = m.refuel_flight(usa, "Arco", S_3B_Tanker, None, TANKER, race_distance=30_000,
                       heading=230, altitude=15000 * FT, speed=270 * KTS, frequency=251,
                       tacanchannel="60Y")
arco.units[0].name = "Arco"
arco.units[0].callsign_dict = {1: 2, 2: 1, 3: 1, "name": "Arco11"}
magic = m.awacs_flight(usa, "Magic", E_2C, None, AWACS, race_distance=40_000, heading=0,
                       altitude=25000 * FT, frequency=255)

magic.units[0].callsign_dict = {1: 2, 2: 1, 3: 1, "name": "Magic11"}
magic.set_frequency(255)          # pydcs drops awacs_flight's frequency argument; set it on the group

# CHEVY: AI Hornet CAP on station from mission start. Orbits until flag 51 is set
# by a commit, then pushes to the egress area. In play, cap.lua retasks it directly (commit, reset, relief).
CAP_STATION = P(42.300, 40.850)            # between Mother and the coast
COMMIT_FLAG = 51
chevy = m.flight_group_inflight(usa, "Chevy", FA_18C_hornet, CAP_STATION.point_from_heading(250, 8000),
                                altitude=20000 * FT, speed=420 * KTS, maintask=task.CAP, group_size=2)
chevy.points[0].tasks = [t for t in chevy.points[0].tasks if not isinstance(t, task.CAPTaskAction)]
CAP_LOADOUT = {
    1: FA_18C_hornet.Pylon1.AIM_9X_Sidewinder_IR_AAM,
    2: FA_18C_hornet.Pylon2.LAU_115_2_LAU_127_AIM_120C,
    3: FA_18C_hornet.Pylon3.FPU_8A_Fuel_Tank_330_gallons,
    4: FA_18C_hornet.Pylon4.AIM_120C_AMRAAM___Active_Radar_AAM,
    6: FA_18C_hornet.Pylon6.AIM_120C_AMRAAM___Active_Radar_AAM,
    7: FA_18C_hornet.Pylon7.FPU_8A_Fuel_Tank_330_gallons,
    8: FA_18C_hornet.Pylon8.LAU_115_2_LAU_127_AIM_120C,
    9: FA_18C_hornet.Pylon9.AIM_9X_Sidewinder_IR_AAM,
}
for i, u in enumerate(chevy.units, start=1):
    u.skill = Skill.Good
    u.name = f"Chevy 1-{i}"
    u.callsign_dict = {1: 7, 2: 1, 3: i, "name": f"Chevy1{i}"}
    u.pylons.clear()
    for st, wpn in CAP_LOADOUT.items():
        u.load_pylon(wpn, st)
station_wp = chevy.add_waypoint(CAP_STATION, 20000 * FT, 420 * KTS, name="CAP STATION")
station_wp.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(CAP_STATION.x, CAP_STATION.y),
                                                 radius=40_000, targets=[task.Targets.All.Air]))
hold = task.ControlledTask(task.OrbitAction(altitude=20000 * FT, speed=420 * KTS,
                                            pattern=task.OrbitAction.OrbitPattern.Circle))
hold.stop_if_user_flag(COMMIT_FLAG, True)
station_wp.tasks.append(hold)
commit_wp = chevy.add_waypoint(EGRESS, 20000 * FT, 480 * KTS, name="COMMIT EGRESS")
commit_wp.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(EGRESS.x, EGRESS.y),
                                                radius=70_000, targets=[task.Targets.All.Air]))
commit_wp.tasks.append(task.OrbitAction(altitude=20000 * FT, speed=450 * KTS,
                                        pattern=task.OrbitAction.OrbitPattern.Circle))

# FORD: the transiting jamming package (F/A-18C stand-ins; no stock DCS aircraft jams for others).
# Its track is laid out so a FORD jet is within JAM_R of the SA-6 from SUP_ON to SUP_OFF, closest pass
# FORD_CPA (outside SA-6 reach). The script turns jamming on and off from FORD's real position.
import math as _m
JAM_R, FORD_CPA, FORD_HDG = 40_000, 27_000, 320
FORD_LEAD_S = 300                                    # activates this long before it reaches jamming range
TOT_ABS_ = START.hour * 3600 + START.minute * 60 + TOT_OFFSET
half_chord = _m.sqrt(JAM_R ** 2 - FORD_CPA ** 2)
FORD_MS = 2 * half_chord / (SUP_BEFORE + SUP_AFTER)  # ground speed that makes the pass last the planned window
FORD_C = SAM.point_from_heading((FORD_HDG - 90) % 360, FORD_CPA)          # closest point, offshore SW of the SA-6
FORD_E = FORD_C.point_from_heading((FORD_HDG + 180) % 360, half_chord)    # enters jamming range
FORD_X = FORD_C.point_from_heading(FORD_HDG, half_chord)                  # leaves jamming range
FORD_S = FORD_E.point_from_heading((FORD_HDG + 180) % 360, FORD_MS * FORD_LEAD_S)
FORD_N = FORD_X.point_from_heading(FORD_HDG, 120_000)                     # on to its tasking up north
FORD_SPAWN = TOT_ABS_ - SUP_BEFORE - FORD_LEAD_S
ford = m.flight_group_inflight(usa, "Ford", FA_18C_hornet, FORD_S, altitude=25000 * FT, speed=FORD_MS * 3.6,
                               maintask=task.CAP, group_size=2)
ford.late_activation = True
# Self-defence only: fires back and evades, never chases (no engage task), resumes its route north.
ford.points[0].tasks = [task.OptROE(task.OptROE.Values.ReturnFire),
                        task.OptReactOnThreat(task.OptReactOnThreat.Values.EvadeFire)]
FORD_LOADOUT = {   # 2x AIM-120C like a Growler's self-defence fit; tanks stand in for the jamming pods
    3: FA_18C_hornet.Pylon3.FPU_8A_Fuel_Tank_330_gallons,
    4: FA_18C_hornet.Pylon4.AIM_120C_AMRAAM___Active_Radar_AAM,
    6: FA_18C_hornet.Pylon6.AIM_120C_AMRAAM___Active_Radar_AAM,
    7: FA_18C_hornet.Pylon7.FPU_8A_Fuel_Tank_330_gallons,
}
for i, u in enumerate(ford.units, start=1):
    u.name = f"Ford 1-{i}"
    u.callsign_dict = {1: 6, 2: 1, 3: i, "name": f"Ford1{i}"}
    u.skill = Skill.Excellent
    u.pylons.clear()
    for st, wpn in FORD_LOADOUT.items():
        u.load_pylon(wpn, st)
for pt, nm in [(FORD_E, "JAM ON"), (FORD_C, "CLOSEST"), (FORD_X, "JAM OFF"), (FORD_N, "NORTH")]:
    ford.add_waypoint(pt, 25000 * FT, FORD_MS * 3.6, name=nm)
assert SAM.distance_to_point(FORD_C) > 25_000, "FORD must stay outside SA-6 reach"

# PONTIAC drone (controls for the Blue ground commander): orbits the target, script lases on request
pontiac = m.flight_group_inflight(usa, "Pontiac", MQ_9_Reaper, TGT.point_from_heading(200, 6000),
                                  altitude=4500, speed=220, maintask=task.Reconnaissance)
pontiac.units[0].name = "Pontiac"
pontiac.units[0].callsign_dict = {1: 8, 2: 1, 3: 1, "name": "Pontiac11"}
pontiac.points[0].tasks.clear()
orbit_wp = pontiac.add_waypoint(TGT, 4500, 220, name="ORBIT")
orbit_wp.tasks.append(task.OrbitAction(altitude=4500, speed=220,
                                       pattern=task.OrbitAction.OrbitPattern.Circle))

# ------------------------------------------------------------------ red
targets = m.vehicle_group(rus, "Depot Targets", Armor.T_72B, TGT, heading=45, group_size=2,
                          formation=dcs.unitgroup.VehicleGroup.Formation.Scattered)
targets.units[1].position = mapping.Point(TGT.x - 55, TGT.y - 45, terrain)
for i, off in enumerate([(60, 40), (-50, 70), (20, -80)]):
    u = m.vehicle(f"Depot Truck {i + 1}", Unarmed.Ural_375)
    u.position = mapping.Point(TGT.x + off[0], TGT.y + off[1], terrain)
    u.heading = 45
    targets.add_unit(u)
for i, u in enumerate(targets.units):
    u.skill = Skill.Average
targets.points[0].tasks.append(task.OptROE(task.OptROE.Values.WeaponHold))

sam = m.vehicle_group(rus, "Depot SAM", AirDefence.Kub_1S91_str, SAM, heading=200, group_size=1)
for i, (dx, dy) in enumerate([(250, -150), (-200, -250), (-300, 250), (300, 300)], start=1):   # standard battery: 1 radar + 4 TELs
    ln = m.vehicle(f"Depot SAM Launcher {i}", AirDefence.Kub_2P25_ln)
    ln.position = mapping.Point(SAM.x + dx, SAM.y + dy, terrain)
    ln.heading = 200
    sam.add_unit(ln)
# Guns: separate group: FORD jams only the SA-6 radar (north with the SA-6, south of the depot)
aaa = m.vehicle_group(rus, "Depot AAA", AirDefence.ZSU_23_4_Shilka,
                      mapping.Point(SAM.x - 300, SAM.y + 200, terrain), heading=200, group_size=1)
aaa.units[0].name = "Depot ZSU North"
zsu_s = m.vehicle("Depot ZSU South", AirDefence.ZSU_23_4_Shilka)
zsu_s.position = TGT.point_from_heading(200, 600)
zsu_s.heading = 200
aaa.add_unit(zsu_s)
sa13 = m.vehicle("Depot SA-13", AirDefence.Strela_10M3)      # IR short-range SAM: radar jamming doesn't affect it
sa13.position = TGT.point_from_heading(95, 500)
sa13.heading = 220
aaa.add_unit(sa13)
for u in aaa.units:
    u.skill = Skill.Average
for u in sam.units:
    u.skill = Skill.Average

migs = m.flight_group_inflight(rus, "Red Scramble", MiG_21Bis, MIG_SPAWN, altitude=6000,
                               speed=850, maintask=task.CAP, group_size=2)
migs.late_activation = True
arm(migs)
for u in migs.units:
    u.skill = Skill.Average
migs.add_waypoint(TGT, 6000, 850, name="Target area")
migs.add_waypoint(EGRESS, 6000, 850, name="Coast")
migs.add_waypoint(TGT, 6000, 850, name="Target area 2")

# Gudauta dawn patrol: up on some mornings only (mission-start RANDOM triggers set flags 60/61).
# Orbits offshore until the script sets flag 62 (FORD's jammers come on), then goes for FORD and RTBs.
PATROL_FLAG, PATROL_TYPE_FLAG, PATROL_PUSH_FLAG = 60, 61, 62
PATROL_CHANCE, PATROL_29_CHANCE = 20, 50
gudauta = terrain.airports["Gudauta"]
for pname, ptype in [("Red Patrol 21", MiG_21Bis), ("Red Patrol 29", MiG_29S)]:
    pg = m.flight_group_inflight(rus, pname, ptype, PATROL_ORBIT.point_from_heading(0, 6000), altitude=6000,
                                 speed=800, maintask=task.CAP, group_size=2)
    pg.late_activation = True
    arm(pg)
    pg.points[0].tasks = [t for t in pg.points[0].tasks if not isinstance(t, task.CAPTaskAction)]
    for i, u in enumerate(pg.units, start=1):
        u.name = f"{pname} {i}"
        u.skill = Skill.Good
    o = pg.add_waypoint(PATROL_ORBIT, 6000, 800, name="PATROL")
    ph = task.ControlledTask(task.OrbitAction(altitude=6000, speed=800, pattern=task.OrbitAction.OrbitPattern.RaceTrack))
    ph.stop_if_user_flag(PATROL_PUSH_FLAG, True)
    o.tasks.append(ph)
    hit = pg.add_waypoint(FORD_C, 6500, 950, name="INTERCEPT")
    hit.tasks.append(task.AttackGroup(ford.id))
    hit.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(FORD_C.x, FORD_C.y), radius=45_000,
                                              targets=[task.Targets.All.Air]))
    pg.land_at(gudauta)

for flag, pct in [(PATROL_FLAG, PATROL_CHANCE), (PATROL_TYPE_FLAG, PATROL_29_CHANCE)]:
    rt = TriggerStart(comment=f"random {pct}% -> flag {flag}")
    rt.add_condition(dcs_condition.Random(pct))
    rt.add_action(dcs_action.SetFlag(flag))
    m.triggerrules.triggers.append(rt)

def _brg_nm(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (a.latlng().lat, a.latlng().lng, b.latlng().lat, b.latlng().lng))
    dlo = lo2 - lo1
    brg = (math.degrees(math.atan2(math.sin(dlo) * math.cos(la2),
           math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo))) + 360) % 360
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return brg, 2 * 6371000 * math.asin(math.sqrt(h)) / 1852


IP_HDG, IP_DIST = _brg_nm(IP, TGT)
EGRESS_HDG, _ = _brg_nm(TGT, EGRESS)

# ------------------------------------------------------------------ script
lua = read_lua("narrow_gate.lua")
cfg = f"""T.cfg = {{
  TOT          = {TOT_ABS},
  WINDOW       = {WINDOW},
  SUP_BEFORE   = {SUP_BEFORE},
  SUP_AFTER    = {SUP_AFTER},
  ZULU_OFFSET  = {ZULU_OFFSET},
  TARGET_GROUP = "Depot Targets",
  SAM_GROUP    = "Depot SAM",
  AAA_GROUP    = "Depot AAA",
  SCRAMBLE_GROUP = "Red Scramble",
  CAP_GROUP    = "Chevy",
  CAP_FLAG     = "51",
  JTAC_UNIT    = "Pontiac",
  CARRIER_UNIT = "CVN-74 Stennis",
  LASER_CODE   = 1688,
  TARGET_POINT = {{ x = {TGT.x:.1f}, z = {TGT.y:.1f} }},
  IMPACT_RADIUS = 2500,
  TANKER_INFO  = "Arco, 251.0 AM, TACAN 60Y",
  IP_HDG = "{IP_HDG:03.0f}", IP_DIST = "{IP_DIST:.1f}", EGRESS_HDG = "{EGRESS_HDG:03.0f}", FAH = "030-080",
  FAH_MIN = 30, FAH_MAX = 80,
  JETS = {{ "Enfield 1-1", "Enfield 1-2" }},
  FORD_GROUP = "Ford", FORD_UNITS = {{ "Ford 1-1", "Ford 1-2" }}, FORD_SPAWN = {FORD_SPAWN},
  JAM_R = {JAM_R}, SAM_POINT = {{ x = {SAM.x:.1f}, z = {SAM.y:.1f} }},
  PATROL_FLAG = "{PATROL_FLAG}", PATROL_TYPE_FLAG = "{PATROL_TYPE_FLAG}", PATROL_PUSH_FLAG = "{PATROL_PUSH_FLAG}",
  PATROL_21 = "Red Patrol 21", PATROL_29 = "Red Patrol 29",
  CAP_SCREEN = {{ x = {FORD_C.x:.1f}, z = {FORD_C.y:.1f} }},
  CAP_EGRESS = {{ x = {EGRESS.x:.1f}, z = {EGRESS.y:.1f} }},
  MIN_FUEL = 0.18,
  NEXT_SUCCESS = "Operation_Long_Road.miz",
  NEXT_SUCCESS_LATE = "Operation_Long_Road_Own_SEAD.miz",
  NEXT_PARTIAL = "Operation_Stone_Ford.miz",
  NEXT_FAILURE = "Operation_Stone_Ford_Hard.miz",
  NEXT_RESCUE  = "Operation_Sandy_Lift.miz",
  OUTCOME_FLAG = "90",
  RESCUE_FLAG  = "91",
  FRIENDLIES = "Blue ground forces at the Inguri, 20 nm south-east",
}}
"""
lua = re.sub(r"T\.cfg = T\.cfg or \{.*?\n\}\n", lambda _: cfg, lua, count=1, flags=re.S)
assert f"TOT          = {TOT_ABS}" in lua
(work_dir() / "narrow_gate_built.lua").write_text(lua, encoding="utf-8")

from missionbuilder.builder import cap_lua_cfg
trig = TriggerStart(comment="TOT strike script")
trig.add_action(DoScript(m.string(cap_lua_cfg(CAP_STATION))))                    # CAPCFG
trig.add_action(DoScript(m.string(read_lua("cap.lua"))))   # controller-run CAP
trig.add_action(DoScript(m.string(lua)))
m.triggerrules.triggers.append(trig)


# ------------------------------------------------------------------ briefing
def hms(s):
    s %= 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


TOT_L, TOT_Z = hms(TOT_ABS), hms(TOT_ABS - ZULU_OFFSET)
m.set_sortie_text("Operation Narrow Gate")
# Briefing text comes from briefings/narrow_gate.md: build.py renders it and writes it into the .miz.
m.set_description_text("See the mission briefing.")
m.set_description_bluetask_text("See the mission briefing.")

m.save(str(OUT))
print("saved", OUT, "TOT", TOT_L, TOT_Z)
print("Arco callsign/freq:", arco.units[0].callsign_dict if hasattr(arco.units[0], 'callsign_dict') else arco.units[0].name, arco.frequency)
