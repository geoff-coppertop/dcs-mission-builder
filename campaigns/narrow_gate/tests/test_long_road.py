"""Scenario tests for Operation Long Road's mission script (run against the built .miz)."""
import re
import sys
from testing.mockdcs import make, text, scripts_from_miz

SCRIPTS = scripts_from_miz(sys.argv[1] if len(sys.argv) > 1 else "Operation_Long_Road.miz")
cfg = SCRIPTS[-1]   # the mission script (CAPCFG, cap.lua and common.lua come first)
num = lambda k: float(re.search(rf"{k}\s*=\s*(-?[\d.]+)", cfg).group(1))
START, RESTART, MIG = num("START"), num("RESTART"), num("MIG_TIME")
CX, CZ = (float(v) for v in re.search(r"COVER = \{ x = (-?[\d.]+), z = (-?[\d.]+)", cfg).groups())

SETUP = """
local M = MOCKSTATE
local cols = {}
for i = 1, 10 do cols[i] = M.mkUnit("Column V" .. i, -230000 + i * 40, 590000 - i * 30) end
M.mkGroup("Column", cols)
M.mkGroup("Column AD", { M.mkUnit("Column SA-8", -229900, 590100), M.mkUnit("Column ZSU 1", -230100, 590000) })
M.mkGroup("Brigade SA-6", { M.mkUnit("SA-6 Straight Flush", -226000, 594000), M.mkUnit("SA-6 Launcher 1", -225800, 593800) })
M.mkGroup("Red CAP", { M.mkUnit("MiG 1", -190000, 560000) })
M.mkGroup("Pontiac", { M.mkUnit("Pontiac", -231000, 591000) })
M.mkGroup("Chevy", { M.mkUnit("Chevy 1-1", -280000, 540000) })
M.mkGroup("Colt", { M.mkUnit("Colt 1-1", -250000, 560000), M.mkUnit("Colt 1-2", -250500, 560000) })
LEAD = M.player("Geoff", "Enfield 1-1", -245000, 575000, 45)
WING = M.player("Wing", "Enfield 1-2", -246000, 574000, 45)
RX, RZ = -226000, 594000
"""


def run(name, body, check):
    L, M = make(START, SETUP, SCRIPTS)
    L.execute(f"local M = MOCKSTATE; local START, RESTART, MIG = {START}, {RESTART}, {MIG}\n" + body)
    t = text(M)
    try:
        check(L, M, t)
    except AssertionError:
        print(f"\n===== FAILED: {name}\n{t}")
        raise
    print(f"ok  {name}")
    return L, M, t


# 1. SEAD leads: column IN refused while SA-6 live; HARM hit suppresses 90 s and opens the window;
#    window closes; second HARM kills the radar (DEAD) and the column stays open.
def c1(L, M, t):
    assert "ABORT ABORT ABORT. SA-6 is LIVE" in t
    assert "ENFIELD 1-1: Magnum." in t and "SA-6 SUPPRESSED until" in t
    assert "Enfield 1-2, CLEARED HOT on the column. SA-6 SUPPRESSED" in t
    assert "Straight Flush is back up. SA-6 LIVE" in t
    assert "SA-6 is DEAD, the column is open" in t
    assert t.count("CLEARED HOT on the column") == 2
    assert "WITHOUT clearance" not in t and "went in with the SA-6 LIVE" not in t
    assert "Brigade SA-6:0=4" in [M.opts[i] for i in range(1, len(M.opts) + 1)]
run("SEAD window, then DEAD", """
M.advance(START + 1500)
M.cmds["Enfield 1-2/IN on column"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = LEAD, weapon = M.weapon(RX + 40, RZ, 30, "HARM") })
M.advance(START + 1535)
M.cmds["Enfield 1-2/IN on column"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = WING, weapon = M.weapon(-230000 + 80, 590000 - 60, 20) })
M.advance(START + 1640)                                -- suppression (90 s) has ended
M.event({ id = world.event.S_EVENT_SHOT, initiator = LEAD, weapon = M.weapon(RX, RZ, 25, "HARM") })
M.advance(START + 1664)
M.units["SA-6 Straight Flush"].alive = false             -- the second HARM kills it
M.advance(START + 1670)
M.cmds["Enfield 1-2/IN on column"]()
""", c1)


# 2. Uncleared release, and a column attack with the SA-6 live, are both flagged; BDA reports
def c2(L, M, t):
    assert "weapon release observed WITHOUT clearance" in t
    assert "that attack went in with the SA-6 LIVE" in t
    assert "BDA:" in t
run("Uncleared and no-SEAD attacks flagged", """
M.advance(START + 1500)
M.event({ id = world.event.S_EVENT_SHOT, initiator = WING, weapon = M.weapon(-230000 + 40, 590000 - 30, 20) })
M.advance(START + 1600)
""", c2)


