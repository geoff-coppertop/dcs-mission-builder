"""Shared mission-building blocks for the Narrow Gate campaign follow-ons.

Same carrier, Enfield flight, tanker, AWACS, CAP and drone setup as Operation Narrow Gate,
parameterised so each follow-on mission only describes its own fight.
"""
import math
import re
from pathlib import Path

import dcs
from dcs import mapping, task, weather
from dcs.mapping import LatLng
from dcs.planes import FA_18C_hornet as HN, S_3B_Tanker, E_2C, MQ_9_Reaper
from dcs.ships import Stennis
from dcs.unit import Skill
from dcs.point import MovingPoint, PointAction, PointProperties
from dcs.triggers import TriggerStart
from dcs.action import DoScript

from .paths import out_dir, work_dir, read_lua
FT = 0.3048
KTS = 1.852
ZULU_OFFSET = 4 * 3600
LASER_CODE = 1688


def hms(s):
    s = int(round(s)) % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def hm(s):
    return hms(s)[:5]


# Hornet stores used across the campaign
W = {
    "9X_1": HN.Pylon1.AIM_9X_Sidewinder_IR_AAM,
    "9X_9": HN.Pylon9.AIM_9X_Sidewinder_IR_AAM,
    "120_6": HN.Pylon6.AIM_120C_AMRAAM___Active_Radar_AAM,
    "120x1_2": HN.Pylon2.LAU_115_2_x_LAU_127___1_x_AIM_120C_AMRAAM___Active_Radar_AAM,
    "120x1_8": HN.Pylon8.LAU_115_2_x_LAU_127___1_x_AIM_120C_AMRAAM___Active_Radar_AAM_,
    "LITENING": HN.Pylon4.AN_AAQ_28_LITENING___Targeting_Pod,
    "TANK_5": HN.Pylon5.FPU_8A_Fuel_Tank_330_gallons,
    "TANK_3": HN.Pylon3.FPU_8A_Fuel_Tank_330_gallons,
    "TANK_7": HN.Pylon7.FPU_8A_Fuel_Tank_330_gallons,
}
for st in (2, 3, 7, 8):
    p = getattr(HN, f"Pylon{st}")
    W[f"HARM_{st}"] = p.AGM_88C_HARM___High_Speed_Anti_Radiation_Missile_
    W[f"GBU12x2_{st}"] = p.BRU_33_with_2_x_GBU_12___500lb_Laser_Guided_Bomb
    W[f"GBU12_{st}"] = p.GBU_12___500lb_Laser_Guided_Bomb
    W[f"MK20x2_{st}"] = p.BRU_33_with_2_x_Mk_20_Rockeye___490lbs_CBU__247_x_HEAT_Bomblets
    W[f"MK20_{st}"] = p.Mk_20_Rockeye___490lbs_CBU__247_x_HEAT_Bomblets
    W[f"MAV_{st}"] = p.LAU_117_AGM_65F


