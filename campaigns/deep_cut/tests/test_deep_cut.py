"""Scenario tests for Operation Deep Cut (both variants), run against the built .miz with a mocked DCS API."""
import re
import sys
from testing.mockdcs import make, text, scripts_from_miz

FILES = sys.argv[1:] or ["Operation_Deep_Cut.miz", "Operation_Deep_Cut_Hard.miz", "Operation_Deep_Cut_SC.miz", "Operation_Deep_Cut_Hard_SC.miz"]


def num(cfg, key):
    return float(re.search(rf"\b{key} = (-?[\d.]+)", cfg).group(1))


def suite(path):
    SCRIPTS = scripts_from_miz(path)
    cfg = SCRIPTS[-1]
    V = {k: num(cfg, k) for k in ("START", "TOT", "WINDOW", "HAMMER", "REPAIR", "SAM_UP", "REACT", "KILL_WINDOW",
                                  "FLOOR_FT", "GRACE", "DET_R", "POP_R", "ALERT_REACT", "PUSH_T")}
    CARRIER = re.search(r'CARRIER = "([^"]+)"', cfg).group(1)
    TX, TZ = (float(v) for v in re.search(r"TGT = \{ x = (-?[\d.]+), z = (-?[\d.]+)", cfg).groups())
    hard = "(HARD)" in cfg
    # A V-shaped gorge running NE-SW, its floor 800 m south-east of the planned target point:
    # 600 m of climb per km off the floor, the floor itself rising gently upstream.
    terrain = f"""
local M = MOCKSTATE
local OX, OZ = {TX} - 566, {TZ} + 566
local UX, UZ = 0.7071, 0.7071
M.heightFn = function(x, z)
  local dx, dz = x - OX, z - OZ
  local along = dx * UX + dz * UZ
  local off = math.abs(-dx * UZ + dz * UX)
  return 700 + 0.02 * along + 0.6 * math.min(off, 2500)
end
FLOOR_OFF = function(x, z) local dx, dz = x - OX, z - OZ return math.abs(-dx * UZ + dz * UX) end
"""
    setup = terrain + f"""
M.mkGroup("Red South", {{ M.mkUnit("Red South 1", {TX} - 70000, {TZ} + 30000), M.mkUnit("Red South 2", {TX} - 70000, {TZ} + 30100) }})
M.mkGroup("Red North", {{ M.mkUnit("Red North 1", {TX} + 25000, {TZ} + 20000) }})
-- players start far out at sea, well outside the radar-floor zone
M.mkGroup("Chevy", {{ M.mkUnit("Chevy 1-1", {TX} - 100000, {TZ} - 100000), M.mkUnit("Chevy 1-2", {TX} - 100100, {TZ} - 100000) }})
M.mkGroup("{CARRIER}", {{ M.mkUnit("{CARRIER}", {TX} - 150000, {TZ} - 150000) }})
M.carrierName = "{CARRIER}"
LEAD = M.player("Geoff", "Enfield 1-1", {TX} - 90000, {TZ} - 90000, 45, 1000)
WING = M.player("Wing", "Enfield 1-2", {TX} - 90100, {TZ} - 90000, 45, 1000)
"""

    def run(name, body, check):
        L, M = make(V["START"], setup, SCRIPTS)
        L.execute("local M = MOCKSTATE\n" + "\n".join(f"local {k} = {v}" for k, v in V.items()) + "\n" + body)
        t = text(M)
        try:
            check(L, M, t)
        except AssertionError:
            print(f"\n===== FAILED [{path}]: {name}\n{t}")
            raise
        print(f"ok  [{'hard' if hard else 'standard'}] {name}")

    # drop a bomb from `who` that lands `dx` m north of the portal at absolute time `at`
    BOMB = """
function bomb(who, at, dx, dz)
  M.advance(at - 10)
  local tg = DC.s.tgt
  M.event({ id = world.event.S_EVENT_SHOT, initiator = who, weapon = M.weapon(tg.x + (dx or 0), tg.z + (dz or 0), 10) })
end
function launch() M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = LEAD }); M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = WING }) end
function trap(u) M.event({ id = world.event.S_EVENT_LAND, initiator = u, place = M.carrier() }) end
"""

    def c_snap(L, M, t):
        d = L.globals().DC.s
        portal = M.statics["Portal"]
        floor_off = L.globals().FLOOR_OFF
        assert floor_off(portal.x, portal.y) < 120, floor_off(portal.x, portal.y)
        assert ((portal.x - TX) ** 2 + (portal.y - TZ) ** 2) ** 0.5 > 500       # moved off the planned point
        sams = [s for s in d.spawned.values() if s.kind == "sam"]
        valley = [s for s in d.spawned.values() if s.kind == "valley"]
        assert len(sams) == 2 and len(valley) == 3, (len(sams), len(valley))
        for s in sams:
            assert s.at.y > 1200, s.at.y          # on the high ground, not the floor
        assert "TARGET: blast door" in t and "MGRS" in t
        assert any("PORTAL (gorge floor" in M.marks[i].text for i in range(1, len(M.marks) + 1))
        team = M.units["Hatchet"]
        assert team is not None and L.globals().land.getHeight({"x": team.p.x, "y": team.p.z}) > d.tgt.y + 300
        assert "Hatchet:SetInvisible" in [M.opts[i] for i in range(1, len(M.opts) + 1)]
        opts = [M.opts[i] for i in range(1, len(M.opts) + 1)]
        assert any(o.startswith("Climb-out") and o.endswith("=4") for o in opts)     # SAMs start on weapon hold
    run("Target and sites placed on DCS terrain", "M.advance(START + 10)", c_snap)

    def c_textbook(L, M, t):
        for s in ["HAMMER: TLAMs impacting the sector air defence command post", "Chevy 1-1, commit", "Shack! The blast door is down. Breach ON TIME",
                  "Through the portal! Secondaries", "TARGET DESTROYED", "climb-out SAMs are UP (bombs on the portal)",
                  "Target 40/40", "Timing 20/20", "Survival 40/40: 2 of 2 jets home",
                  "SCORE 100/100: TEXTBOOK", "Kutaisi has fighter control back on the backup radar", "CAP: Chevy committed"]:
            assert s in t, s
        assert "you're above the floor" not in t and "Red's radar" not in t
        assert M.flags["90"] == 1 and M.flags["92"] == 100
        assert M.activated["Red South"] and not M.activated["Red North"]
        assert "Also fly" not in t and M.flags["91"] is False
        assert len(M.explosions) == 2
    run("On time, unseen, breach and kill, all home", BOMB + """
launch()
bomb(LEAD, TOT, 4, 3)
bomb(WING, TOT + 12, -5, 2)
M.advance(HAMMER + REPAIR + 5)
trap(LEAD); trap(WING)
""", c_textbook)

    def c_detected(L, M, t):
        assert "Red's radar has the package" in t and "expect the Kutaisi alert too" in t
        assert "climb-out SAMs are UP (package detected)" in t
        assert M.activated["Red North"] and M.activated["Red South"]
        assert "Timing 12/20" in t and "package detected" in t
        assert ("you're above the floor" in t) == (not hard)
    run("Seen above the floor before HAMMER", BOMB + """
launch()
M.advance(TOT - 600)
local tg = DC.s.tgt
LEAD.p = { x = tg.x - (POP_R + DET_R) / 2, y = 0, z = tg.z }
LEAD.p.y = land.getHeight({ x = LEAD.p.x, y = LEAD.p.z }) + (FLOOR_FT + 200) * 0.3048
M.advance(TOT - 600 + GRACE + 2)
LEAD.p = { x = tg.x - 90000, y = 1000, z = tg.z - 90000 }
M.advance(TOT - 600 + GRACE + ALERT_REACT + 5)
bomb(LEAD, TOT, 0, 0)
bomb(LEAD, TOT + 1, 1, 1)
M.advance(TOT + 30)
trap(LEAD); trap(WING)
""", c_detected)

    def c_pop(L, M, t):
        assert "you're above the floor" not in t and "Red's radar" not in t and "SAMs are UP" not in t
    run("Pop-up inside the attack zone is not seen", BOMB + """
launch()
M.advance(TOT - 60)
local tg = DC.s.tgt
LEAD.p = { x = tg.x - POP_R + 1500, y = 0, z = tg.z }
LEAD.p.y = land.getHeight({ x = LEAD.p.x, y = LEAD.p.z }) + 3000 * 0.3048
M.advance(TOT - 30)
""", c_pop)

    def c_water(L, M, t):
        assert "you're above the floor" not in t and "Red's radar" not in t
    run("Over the reservoir the floor counts from the water, not the bed", BOMB + """
launch()
M.advance(TOT - 600)
local tg = DC.s.tgt
M.surfaceFn = function(x, z) return land.getHeight({ x = x, y = z }) + 400 end     -- 400 m of water
LEAD.p = { x = tg.x - (POP_R + DET_R) / 2, y = 0, z = tg.z }
LEAD.p.y = land.getHeight({ x = LEAD.p.x, y = LEAD.p.z }) + 400 + (FLOOR_FT - 150) * 0.3048
M.advance(TOT - 600 + GRACE + 3)
""", c_water)

    def c_dam(L, M, t):
        assert "you're above the floor" not in t and "Red's radar" not in t
    run("Crossing the dam crest is measured from the crest", BOMB + """
launch()
M.advance(TOT - 600)
local tg = DC.s.tgt
local cx, cz = tg.x - (POP_R + DET_R) / 2, tg.z
local base = M.heightFn
M.heightFn = function(x, z)                                -- a 250 m wall just ahead of the jet
  if x > cx + 90 and x < cx + 160 then return base(x, z) + 250 end
  return base(x, z)
end
LEAD.p = { x = cx, y = base(cx, cz) + 250 + (FLOOR_FT - 150) * 0.3048, z = cz }
M.advance(TOT - 600 + GRACE + 3)
""", c_dam)

    def c_push(L, M, t):
        assert "five minutes to push. Hold at PUSH" in t and "FEET DRY, 3000" in t
        assert "Enfield, one minute to push" in t and "Enfield, PUSH PUSH" in t and "Springfield" not in t
    run("MAGIC calls the push", "M.advance(PUSH_T + 60)", c_push)

    if not hard:
        def c_warn(L, M, t):
            assert "Enfield 1-1, you're above the floor" in t and "Red's radar" not in t
        run("A moment above the floor is a warning, not a detection", BOMB + """
launch()
M.advance(TOT - 600)
local tg = DC.s.tgt
LEAD.p = { x = tg.x - (POP_R + DET_R) / 2, y = 0, z = tg.z }
LEAD.p.y = land.getHeight({ x = LEAD.p.x, y = LEAD.p.z }) + (FLOOR_FT + 200) * 0.3048
M.advance(TOT - 600 + 1.5)
LEAD.p.y = land.getHeight({ x = LEAD.p.x, y = LEAD.p.z }) + (FLOOR_FT - 200) * 0.3048
M.advance(TOT - 500)
""", c_warn)

    def c_late(L, M, t):
        assert "Window closed, no breach" in t and "Breach LATE" in t
        assert "climb-out SAMs are UP (Red alerted by HAMMER)" in t
        assert "Timing 8/20" in t and "SCORE 88/100: SUCCESS" in t
    run("Late breach", BOMB + """
launch()
bomb(LEAD, TOT + SAM_UP + 20, 0, 0)
bomb(WING, TOT + SAM_UP + 40, 0, 0)
M.advance(TOT + SAM_UP + 60)
trap(LEAD); trap(WING)
""", c_late)

    def c_early(L, M, t):
        assert "Breach EARLY" in t and "Bombs on the gorge before HAMMER took out their fighter control" in t
        assert M.activated["Red South"]
    run("Early, before HAMMER", BOMB + """
launch()
bomb(LEAD, HAMMER - 30, 0, 0)
M.advance(HAMMER - 25)
""", c_early)

    def c_sealed(L, M, t):
        assert "The portal is sealed" in t and "TARGET DESTROYED" not in t
        assert "Target 15/40" in t and "SCORE 75/100: PARTIAL" in t     # no kill, no SUCCESS
        assert M.flags["90"] == 3
    run("Breach, but the kill comes too late", BOMB + """
launch()
bomb(LEAD, TOT, 0, 0)
bomb(WING, TOT + KILL_WINDOW + 3, 0, 0)
M.advance(TOT + KILL_WINDOW + 10)
trap(LEAD); trap(WING)
""", c_sealed)

    def c_miss(L, M, t):
        assert "Miss, 60 m north of the blast door. Door still up." in t
        assert "Miss, 40 m off the portal" in t and "TARGET DESTROYED" in t
    run("Misses are called, then the kill", BOMB + """
launch()
bomb(LEAD, TOT - 5, 60, 0)
bomb(LEAD, TOT, 0, 0)
bomb(WING, TOT + 10, 40, 0)
bomb(WING, TOT + 20, 0, 0)
M.advance(TOT + 40)
""", c_miss)

    def c_loss(L, M, t):
        assert "Survival 20/40: 1 of 2 jets home (Wing ejected)" in t and "SCORE 80/100: SUCCESS" in t
    run("One jet lost on the way out", BOMB + """
launch()
bomb(LEAD, TOT, 0, 0)
bomb(LEAD, TOT, 2, 2)
M.advance(TOT + 200)
M.event({ id = world.event.S_EVENT_EJECTION, initiator = WING })
trap(LEAD)
""", c_loss)

    def c_divert(L, M, t):
        assert "Wing is down safe at Senaki-Kolkhi" in t and "Survival 40/40" in t
    run("A divert counts as home", BOMB + """
launch()
bomb(LEAD, TOT, 0, 0)
bomb(WING, TOT + 5, 0, 0)
M.advance(TOT + 600)
trap(LEAD)
M.event({ id = world.event.S_EVENT_LAND, initiator = WING, place = { getName = function() return "Senaki-Kolkhi" end } })
""", c_divert)

    def c_laser(L, M, t):
        assert "HATCHET: Laser on the blast door, code 1688" in t and len(M.lasers) == 1
        assert M.lasers[1].code == 1688 and M.lasers[1].dead       # off once the store is destroyed
        assert "TARGET DESTROYED" in t
    run("HATCHET lases on call, off after the kill", BOMB + """
launch()
M.advance(TOT - 60)
M.cmds["Deep Cut/Hatchet: laser on the door"]()
M.advance(TOT - 30)
bomb(LEAD, TOT, 0, 0)
bomb(LEAD, TOT, 1, 1)
M.advance(TOT + 10)
""", c_laser)

    def c_eject(L, M, t):
        nxt = re.search(r'NEXT_ESCAPE = "([^"]+)"', cfg).group(1)
        assert nxt == ("Operation_Deep_Cut_Escape_SC.miz" if "_SC" in str(path) else "Operation_Deep_Cut_Escape.miz")
        assert f"Also fly {nxt} to bring the downed pilot home." in t
        assert M.flags["91"] is True
    run("A pilot down over land goes to the escape mission", BOMB + """
launch()
bomb(LEAD, TOT, 0, 0)
bomb(LEAD, TOT, 1, 1)
M.advance(TOT + 120)
M.event({ id = world.event.S_EVENT_EJECTION, initiator = WING })
trap(LEAD)
""", c_eject)

    def c_same(L, M, t):
        assert "Shack!" in t and "TARGET DESTROYED" not in t
    run("One bomb cannot breach and kill", BOMB + """
launch()
bomb(LEAD, TOT, 0, 0)
M.advance(TOT + 30)
""", c_same)

    def c_menu(L, M, t):
        assert "Radar floor" in t and "HAMMER hits Red's fighter control" in t
    run("Time check", "M.advance(START + 60); M.cmds['Deep Cut/Time check']()", c_menu)


for f in FILES:
    suite(f)
print("ALL DEEP CUT SCENARIOS PASSED")
