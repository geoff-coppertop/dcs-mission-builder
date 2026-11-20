"""Scenario tests for Operation Deep Cut: Escape, run against the built .miz with a mocked DCS API."""
import re
import sys
from testing.mockdcs import make, text, scripts_from_miz

PATH = sys.argv[1] if len(sys.argv) > 1 else "Operation_Deep_Cut_Escape.miz"
SCRIPTS = scripts_from_miz(PATH)
cfg = SCRIPTS[-1]
CARRIER = re.search(r'CARRIER = "([^"]+)"', cfg).group(1)
START = float(re.search(r"START = (\d+)", cfg).group(1))
DISCOVER = float(re.search(r"DISCOVER = (\d+)", cfg).group(1))
REACT = float(re.search(r"ALERT_REACT = (\d+)", cfg).group(1))
PX, PZ = (float(v) for v in re.search(r"PARK = \{ x = (-?[\d.]+), z = (-?[\d.]+) \}", cfg).groups())

SETUP = f"""
local M = MOCKSTATE
for _, g in ipairs({{ "Senaki Guns North", "Senaki Guns South", "Senaki SA-13" }}) do M.mkGroup(g, {{ M.mkUnit(g .. " 1", 0, 0) }}) end
M.mkGroup("Red South", {{ M.mkUnit("Red South 1", 5000, 40000), M.mkUnit("Red South 2", 5000, 40100) }})
M.mkGroup("Senaki Guard Car", {{ M.mkUnit("Senaki BRDM-2", 100, 100) }})
M.mkGroup("Chevy", {{ M.mkUnit("Chevy 1-1", -10000, -80000), M.mkUnit("Chevy 1-2", -10100, -80000) }})
M.mkGroup("{CARRIER}", {{ M.mkUnit("{CARRIER}", -20000, -300000) }})
M.carrierName = "{CARRIER}"
JET = M.player("Geoff", "Enfield 1-1", 0, 0, 270, 10)
"""


def run(name, body, check):
    L, M = make(START, SETUP, SCRIPTS)
    L.execute(f"local M = MOCKSTATE; local START, DISCOVER, REACT, PX, PZ = {START}, {DISCOVER}, {REACT}, {PX}, {PZ}\n" + body)
    t = text(M)
    opts = [M.opts[i] for i in range(1, len(M.opts) + 1)]
    try:
        check(L, M, t, opts)
    except AssertionError:
        print(f"\n===== FAILED: {name}\n{t}")
        raise
    print(f"ok  {name}")


def c_clean(L, M, t, opts):
    assert "Senaki Guns North:0=4" in opts                       # guards start on weapon hold
    assert "Wheels up" in t and "They've seen you (the takeoff)" in t
    assert not M.activated["Senaki Guard Car"]                       # airborne before anyone came
    assert "Senaki Guns North:0=2" in opts                       # and open fire once the jet is seen
    assert M.activated["Red South"] and "Chevy 1-1, commit" in t
    assert "OUTCOME: SUCCESS" in t and M.flags["90"] == 1 and "aboard in somebody else's Tomcat" in t
    assert "KESTREL is correct" in t and "intercept and identify" not in t and "Checked in with MAGIC" in t
run("Away before the guards, chased, checked in, home", """
M.advance(START + 300)
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.cmds["Escape/Check in with MAGIC (KESTREL)"]()
M.advance(START + 300 + 20 + REACT + 10)
JET.p = { x = -20000, y = 1500, z = -290000 }
M.advance(START + 300 + 20 + REACT + 20)
M.event({ id = world.event.S_EVENT_LAND, initiator = JET, place = M.carrier() })
""", c_clean)


def c_parked(L, M, t, opts):
    assert "Guards! Rifles up, at the ladder" in t
    assert M.activated["Senaki Guard Car"] and M.units["Senaki Guards 1"] is not None
    assert "OUTCOME: FAILURE" in t and "Captured on the ramp, still parked" in t and M.flags["90"] == 3
    assert not M.activated["Red South"]                  # it's over: no chase
run("Still parked when the guards come: captured", """
JET.p = { x = PX, y = 10, z = PZ }
M.advance(START + DISCOVER + REACT + 30)
""", c_parked)


def c_taxi_late(L, M, t, opts):
    assert "armoured car heading for the taxiway" in t and "Captured on the ramp, still on the taxiway" in t
    assert M.activated["Senaki Guard Car"] and M.tasks["Senaki Guard Car"].id == "Mission"
    g = M.units["Senaki Guards 1"]
    assert abs(g.p.x - (PX + 15)) < 1 and abs(g.p.z - (PZ + 12)) < 1        # at the empty parking spot
    assert M.flags["90"] == 3
run("Taxiing when the guards come, not airborne in time: captured", """
JET.p = { x = PX + 400, y = 10, z = PZ }
M.advance(START + DISCOVER + 65)
""", c_taxi_late)