class Builder:
    def __init__(self, name, start_dt, out_file):
        self.name = name
        self.out = out_dir() / out_file
        self.m = dcs.Mission(dcs.terrain.Caucasus())
        self.terrain = self.m.terrain
        self.m.start_time = start_dt
        self.start_s = start_dt.hour * 3600 + start_dt.minute * 60
        w = self.m.weather
        w.clouds_preset = None
        w.clouds_density = 0
        w.wind_at_ground = weather.Wind(90, 3)
        w.wind_at_2000 = weather.Wind(90, 5)
        w.wind_at_8000 = weather.Wind(90, 8)
        self.usa = self.m.country("USA")
        self.rus = self.m.country("Russia")
        self.scripts = []

    # ------------------------------------------------------------ geometry
    def P(self, lat, lon):
        return mapping.Point.from_latlng(LatLng(lat, lon), self.terrain)

    def off(self, p, dx_north, dy_east):
        return mapping.Point(p.x + dx_north, p.y + dy_east, self.terrain)

    @staticmethod
    def brg_nm(a, b):
        la1, lo1, la2, lo2 = map(math.radians, (a.latlng().lat, a.latlng().lng, b.latlng().lat, b.latlng().lng))
        dlo = lo2 - lo1
        brg = (math.degrees(math.atan2(math.sin(dlo) * math.cos(la2),
               math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo))) + 360) % 360
        h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
        return brg, 2 * 6371000 * math.asin(math.sqrt(h)) / 1852

    # ------------------------------------------------------------ carrier
    def carrier(self, start=(42.150, 40.750), recovery_min=50, speed_kmh=50):
        p = self.P(*start)
        cvn = self.m.ship_group(self.usa, "CVN-74 Stennis", Stennis, p, heading=270)
        cvn.units[0].name = "CVN-74 Stennis"
        u = cvn.units[0]
        wp0 = cvn.points[0]
        wp0.speed = speed_kmh / 3.6
        wp0.tasks.append(task.ActivateBeaconCommand(channel=74, modechannel="X", callsign="STN", aa=False, unit_id=u.id))
        wp0.tasks.append(task.ActivateICLSCommand(channel=11, unit_id=u.id))
        cvn.add_waypoint(p.point_from_heading(270, 120_000), speed=speed_kmh)
        cvn.set_frequency(127_500_000)
        self.cvn, self.cvn_start = cvn, p
        self.cvn_recovery = p.point_from_heading(270, speed_kmh * 1000 * recovery_min / 60)
        return cvn

    # ------------------------------------------------------------ players
    def enfield(self, loadouts, route, name="Enfield", freq=251.0):
        """loadouts: [ {station: store}, {station: store} ]  (1-1, 1-2)
        route: [(name, point, alt_ft, kts) ...]; MOTHER landing appended automatically."""
        g = self.m.flight_group_from_unit(self.usa, name, HN, self.cvn, maintask=task.GroundAttack,
                                          start_type=dcs.mission.StartType.Cold, group_size=2)
        g.units[0].skill = Skill.Player
        g.units[1].skill = Skill.Client
        for i, u in enumerate(g.units, start=1):
            u.name = f"{name} 1-{i}"
            u.callsign_dict = {1: 1, 2: 1, 3: i, "name": f"{name}1{i}"}
            u.pylons.clear()
            for st, store in loadouts[i - 1].items():
                u.load_pylon(store, st)
            u.fuel = HN.fuel_max
            u.gun = 100
            u.chaff = 60
            u.flare = 30
        g.set_frequency(freq)
        self.wps = {}
        for wname, pt, alt_ft, kts in route:
            self.wps[wname] = g.add_waypoint(pt, alt_ft * FT, kts * KTS, name=wname)
        land = MovingPoint(self.cvn_recovery)
        land.type, land.action = "Land", PointAction.Landing
        land.helipad_id = land.link_unit = self.cvn.units[0].id
        land.alt = land.speed = 0
        land.ETA_locked = False
        land.name = "MOTHER"
        land.properties = PointProperties()
        g.add_point(land)
        self.enfield_g = g
        return g

    # ------------------------------------------------------------ support
    def tanker(self, anchor, heading=230):
        a = self.m.refuel_flight(self.usa, "Arco", S_3B_Tanker, None, anchor, race_distance=30_000, heading=heading,
                                 altitude=15000 * FT, speed=270 * KTS, frequency=251, tacanchannel="60Y")
        a.units[0].name = "Arco"
        a.units[0].callsign_dict = {1: 2, 2: 1, 3: 1, "name": "Arco11"}
        return a

    def awacs(self, anchor=(42.300, 40.500)):
        g = self.m.awacs_flight(self.usa, "Magic", E_2C, None, self.P(*anchor), race_distance=40_000, heading=0,
                                altitude=25000 * FT, frequency=255)
        g.units[0].callsign_dict = {1: 2, 2: 1, 3: 1, "name": "Magic11"}
        g.set_frequency(255)      # pydcs drops awacs_flight's frequency argument; set it on the group
        return g

    def cap(self, station, commit_point, commit_flag=51):
        """CHEVY: AI Hornet CAP on station; F10 commit sets the flag, which ends the orbit."""
        HN_ = HN
        g = self.m.flight_group_inflight(self.usa, "Chevy", HN_, station.point_from_heading(250, 8000),
                                         altitude=20000 * FT, speed=420 * KTS, maintask=task.CAP, group_size=2)
        g.points[0].tasks = [t for t in g.points[0].tasks if not isinstance(t, task.CAPTaskAction)]
        lo = cap_loadout()
        self.cap_station, self.cap_commit = station, commit_point
        for i, u in enumerate(g.units, start=1):
            u.skill = Skill.Good
            u.name = f"Chevy 1-{i}"
            u.callsign_dict = {1: 7, 2: 1, 3: i, "name": f"Chevy1{i}"}
            u.pylons.clear()
            for st, store in lo.items():
                u.load_pylon(store, st)
        s = g.add_waypoint(station, 20000 * FT, 420 * KTS, name="CAP STATION")
        s.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(station.x, station.y), radius=40_000,
                                                targets=[task.Targets.All.Air]))
        hold = task.ControlledTask(task.OrbitAction(altitude=20000 * FT, speed=420 * KTS,
                                                    pattern=task.OrbitAction.OrbitPattern.Circle))
        hold.stop_if_user_flag(commit_flag, True)
        s.tasks.append(hold)
        c = g.add_waypoint(commit_point, 20000 * FT, 480 * KTS, name="COMMIT")
        c.tasks.append(task.EngageTargetsInZone(position=mapping.Vector2(commit_point.x, commit_point.y), radius=70_000,
                                                targets=[task.Targets.All.Air]))
        c.tasks.append(task.OrbitAction(altitude=20000 * FT, speed=450 * KTS, pattern=task.OrbitAction.OrbitPattern.Circle))
        return g

    def add_cap_scripts(self, label, fleet_only=False):
        """CAPCFG + cap.lua (controller-run CAP with alert relief); call before the mission script.
        label names the player's area that commits and cover requests go to (the builder's commit point)."""
        self.add_script(cap_lua_cfg(self.cap_station, fleet_only=fleet_only, req=self.cap_commit, req_label=label))
        self.add_script(read_lua("cap.lua"))

    def drone(self, center, name="Pontiac", alt_m=4500):
        g = self.m.flight_group_inflight(self.usa, name, MQ_9_Reaper, center.point_from_heading(200, 6000),
                                         altitude=alt_m, speed=220, maintask=task.Reconnaissance)
        g.units[0].name = name
        g.units[0].callsign_dict = {1: 8, 2: 1, 3: 1, "name": f"{name}11"}
        g.points[0].tasks.clear()
        o = g.add_waypoint(center, alt_m, 220, name="ORBIT")
        o.tasks.append(task.OrbitAction(altitude=alt_m, speed=220, pattern=task.OrbitAction.OrbitPattern.Circle))
        return g

    # ------------------------------------------------------------ red helpers
    def vgroup(self, side_country, name, units, heading=0, skill=Skill.Average):
        """units: [(unit_name, type, point)]; first unit creates the group."""
        n0, t0, p0 = units[0]
        g = self.m.vehicle_group(side_country, name, t0, p0, heading=heading, group_size=1)
        g.units[0].name = n0
        for un, ut, up in units[1:]:
            v = self.m.vehicle(un, ut)
            v.position = up
            v.heading = heading
            g.add_unit(v)
        for u in g.units:
            u.skill = skill
            u.heading = heading
        return g

    # ------------------------------------------------------------ scripts and save
    def add_script(self, lua_text, cfg_text=None, keep_copy=None):
        if cfg_text is not None:
            lua_text = re.sub(r"T\.cfg = T\.cfg or \{.*?\n\}\n", lambda _: cfg_text, lua_text, count=1, flags=re.S)
            assert cfg_text.strip()[:20] in lua_text
        if keep_copy:
            (work_dir() / keep_copy).write_text(lua_text, encoding="utf-8")
        self.scripts.append(lua_text)

    def save(self, sortie, description, task_text):
        trig = TriggerStart(comment=f"{self.name} scripts")
        for s in self.scripts:
            trig.add_action(DoScript(self.m.string(s)))
        self.m.triggerrules.triggers.append(trig)
        self.m.set_sortie_text(sortie)
        self.m.set_description_text(description)
        self.m.set_description_bluetask_text(task_text)
        self.m.save(str(self.out))
        print("saved", self.out)


