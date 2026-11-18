"""Scenario tests for Operation Deep Cut: Escape, run against the built .miz with a mocked DCS API."""
import re
import sys
from testing.mockdcs import make, text, scripts_from_miz

PATH = sys.argv[1] if len(sys.argv) > 1 else "Operation_Deep_Cut_Escape.miz"
SCRIPTS = scripts_from_miz(PATH)
cfg = SCRIPTS[-1]
START = float(re.search(r"START = (\d+)", cfg).group(1))
DISCOVER = float(re.search(r"DISCOVER = (\d+)", cfg).group(1))
REACT = float(re.search(r"ALERT_REACT = (\d+)", cfg).group(1))

SETUP = """
local M = MOCKSTATE
for _, g in ipairs({ "Senaki Guns North", "Senaki Guns South", "Senaki SA-13" }) do M.mkGroup(g, { M.mkUnit(g .. " 1", 0, 0) }) end
M.mkGroup("Red South", { M.mkUnit("Red South 1", 5000, 40000), M.mkUnit("Red South 2", 5000, 40100) })
M.mkGroup("Chevy", { M.mkUnit("Chevy 1-1", -10000, -80000), M.mkUnit("Chevy 1-2", -10100, -80000) })
M.mkGroup("CVN-74 Stennis", { M.mkUnit("CVN-74 Stennis", -20000, -120000) })
JET = M.player("Geoff", "Enfield 1-1", 0, 0, 270, 10)
"""


def run(name, body, check):
    L, M = make(START, SETUP, SCRIPTS)
    L.execute(f"local M = MOCKSTATE; local START, DISCOVER, REACT = {START}, {DISCOVER}, {REACT}\n" + body)
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
    assert "Senaki Guns North:0=2" in opts                       # and open fire once the jet is seen
    assert M.activated["Red South"] and "Chevy 1-1, commit" in t
    assert "OUTCOME: SUCCESS" in t and M.flags["90"] == 1 and "aboard in somebody else's Tomcat" in t
    assert "KESTREL is correct" in t and "intercept and identify" not in t and "Checked in with MAGIC" in t
run("Away before the guards, chased, checked in, home", """
M.advance(START + 300)
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.cmds["Escape/Check in with MAGIC (KESTREL)"]()
M.advance(START + 300 + 20 + REACT + 10)
JET.p = { x = -20000, y = 1500, z = -110000 }
M.advance(START + 300 + 20 + REACT + 20)
M.event({ id = world.event.S_EVENT_LAND, initiator = JET, place = M.carrier() })
""", c_clean)


def c_slow(L, M, t, opts):
    assert "They've seen you (a guard on his rounds)" in t
    assert not M.activated["Red South"]
    M.flags  # fighters are 90 s behind the discovery
run("Too slow on the ramp", "M.advance(START + DISCOVER + 5)", c_slow)


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
    assert "Unknown Tomcat, 32 nm east of Mother" in t and "intercept and identify" in t
    task = M.tasks["Chevy"]
    assert task and task.id == "Mission"
    assert "Tally one Tomcat" in t and "OUTCOME: SUCCESS" in t and "Identified by CHEVY" in t
run("No check-in: CHEVY intercepts and identifies", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 30)
JET.p = { x = -20000, y = 1500, z = -60000 }
M.advance(START + 35)
local c = M.units["Chevy 1-1"]
c.p = { x = -20500, y = 1500, z = -61000 }
M.advance(START + 50)
JET.p = { x = -20000, y = 1500, z = -110000 }
M.advance(START + 55)
M.event({ id = world.event.S_EVENT_LAND, initiator = JET, place = M.carrier() })
""", c_intercept)


def c_recommit(L, M, t, opts):
    assert "break off the unknown Tomcat" in t and "Chevy is busy with the MiGs" in t
    assert "back to the unknown Tomcat" in t and "Tally one Tomcat" in t
run("MiGs pull CHEVY off; it comes back for the ID", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 30)
JET.p = { x = -20000, y = 1500, z = -60000 }
M.advance(START + REACT + 25)
M.units["Red South 1"].alive = false; M.units["Red South 2"].alive = false
M.advance(START + REACT + 25 + 75)
M.units["Chevy 1-1"].p = { x = -20500, y = 1500, z = -61000 }
M.advance(START + REACT + 25 + 95)
""", c_recommit)


def c_unknown_trap(L, M, t, opts):
    assert "you are NOT cleared" in t and "trapped without clearance" in t
    assert "OUTCOME: PARTIAL" in t and "Never identified" in t
run("Trap without being identified", """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = JET })
M.advance(START + 60)
JET.p = { x = -20000, y = 1500, z = -112000 }
M.advance(START + 70)
M.event({ id = world.event.S_EVENT_LAND, initiator = JET, place = M.carrier() })
""", c_unknown_trap)


def c_ground_call(L, M, t, opts):
    assert "Nobody can hear you from the ground" in t and "KESTREL is correct" not in t
run("Check-in from the ramp does nothing", """
M.advance(START + 30)
M.cmds["Escape/Check in with MAGIC (KESTREL)"]()
""", c_ground_call)

print("ALL ESCAPE SCENARIOS PASSED")