def c_taxi_made_it(L, M, t, opts):
    assert "armoured car heading for the taxiway" in t and "Wheels up" in t
    assert "Captured" not in t and "OUTCOME" not in t and M.activated["Red South"]
    assert M.activated["Senaki Guard Car"]
run("Taxiing when the guards come, airborne inside the window: away", """
JET.p = { x = PX + 400, y = 10, z = PZ }
M.advance(START + DISCOVER + 30)
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + DISCOVER + REACT + 10)
""", c_taxi_made_it)


def c_water(L, M, t, opts):
    assert "OUTCOME: PARTIAL" in t and M.flags["90"] == 2
run("Down over the water", """
M.waterFn = function() return true end
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 200)
M.event({ id = world.event.S_EVENT_EJECTION, initiator = JET })
""", c_water)


def c_land(L, M, t, opts):
    assert "OUTCOME: FAILURE" in t and M.flags["90"] == 3
run("Down over land", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 200)
M.event({ id = world.event.S_EVENT_EJECTION, initiator = JET })
""", c_land)


def c_status(L, M, t, opts):
    assert "Not seen yet. Guards expected" in t
run("Status", "M.advance(START + 60); M.cmds['Escape/Status']()", c_status)

def c_intercept(L, M, t, opts):
    assert "Unknown Tomcat, 65 nm east of Mother" in t and "intercept and identify" in t
    task = M.tasks["Chevy"]
    assert task and task.id == "Mission"
    assert "Tally one Tomcat" in t and "OUTCOME: SUCCESS" in t and "Identified by CHEVY" in t
run("No check-in: CHEVY intercepts and identifies", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 30)
JET.p = { x = -20000, y = 1500, z = -180000 }
M.advance(START + 35)
local c = M.units["Chevy 1-1"]
c.p = { x = -20500, y = 1500, z = -181000 }
M.advance(START + 50)
JET.p = { x = -20000, y = 1500, z = -290000 }
M.advance(START + 55)
M.event({ id = world.event.S_EVENT_LAND, initiator = JET, place = M.carrier() })
""", c_intercept)


def c_silent(L, M, t, opts):
    assert "Chevy is committed on the unknown Tomcat; no CAP for the coast until it resets" in t
    assert "KESTREL is correct" in t and "free to work the MiGs" in t
    assert t.count("commit. two MiG-29s off Kutaisi") == 1          # only once the Tomcat is known
run("Silent: CHEVY stays on the unknown, the MiGs wait until you check in", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 30)
JET.p = { x = -20000, y = 1500, z = -180000 }
M.advance(START + 20 + REACT + 10)
M.cmds["Escape/Check in with MAGIC (KESTREL)"]()
M.advance(START + 20 + REACT + 20)
""", c_silent)


def c_divert(L, M, t, opts):
    assert "break off the coast. Divert: unknown Tomcat inbound" in t
    assert "Tally one Tomcat" in t
    assert t.count("commit. two MiG-29s off Kutaisi") == 2          # before the divert, and again after the ID
run("MiGs first; the unknown pulls CHEVY off them; the ID sends it back", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 20 + REACT + 10)
JET.p = { x = -20000, y = 1500, z = -180000 }
M.advance(START + 20 + REACT + 15)
M.units["Chevy 1-1"].p = { x = -20500, y = 1500, z = -181000 }
M.advance(START + 20 + REACT + 35)
""", c_divert)


def c_fleet(L, M, t, opts):
    assert "approaching the fleet's missile zone" in t and "ENGAGING. Birds away" in t and "Splash one" in t
    assert len(M.explosions) == 1
    assert "OUTCOME: FAILURE" in t and "Shot down by our own fleet" in t and M.flags["90"] == 3
run("Silent inside 20 nm: the fleet shoots", """
M.waterFn = function() return true end
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 30)
JET.p = { x = -20000, y = 1500, z = -270000 }
M.advance(START + 40)
JET.p = { x = -20000, y = 1500, z = -285000 }
M.advance(START + 70)
M.event({ id = world.event.S_EVENT_EJECTION, initiator = JET })
""", c_fleet)


def c_abort(L, M, t, opts):
    assert "Birds away" in t and "ABORT, ABORT" in t and "Splash one" not in t and len(M.explosions) == 0
    assert "OUTCOME: SUCCESS" in t
run("Checking in with missiles in the air aborts them", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 30)
JET.p = { x = -20000, y = 1500, z = -285000 }
M.advance(START + 40)
M.cmds["Escape/Check in with MAGIC (KESTREL)"]()
M.advance(START + 70)
M.event({ id = world.event.S_EVENT_LAND, initiator = JET, place = M.carrier() })
""", c_abort)


def c_ground_call(L, M, t, opts):
    assert "Nobody can hear you from the ground" in t and "KESTREL is correct" not in t
run("Check-in from the ramp does nothing", """
M.advance(START + 30)
M.cmds["Escape/Check in with MAGIC (KESTREL)"]()
""", c_ground_call)

print("ALL ESCAPE SCENARIOS PASSED")
