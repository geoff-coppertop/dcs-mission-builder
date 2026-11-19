"""Build Operation_Deep_Cut_Escape.miz: the follow-up flown when a Deep Cut pilot ejects over land.

Red's F-14A-135-GR, readied for a ferry flight (full fuel and tanks, gun only, start cart hooked up), cold on
the ramp at Senaki-Kolkhi (neutral field, Red guards around it, on alert the morning after the raid). Get
airborne before you are seen, outrun the Kutaisi alert to the coast where CHEVY holds CAP, and land aboard CVN-74.
The jet is in the Iran country, moved into the blue coalition, so DCS gives it its default ex-export paint.
One jet, 1 player; in multiplayer a second player can take the RIO seat.
"""
import datetime

import dcs
from dcs import task, mapping
from dcs.planes import F_14A_135_GR as F14A, MiG_29S
from dcs.point import MovingPoint, PointAction, PointProperties
from dcs.unit import Skill
from dcs.vehicles import AirDefence, Armor

from missionbuilder.builder import Builder, FT, KTS
from missionbuilder.paths import read_lua
from missionbuilder.red_arms import arm

START = datetime.datetime(2027, 1, 15, 8, 50, 0)     # the next morning, just after sunrise
DISCOVER = 9 * 60                                    # guards reach the jet this long after start (base on alert):
                                                     # a stored-heading start (~3 min align) plus taxi, with some margin
ALERT_REACT = 6 * 60                                 # Kutaisi's alert after the jet is seen: 1-2 min to relay the
                                                     # report to the sector and on to Kutaisi, then a cockpit-
                                                     # readiness scramble (takeoff within 5 min)
COAST = (42.200, 41.640)                             # feet wet, south of the Enguri mouth


