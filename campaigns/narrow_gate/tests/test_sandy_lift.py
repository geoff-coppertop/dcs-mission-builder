"""Scenario tests for Operation Sandy Lift."""
import re
import sys
from testing.mockdcs import make, text, scripts_from_miz

SCRIPTS = scripts_from_miz(sys.argv[1] if len(sys.argv) > 1 else "Operation_Sandy_Lift.miz")
cfg = SCRIPTS[-1]   # the mission script (CAPCFG, cap.lua and common.lua come first)
START = float(re.search(r"START = (\d+)", cfg).group(1))
SEARCH = float(re.search(r"SEARCH_TIME = (\d+)", cfg).group(1))
MIG = float(re.search(r"MIG_TIME = (\d+)", cfg).group(1))
AD = re.search(r'THREAT_GROUPS = \{ "([^"]+)"', cfg).group(1)
MIGK = re.search(r'MIG_KIND = "([^"]+)"', cfg).group(1)
LX, LZ_ = (float(v) for v in re.search(r"LZ = \{ x = (-?[\d.]+), z = (-?[\d.]+)", cfg).groups())

SETUP = f"""
local M = MOCKSTATE
LX, LZZ = {LX}, {LZ_}
ADG = "{AD}"
M.mkGroup("Survivor", {{ M.mkUnit("Survivor", LX, LZZ) }})
M.mkGroup("{AD}", {{ M.mkUnit("Depot SA-13", LX + 1000, LZZ + 3300, "Strela-10M3"),
                          M.mkUnit("Depot ZSU South", LX - 500, LZZ + 3000, "ZSU-23-4 Shilka") }})
M.mkGroup("Search Party", {{ M.mkUnit("Search BTR-80", LX - 4300, LZZ + 1300, "BTR-80"),
                             M.mkUnit("Search Igla", LX - 4320, LZZ + 1320, "SA-18 Igla manpad") }})
M.mkGroup("Dodge", {{ M.mkUnit("Dodge 1-1", LX - 3000, LZZ - 26000, "SH-60B") }})
M.units["Dodge 1-1"].p.y = 150
M.mkGroup("Red CAP", {{ M.mkUnit("MiG", LX + 40000, LZZ - 40000) }})
M.mkGroup("Pontiac", {{ M.mkUnit("Pontiac", LX + 500, LZZ + 1000) }})
M.mkGroup("Chevy", {{ M.mkUnit("Chevy 1-1", LX - 40000, LZZ - 60000) }})
LEAD = M.player("Geoff", "Enfield 1-1", LX - 5000, LZZ - 10000, 60)
WING = M.player("Wing", "Enfield 1-2", LX - 5500, LZZ - 10500, 60)
function KILL(g) for _, u in ipairs(M.groups[g].units) do u.alive = false end end
function HELO_AT_LZ() local h = M.units["Dodge 1-1"]; h.p.x, h.p.z, h.p.y = LX + 60, LZZ + 40, 13 end
"""


def run(name, body, check):
    L, M = make(START, SETUP, SCRIPTS)
    L.execute(f"local M = MOCKSTATE; local START, SEARCH, MIG = {START}, {SEARCH}, {MIG}\n" + body)
    t = text(M)
    try:
        check(L, M, t)
    except AssertionError:
        print(f"\n===== FAILED: {name}\n{t}")
        raise
    print(f"ok  {name}")


TAKEOFF = """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = LEAD })
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = WING })
"""
TRAP = """
M.event({ id = world.event.S_EVENT_LAND, initiator = LEAD, place = M.carrier() })
M.event({ id = world.event.S_EVENT_LAND, initiator = WING, place = M.carrier() })
"""


def c1(L, M, t):
    assert M.tasks["Search Party"] is not None and "search party moving toward the survivor" in t
    assert "be advised, 4 threats".lower() in t.lower() or "Be advised, 4 threats" in t
    assert M.flags["52"] is True and "Already committed" in t
    assert "Wheels down at the survivor" in t and "Survivor aboard!" in t and "Dodge is aboard with the survivor" in t
    assert "OUTCOME: SUCCESS" in t and "survivor RESCUED" in t
    assert M.flags["92"] == 1
    assert t.index("Dodge is aboard with the survivor") < t.index("MISSION SUMMARY")
run("Rescue: called with threats, pickup, home, summary waits for both", TAKEOFF + """
M.advance(SEARCH + 5)
M.cmds["Sandy Lift/CALL IN DODGE (rescue helo)"]()
M.cmds["Sandy Lift/CALL IN DODGE (rescue helo)"]()
M.advance(SEARCH + 400)
HELO_AT_LZ()
M.advance(SEARCH + 405)
M.advance(SEARCH + 450)
""" + TRAP + """
M.advance(SEARCH + 900)
M.event({ id = world.event.S_EVENT_LAND, initiator = M.units["Dodge 1-1"], place = M.carrier() })
""", c1)


def c2(L, M, t):
    assert "thanks for the clean LZ" in t
    assert "LZ is clean" in t and "Search party destroyed" in t
run("Clean LZ call", """
M.advance(SEARCH + 60)
KILL(ADG); KILL("Search Party")
M.cmds["Sandy Lift/Pontiac: LZ report"]()
M.cmds["Sandy Lift/CALL IN DODGE (rescue helo)"]()
""", c2)


def c3(L, M, t):
    assert "He's been taken. Rescue is OFF." in t and "OUTCOME: FAILURE" in t and "search party reached the survivor first" in t
    assert M.flags["92"] == 0
run("Capture", TAKEOFF + """
M.advance(SEARCH + 60)
M.units["Search BTR-80"].p.x, M.units["Search BTR-80"].p.z = LX + 200, LZZ
M.advance(SEARCH + 70)
""" + TRAP, c3)


def c4(L, M, t):
    assert "Dodge 1-1 is down" in t and "OUTCOME: FAILURE" in t and "Dodge was shot down" in t
    assert "Survivor aboard!" not in t
run("Helo lost during boarding", TAKEOFF + """
M.advance(SEARCH + 10)
M.cmds["Sandy Lift/CALL IN DODGE (rescue helo)"]()
M.advance(SEARCH + 400)
HELO_AT_LZ()
M.advance(SEARCH + 410)
M.units["Dodge 1-1"].alive = false
M.event({ id = world.event.S_EVENT_DEAD, initiator = M.units["Dodge 1-1"] })
M.advance(SEARCH + 460)
""" + TRAP, c4)


def c5(L, M, t):
    assert len(M.lasers) == 1 and "Laser on the nearest threat to the LZ, Strela-10M3" in t or "Laser on the nearest threat" in t
    assert M.smoke == 1 and "Green smoke out" in t
    assert M.activated["Red CAP"] and f"two {MIGK} out of Gudauta" in t
    assert f"Chevy 1-1, commit. Two {MIGK} heading for the survivor's area." in t and M.flags["51"] is True
run("Laser, smoke, MiGs", """
M.cmds["Pontiac laser/Laser on nearest threat (1688)"]()
M.cmds["Sandy Lift/Survivor: pop green smoke"]()
M.advance(MIG + 5)
""", c5)


def c6(L, M, t):
    assert "OUTCOME: FAILURE" in t and "Dodge never made the pickup" in t
run("Forced summary with no pickup", """
M.advance(START + 600)
M.cmds["Sandy Lift/Mission summary now"]()
""", c6)

print("\nALL SANDY LIFT SCENARIOS PASSED")
