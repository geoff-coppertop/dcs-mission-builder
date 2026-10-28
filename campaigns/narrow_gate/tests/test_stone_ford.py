"""Scenario tests for Operation Stone Ford (both variants)."""
import re
import sys
from testing.mockdcs import make, text, scripts_from_miz

FILES = sys.argv[1:] or ["Operation_Stone_Ford.miz", "Operation_Stone_Ford_Hard.miz"]


def suite(path):
    SCRIPTS = scripts_from_miz(path)
    cfg = SCRIPTS[-1]   # the mission script (CAPCFG, cap.lua and common.lua come first)
    START = float(re.search(r"START = (\d+)", cfg).group(1))
    BX, BZ = (float(v) for v in re.search(r"BRIDGE = \{ x = (-?[\d.]+), z = (-?[\d.]+)", cfg).groups())
    waves = re.findall(r'group = "(Wave \d+)", time = (\d+)', cfg)
    MIG = float(re.search(r"MIG_TIME = (\d+)", cfg).group(1))
    W1T = float(waves[0][1])
    setup = f"""
local M = MOCKSTATE
BX, BZ = {BX}, {BZ}
local blues = {{}}
for i = 1, 6 do blues[i] = M.mkUnit("Bridgehead " .. i, BX + 300 + i * 20, BZ - 300) end
M.mkGroup("Bridgehead", blues)
M.mkGroup("Axeman", {{ M.mkUnit("Axeman", BX + 600, BZ - 350) }})
"""
    for gi, (g, _) in enumerate(waves):
        units = ", ".join(f'M.mkUnit("{g} {j}", BX + 6000 + {gi} * 500 + {j} * 70, BZ - 4500)' for j in range(1, 5))
        setup += f'M.mkGroup("{g}", {{ {units} }})\n'
    setup += """
M.mkGroup("Red CAP", { M.mkUnit("MiG", BX + 60000, BZ - 60000) })
M.mkGroup("Chevy", { M.mkUnit("Chevy 1-1", BX - 60000, BZ - 90000) })
LEAD = M.player("Geoff", "Enfield 1-1", BX + 2000, BZ - 12000, 45)     -- ~6.6 nm from Axeman, heading 045
WING = M.player("Wing", "Enfield 1-2", BX + 1500, BZ - 12500, 45)
"""
    total = 4 * len(waves)
    LOST_AT = int(re.search(r"LOST_AT = (\d+)", cfg).group(1))

    def run(name, body, check):
        L, M = make(START, setup, SCRIPTS)
        L.execute(f"local M = MOCKSTATE; local START, W1, MIG = {START}, {W1T}, {MIG}\n" + body)
        t = text(M)
        try:
            check(L, M, t)
        except AssertionError:
            print(f"\n===== FAILED [{path}]: {name}\n{t}")
            raise
        print(f"ok  [{path.split('_', 2)[-1]}] {name}")

    FLOW = """
M.advance(W1 + 5)
M.cmds["JTAC Axeman/1. Check in"]()
M.advance(W1 + 10)
M.cmds["JTAC Axeman/2. Ready to copy 9-line"]()
M.cmds["JTAC Axeman/3. Read back 4, 6, restrictions"]()
M.advance(W1 + 15)
"""

    def c1(L, M, t):
        assert M.activated["Wave 1"] and "Wave 1 is moving, 4 vehicles" in t
        for s in ["checking in", "GAME PLAN: Type 1 control", "9-line follows, target Wave 1", "Readback correct",
                  "I have you in sight. CLEARED HOT on Wave 1", "Laser on, code 1688", "Copy spot", "BDA:", "direct hit"]:
            assert s in t, s
        assert "WITHOUT clearance" not in t and "CEASE FIRE" not in t and "DANGER CLOSE" not in t
    run("Full Type 1 flow", FLOW + """
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.cmds["Enfield 1-1/Ten seconds (laser on)"]()
M.advance(W1 + 17)
M.cmds["Enfield 1-1/Spot"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = LEAD, weapon = M.weapon(BX + 6070, BZ - 4500, 25) })
M.advance(W1 + 70)
""", c1)

    def c2(L, M, t):
        assert "No readback for the current 9-line" in t
        assert "outside final attack heading" in t
        assert "CONTINUE. No joy" in t
        assert t.count("CLEARED HOT") == 0
    run("Abort / continue cases", """
M.advance(W1 + 5)
M.cmds["Enfield 1-1/IN (heading auto)"]()                      -- no 9-line / readback
M.cmds["JTAC Axeman/1. Check in"]()
M.advance(W1 + 10)
M.cmds["JTAC Axeman/2. Ready to copy 9-line"]()
M.cmds["JTAC Axeman/3. Read back 4, 6, restrictions"]()
M.cmds["JTAC Axeman/2. Ready to copy 9-line"]()               -- new 9-line voids the readback
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.cmds["JTAC Axeman/3. Read back 4, 6, restrictions"]()
LEAD.hdg = 135
M.cmds["Enfield 1-1/IN (heading auto)"]()                      -- toward the village
LEAD.hdg = 45; LEAD.p.x = BX + 2000; LEAD.p.z = BZ - 25000      -- ~13 nm out
M.cmds["Enfield 1-1/IN (heading auto)"]()
""", c2)

    def c3(L, M, t):
        assert "DANGER CLOSE, my initials WH" in t and "danger close, initials WH" in t
        assert "TROOPS IN CONTACT with Wave 1" in t
        assert "Wave 1:0=2" in [M.opts[i] for i in range(1, len(M.opts) + 1)]
    run("Danger close and contact", """
M.advance(W1 + 5)
for j = 1, 4 do M.units["Wave 1 " .. j].p.x = BX + 1300 + j * 30; M.units["Wave 1 " .. j].p.z = BZ - 300 end    -- ~900 m from the village line
M.advance(W1 + 10)
M.cmds["JTAC Axeman/1. Check in"]()
M.advance(W1 + 15)
M.cmds["JTAC Axeman/2. Ready to copy 9-line"]()
M.cmds["JTAC Axeman/3. Read back 4, 6, restrictions"]()
""", c3)

    def c4(L, M, t):
        assert "CEASE FIRE, CEASE FIRE" in t and "FRATRICIDE: 1 impact" in t and "OUTCOME: PARTIAL" in t
    run("Fratricide", FLOW + """
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = LEAD })
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = LEAD, weapon = M.weapon(BX + 330, BZ - 300, 20) })
M.advance(W1 + 60)
for _, g in ipairs({ "Wave 1", "Wave 2", "Wave 3", "Wave 4" }) do
  if M.groups[g] then for _, u in ipairs(M.groups[g].units) do u.alive = false end end
end
M.event({ id = world.event.S_EVENT_LAND, initiator = LEAD, place = M.carrier() })
""", c4)

    hard = 'CAP_MODE = "fleet"' in cfg
    def c5(L, M, t):
        assert M.activated["Red CAP"]
        if hard:
            assert M.flags["51"] is None and "stays on fleet defence" in t and "You are on your own" in t
            assert "Negative. CAG has Chevy on fleet defence." in t
        else:
            assert M.flags["51"] is True and "Chevy 1-1, commit. Red fighters heading for the Inguri." in t
            assert "Negative, Chevy is committed on the Inguri." in t
    run("MiGs and CAP", """
M.advance(MIG + 5)
M.cmds["Stone Ford/Request CAP cover"]()
""", c5)

    def outcome(name, through, alive_left, lose, expect):
        def c(L, M, t):
            assert "OUTCOME: " + expect in t, t[-700:]
            assert ("Operation_Sandy_Lift_Inguri.miz" in t) == lose
            if through:
                assert f"{through} through" in t or "THROUGH the line" in t
        body = "M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = LEAD })\n"
        body += "M.advance(START + 3600)\n"     # all waves active
        body += f"local moved = 0\nfor _, g in ipairs({{ {', '.join(repr(w[0]).replace(chr(39), chr(34)) for w in waves)} }}) do\n"
        body += f"""  for _, u in ipairs(M.groups[g].units) do
    if moved < {through} then u.p.x = BX + 100; u.p.z = BZ; moved = moved + 1
    elseif moved < {through} + {alive_left} then moved = moved + 1
    else u.alive = false end
  end
end
M.advance(START + 3610)
"""
        body += ('M.event({ id = world.event.S_EVENT_EJECTION, initiator = LEAD })\n' if lose else
                 'M.event({ id = world.event.S_EVENT_LAND, initiator = LEAD, place = M.carrier() })\n')
        run("Outcome " + name, body, c)

    outcome("held (1 through)", 1, 0, False, "SUCCESS")
    outcome("held at cost (2 through)", 2, 0, False, "PARTIAL")
    outcome(f"lost ({LOST_AT} through)", LOST_AT, 0, False, "FAILURE")
    outcome("lost via survivors still advancing + jet lost", 1, 2, True, "FAILURE")


for f in FILES:
    suite(f)
print("\nALL STONE FORD SCENARIOS PASSED")