def build():
    b = Builder("Operation Deep Cut: Escape", START, "Operation_Deep_Cut_Escape.miz")
    b.m.weather.season_temperature = -6
    P = b.P
    field = b.terrain.airports["Senaki-Kolkhi"]
    fp = field.position
    coast = P(*COAST)

    b.carrier(start=(42.150, 39.750), recovery_min=40)     # ~85 nm off the coast, ~100 nm by recovery
    b.tanker(P(42.30, 40.95))
    b.awacs()
    b.cap(P(42.25, 41.25), commit_point=coast)

    # Red's Tomcat, readied for a ferry flight: fuelled, tanks on, no missiles
    iran = b.m.coalition["red"].swap_country(b.m.coalition["blue"], "Iran")
    g = b.m.flight_group_from_airport(iran, "Enfield", F14A, field, maintask=task.CAP,
                                      start_type=dcs.mission.StartType.Cold, group_size=1)
    u = g.units[0]
    u.name, u.skill = "Enfield 1-1", Skill.Player
    u.callsign_dict = {1: 1, 2: 1, 3: 1, "name": "Enfield11"}
    u.pylons.clear()
    for st, store in {3: F14A.Pylon3.Fuel_tank_300_gal_, 8: F14A.Pylon8.Fuel_tank_300_gal_}.items():
        u.load_pylon(store, st)
    u.fuel = F14A.fuel_max
    # the ferry crew aligned the INS during yesterday's engine runs and the jet hasn't moved: stored heading is valid
    u.set_property("INSAlignmentStored", True)
    # no TACAN preset: a Red ferry jet has no reason to carry Mother's channel; the pilot dials 74X
    u.gun, u.chaff, u.flare = 100, 60, 30
    g.set_frequency(251.0)
    g.add_waypoint(fp.point_from_heading(270, 8000), 1500 * FT, 450 * KTS, name="RUN WEST")
    g.add_waypoint(coast, 1500 * FT, 480 * KTS, name="FEET WET")
    g.add_waypoint(P(42.25, 41.25), 10000 * FT, 400 * KTS, name="CHEVY")
    land = MovingPoint(b.cvn_recovery)
    land.type, land.action = "Land", PointAction.Landing
    land.helipad_id = land.link_unit = b.cvn.units[0].id
    land.alt = land.speed = 0
    land.ETA_locked = False
    land.name = "MOTHER"
    land.properties = PointProperties()
    g.add_point(land)

    # Red guards on the field: quiet until the jet is seen
    b.vgroup(b.rus, "Senaki Guns North", [("Senaki ZU-23 N1", AirDefence.ZU_23_Emplacement, fp.point_from_heading(0, 700)),
                                          ("Senaki ZU-23 N2", AirDefence.ZU_23_Emplacement, fp.point_from_heading(20, 800))], 180)
    b.vgroup(b.rus, "Senaki Guns South", [("Senaki ZU-23 S1", AirDefence.ZU_23_Emplacement, fp.point_from_heading(180, 700)),
                                          ("Senaki ZSU-23-4", AirDefence.ZSU_23_4_Shilka, fp.point_from_heading(200, 900))], 0)
    b.vgroup(b.rus, "Senaki SA-13", [("Senaki SA-13", AirDefence.Strela_10M3, fp.point_from_heading(90, 1500))], 270)

    # the guard post: a BRDM-2 300 m from the Tomcat toward the field, late-activated; the script sends it at the
    # jet (and spawns infantry) if the guards spot you before you're airborne
    park = g.units[0].position
    post = park.point_from_heading(park.heading_between_point(fp), 300)
    car = b.vgroup(b.rus, "Senaki Guard Car", [("Senaki BRDM-2", Armor.BRDM_2, post)], 0)
    car.late_activation = True

    # the Kutaisi alert: launches after the jet is seen
    kut = b.terrain.airports["Kutaisi"].position
    r = b.m.flight_group_inflight(b.rus, "Red South", MiG_29S, kut.point_from_heading(300, 6000), altitude=1500,
                                  speed=900, maintask=task.CAP, group_size=2)
    r.late_activation = True
    arm(r)
    r.points[0].tasks = [t for t in r.points[0].tasks if not isinstance(t, task.CAPTaskAction)]
    for i, ru in enumerate(r.units, start=1):
        ru.name, ru.skill = f"Red South {i}", Skill.Good
    w = r.add_waypoint(coast, 4000, 1000, name="Coast")
    w.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(coast.x, coast.y), radius=70_000,
                                            targets=[task.Targets.All.Air]))
    w.tasks.append(task.OrbitAction(altitude=4000, speed=850, pattern=task.OrbitAction.OrbitPattern.Circle))

    cfg = f"""T.cfg = {{
  NAME = "OPERATION DEEP CUT: ESCAPE", START = {b.start_s}, DISCOVER = {DISCOVER}, TAKEOFF_NOTICE = 20, ALERT_REACT = {ALERT_REACT},
  FIELD = "Senaki-Kolkhi", FIELD_AD = {{ "Senaki Guns North", "Senaki Guns South", "Senaki SA-13" }},
  SOUTH_GROUP = "Red South", SOUTH_KIND = "two MiG-29s", SOUTH_BASE = "Kutaisi",
  JET = "Enfield 1-1", OUTCOME_FLAG = "90",
  CODE = "KESTREL", CARRIER = "CVN-74 Stennis", ID_R = 148160, VID_R = 3700, VID_S = 8,
  FLEET_WARN_R = 37040, FLEET_R = 18520, MISSILE_TOF = 20,
  PARK = {{ x = {park.x:.1f}, z = {park.y:.1f} }}, PARK_R = 30, CAUGHT_WINDOW = 60,
  GUARD_CAR = "Senaki Guard Car", GUARDS = "Senaki Guards", GUARD_TYPE = "Soldier AK",
}}
"""
    b.add_cap_scripts("the coast")
    b.add_script(read_lua("common.lua"))
    b.add_script(read_lua("escape.lua"), cfg, keep_copy="escape_built.lua")
    b.save("Operation Deep Cut: Escape", "See the mission briefing.", "See the mission briefing.")


if __name__ == "__main__":
    build()