# 3. Column restarts on time, gets a route, vehicles reaching cover escape and are removed
def c3(L, M, t):
    assert "The column is MOVING" in t and M.tasks["Column"] is not None and M.tasks["Column AD"] is not None
    assert "One vehicle into cover. 3 escaped." in t
    assert sum(1 for i in range(1, len(M.destroyed) + 1)) == 3
    assert "Expect it to move in 10 minutes" in t and "Two minutes" in t
run("Restart and escape", f"""
M.advance(RESTART + 10)
for i = 1, 3 do M.units["Column V" .. i].p.x = {CX}; M.units["Column V" .. i].p.z = {CZ} end
M.advance(RESTART + 30)
""", c3)


# 4. MiGs launch on time; MAGIC commits Chevy on its own; a request while busy is refused
def c4(L, M, t):
    assert M.activated["Red CAP"] and "two MiG-29s" in t
    assert M.flags["51"] is True and "Chevy 1-1, commit. Two MiG-29s out of Gudauta, heading for the column." in t
    assert "Negative, Chevy is committed on the column." in t
    assert M.tasks["Chevy"] is not None
run("MiGs and CAP", """
M.advance(MIG + 5)
M.cmds["Long Road/Request CAP cover"]()
""", c4)


# 5. Laser: on radar, on column with shift, stops when target gone
def c5(L, M, t):
    assert len(M.lasers) >= 2 and "Laser on the Straight Flush" in t and "Laser on the column" in t
    assert L.globals().RADAR_LASED and L.globals().SHIFTED
run("Laser targets", """
M.cmds["Pontiac laser/Laser on Straight Flush (1688)"]()
M.advance(START + 5)
RADAR_LASED = math.abs(M.lasers[1].pt.x - RX) < 5
M.cmds["Pontiac laser/Laser on column (1688)"]()
M.advance(START + 8)
local first = M.lasers[#M.lasers].pt.x
M.units["Column V1"].alive = false
M.advance(START + 10)
SHIFTED = M.lasers[#M.lasers].pt.x ~= first
""", c5)


# 6. Outcome grading + rescue pointer
def outcome(name, kills, escape, lose, expect):
    def c(L, M, t):
        assert "OUTCOME: " + expect in t, t[-600:]
        assert ("Operation_Sandy_Lift_Long_Road.miz" in t) == lose
        assert M.flags["90"] == {"SUCCESS": 1, "PARTIAL": 2, "FAILURE": 3}[expect]
    body = """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = LEAD })
M.advance(START + 1500)
"""
    for i in range(1, kills + 1):
        body += f'M.units["Column V{i}"].alive = false\n'
    body += f"M.advance(RESTART + 10)\n"
    for i in range(kills + 1, kills + 1 + escape):
        body += f'M.units["Column V{i}"].p.x = {CX}; M.units["Column V{i}"].p.z = {CZ}\n'
    body += "M.advance(RESTART + 40)\n"
    body += ('M.event({ id = world.event.S_EVENT_EJECTION, initiator = LEAD })\n' if lose else
             'M.event({ id = world.event.S_EVENT_LAND, initiator = LEAD, place = M.carrier() })\n')
    run("Outcome " + name, body, c)

outcome("success 7/10", 7, 3, False, "SUCCESS")
outcome("partial 5/10", 5, 5, False, "PARTIAL")
outcome("failure 2/10 + jet lost", 2, 8, True, "FAILURE")

COLT = "COLT = true" in cfg
if COLT:
    # 7. COLT: push once, its HARM hit opens the window, it is credited in the summary
    def c7(L, M, t):
        assert M.flags["53"] is True and "pushing on the Straight Flush" in t and "COLT: Already pushed." in t
        assert "COLT 1-1: Magnum." in t and "SA-6 SUPPRESSED until" in t
        assert "Enfield 1-2, CLEARED HOT on the column" in t
        assert "1 from COLT" in t and "COLT pushed at" in t
    run("COLT push opens the window", """
    M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = LEAD })
    M.advance(START + 1400)
    M.cmds["Long Road/PUSH COLT (SEAD)"]()
    M.cmds["Long Road/PUSH COLT (SEAD)"]()
    M.advance(START + 1580)
    M.event({ id = world.event.S_EVENT_SHOT, initiator = M.units["Colt 1-1"], weapon = M.weapon(RX + 30, RZ, 30, "HARM") })
    M.event({ id = world.event.S_EVENT_SHOT, initiator = M.units["Colt 1-1"], weapon = M.weapon(RX, RZ, 5, "AAM") })
    M.advance(START + 1615)
    M.cmds["Enfield 1-2/IN on column"]()
    M.advance(START + 1700)
    M.event({ id = world.event.S_EVENT_LAND, initiator = LEAD, place = M.carrier() })
    """, c7)

else:
    # 7b. Own SEAD: no COLT in the menu or the radio calls
    def c7b(L, M, t):
        assert "Long Road/PUSH COLT (SEAD)" not in [k for k in M.cmds.keys()], "no COLT menu without COLT"
        assert "your own HARMs, no COLT today" in t
    run("Own SEAD: no COLT", """
M.advance(START + 10)
""", c7b)

print("\nALL LONG ROAD SCENARIOS PASSED")