def cap_loadout():
    """CHEVY / UZI fit: 2x AIM-9X, 6x AIM-120C, 2 tanks."""
    return {1: W["9X_1"], 2: HN.Pylon2.LAU_115_2_LAU_127_AIM_120C, 3: W["TANK_3"], 4: HN.Pylon4.AIM_120C_AMRAAM___Active_Radar_AAM,
            6: W["120_6"], 7: W["TANK_7"], 8: HN.Pylon8.LAU_115_2_LAU_127_AIM_120C, 9: W["9X_9"]}


def cap_lua_cfg(station, fleet_only=False, flag=51, boat_r=40_000, carrier="CVN-74 Stennis",
                alert_delay=300, alert_transit=420, req=None, req_label="your area"):
    """Lua text defining CAPCFG for cap.lua. station is a pydcs Point (x north, y east)."""
    pyl = ", ".join(f'[{st}] = {{ CLSID = "{w[1]["clsid"]}" }}' for st, w in cap_loadout().items())
    return (f'CAPCFG = {{ GROUP = "Chevy", CALL = "Chevy", CARRIER = "{carrier}", FLAG = "{flag}",\n'
            f'  STATION = {{ x = {station.x:.1f}, z = {station.y:.1f} }}, ALT = {20000 * 0.3048:.0f}, SPD = {420 * 1.852 / 3.6:.1f},\n'
            f'  FLEET_ONLY = {"true" if fleet_only else "false"}, BOAT_R = {boat_r},\n'
            f'  MIN_MISSILES = 2, BINGO = 0.25, ALERT_DELAY = {alert_delay}, ALERT_TRANSIT = {alert_transit},\n'
            + (f'  REQ = {{ x = {req.x:.1f}, z = {req.y:.1f} }}, REQ_LABEL = "{req_label}",\n' if req else "")
            + f'  PYLONS = {{ {pyl} }} }}\n')
