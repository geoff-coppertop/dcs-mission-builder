"""Run the embedded mission script against a mocked DCS scripting API."""
import sys
import importlib, os
import lupa as _lupa_default
lupa = importlib.import_module("lupa." + os.environ["NG_LUA"]) if os.environ.get("NG_LUA") else _lupa_default

MOCK = r"""
local M = { now = __T0__, t0 = __T0__, flags = {}, act = {}, sched = {}, msgs = {}, opts = {}, cmds = {},
            menus = {}, activated = false, smoke = 0, lasers = {}, handlers = {} }
MOCKSTATE = M
local function log(s) M.msgs[#M.msgs+1] = string.format("[%s] %s", M.now, s) end

timer = {
  getTime = function() return M.now - M.t0 end,
  getAbsTime = function() return M.now end,
  scheduleFunction = function(fn, arg, t) M.sched[#M.sched+1] = {fn=fn, arg=arg, t=t} end,
}
coalition = { side = { RED = 1, BLUE = 2 } }
trigger = { action = {
    outTextForCoalition = function(side, text) log(text) end,
    smoke = function() M.smoke = M.smoke + 1 end,
    activateGroup = function(g) if g.name == "Red Scramble" then M.activated = true else M.act[g.name] = true end end,
    setUserFlag = function(f, v) if f == "51" and v then M.capActive = true end; M.flags[f] = v end },
  smokeColor = { Red = 1 },
  misc = { getZone = function(n) if n == "BRIDGE" then return M.zone end end,
           getUserFlag = function(f) local v = M.flags[tostring(f)] return (v and v ~= 0) and 1 or 0 end } }
country = { id = { USA = 2 } }
AI = { Option = {
  Ground = { id = { ALARM_STATE = 9, ROE = 0 },
             val = { ALARM_STATE = { AUTO = 0, GREEN = 1, RED = 2 },
                     ROE = { OPEN_FIRE = 2, WEAPON_HOLD = 4 } } },
  Air = { id = { ROE = 0 }, val = { ROE = { WEAPON_HOLD = 4 } } } } }
M.tasks = {}
Weapon = { Category = { SHELL = 0, MISSILE = 1, ROCKET = 2, BOMB = 3 },
           MissileCategory = { AAM = 1, SAM = 2, BM = 3, ANTI_SHIP = 4, CRUISE = 5, OTHER = 6 } }
world = { event = { S_EVENT_SHOT = 1, S_EVENT_TAKEOFF = 3, S_EVENT_LAND = 4, S_EVENT_CRASH = 5, S_EVENT_EJECTION = 6,
                    S_EVENT_DEAD = 8, S_EVENT_PILOT_DEAD = 9, S_EVENT_UNIT_LOST = 30 },
          VolumeType = { SPHERE = 2 },
          addEventHandler = function(h) M.handlers[#M.handlers+1] = h end,
          searchObjects = function(cat, vol, fn)
            for _, o in ipairs(M.scenery) do
              local dx, dz = o.p.x - vol.params.point.x, o.p.z - vol.params.point.z
              if math.sqrt(dx*dx + dz*dz) <= vol.params.radius then fn(o) end
            end
          end }
Object = { Category = { UNIT = 1, WEAPON = 2, STATIC = 3, BASE = 4, SCENERY = 5, CARGO = 6 } }
M.scenery = {}
M.zone = nil
function M.addScenery(tn, x, z)
  local o = { tn = tn, p = { x = x, y = 3, z = z }, alive = true }
  function o:getTypeName() return self.tn end
  function o:getPoint() return self.p end
  function o:isExist() return self.alive end
  function o:getLife() return self.alive and 100 or 0 end
  M.scenery[#M.scenery+1] = o
  return o
end
land = { isVisible = function() return true end, getHeight = function() return 12 end }
coord = { LOtoLL = function(p) return 42.74, 41.505, 0 end,
          LLtoMGRS = function() return { UTMZone = "37T", MGRSDigraph = "GH", Easting = 123, Northing = 45678 } end }
missionCommands = {
  addSubMenuForCoalition = function(side, name, parent) M.menus[#M.menus+1] = name; return { name } end,
  addCommandForCoalition = function(side, name, parent, fn) M.cmds[(parent and parent[1] or "") .. "/" .. name] = fn end }

-- units / groups
local function mkUnit(name, x, z)
  local u = { name = name, life = 10, alive = true, p = { x = x, y = 5, z = z } }
  function u:isExist() return self.alive end
  function u:getLife() return self.alive and self.life or 0 end
  function u:getName() return self.name end
  function u:getPoint() return self.p end
  function u:getAmmo() return self.ammo end
  function u:getFuel() return self.fuel or 0.6 end
  function u:getID() return 1000 + #self.name end
  return u
end
local function aam(n) return { { count = n, desc = { category = 1, missileCategory = 1, typeName = "AIM_120C" } } } end
M.aam = aam
local function mkCtl(gname)
  return { setOption = function(_, k, v) M.opts[#M.opts+1] = gname .. ":" .. k .. "=" .. v end,
           setCommand = function(_, c) M.opts[#M.opts+1] = gname .. ":" .. c.id end,
           setTask = function(_, t) M.tasks[gname] = t
             local p = t.params.route.points[1]
             M.opts[#M.opts+1] = gname .. ":task " .. p.type .. " " .. math.floor(p.x) .. "," .. math.floor(p.y) end }
end
M.units = {}
M.groups = {}
local function mkGroup(name, units)
  local g = { name = name, units = units }
  function g:isExist() return true end
  function g:getUnits() local o = {} for _, u in ipairs(self.units) do if u.alive then o[#o+1] = u end end return o end
  function g:getController() return mkCtl(name) end
  function g:activate() if name == "Red Scramble" then M.activated = true else M.act[name] = true end end
  M.groups[name] = g
  for _, u in ipairs(units) do M.units[u.name] = u end
  return g
end
local TX, TZ = -230961.2, 596825.7
mkGroup("Depot Targets", { mkUnit("T1", TX, TZ), mkUnit("T2", TX + 40, TZ + 30), mkUnit("T3", TX - 50, TZ + 70) })
mkGroup("Depot SAM", { mkUnit("SA6", TX + 1000, TZ) })
mkGroup("Depot AAA", { mkUnit("ZSU-N", TX + 1000, TZ - 300), mkUnit("ZSU-S", TX - 560, TZ - 200), mkUnit("SA13", TX - 40, TZ + 500) })
mkGroup("Red Scramble", { mkUnit("MiG1", TX + 40000, TZ) })
mkGroup("Pontiac", { mkUnit("Pontiac", TX - 3000, TZ) })
mkGroup("Chevy", { mkUnit("Chevy 1-1", TX - 90000, TZ), mkUnit("Chevy 1-2", TX - 90100, TZ) })
M.units["Chevy 1-1"].ammo = aam(6); M.units["Chevy 1-2"].ammo = aam(6)
mkGroup("CVN-74 Stennis", { mkUnit("CVN-74 Stennis", TX - 60000, TZ - 70000) })
mkGroup("Red Patrol 21", { mkUnit("Red Patrol 21 1", TX + 30000, TZ - 90000), mkUnit("Red Patrol 21 2", TX + 30100, TZ - 90000) })
mkGroup("Red Patrol 29", { mkUnit("Red Patrol 29 1", TX + 30000, TZ - 90000), mkUnit("Red Patrol 29 2", TX + 30100, TZ - 90000) })
Group = { Category = { AIRPLANE = 0 } }
coalition.addGroup = function(c, cat, data)
  local us = {}
  for _, d in ipairs(data.units) do local u = mkUnit(d.name, d.x, d.y) u.ammo = aam(6) us[#us+1] = u end
  M.spawned = data
  return mkGroup(data.name, us)
end
-- FORD: inside jamming range exactly from TOT-SUP_BEFORE to TOT+SUP_AFTER (computed when asked, from the live cfg)
local function fordUnit(name, dz)
  local u = mkUnit(name, 0, 0)
  function u:getPoint()
    local c = TOTS.cfg
    local on, off = c.TOT - c.SUP_BEFORE, c.TOT + c.SUP_AFTER
    local inside = M.now >= on and M.now < off and M.act["Ford"] and not M.fordOut
    local r = inside and (c.JAM_R - 2000) or (c.JAM_R + 20000)
    return { x = c.SAM_POINT.x - r, y = 7600, z = c.SAM_POINT.z + dz }
  end
  return u
end
mkGroup("Ford", { fordUnit("Ford 1-1", 0), fordUnit("Ford 1-2", 50) })
Group.getByName = function(n) return M.groups[n] end
M.red = { "Red Scramble", "Red Patrol 21", "Red Patrol 29" }
coalition.getGroups = function(side, cat)
  local out = {}
  if side ~= coalition.side.RED then return out end
  for _, n in ipairs(M.red) do
    local g = M.groups[n]
    if g then
      for _, u in ipairs(g.units) do
        u.isActive = function() return (n == "Red Scramble" and M.activated) or M.act[n] == true end
      end
      out[#out + 1] = g
    end
  end
  return out
end
Unit = { getByName = function(n) return M.units[n] end }

Spot = { createLaser = function(src, off, pt, code)
  local s = { pt = pt, code = code }
  function s:setPoint(p) self.pt = p end
  function s:destroy() self.dead = true end
  M.lasers[#M.lasers+1] = s
  return s end }

-- driver helpers
function M.advance(to)
  while true do
    table.sort(M.sched, function(a, b) return a.t < b.t end)
    local nxt = M.sched[1]
    if not nxt or (nxt.t + M.t0) > to then break end
    table.remove(M.sched, 1)
    M.now = nxt.t + M.t0
    local r = nxt.fn(nxt.arg, nxt.t)
    if r then M.sched[#M.sched+1] = { fn = nxt.fn, arg = nxt.arg, t = r } end
  end
  M.now = to
end
function M.event(e) for _, h in ipairs(M.handlers) do h:onEvent(e) end end
function M.player(name, unitName, x, z, hdg, alt)
  local u = mkUnit(unitName or ("P-" .. name), x or 0, z or 0)
  u.p.y = alt or 6096
  u.hdg = hdg or 0
  u.getPlayerName = function() return name end
  u.fuel = 0.5
  function u:getFuel() return self.fuel end
  function u:getPosition() local r = math.rad(self.hdg) return { x = { x = math.cos(r), y = 0, z = math.sin(r) }, p = self.p } end
  M.units[u.name] = u
  return u
end
-- a bomb that exists for `fall` seconds and then impacts at (x,z)
function M.bomb(x, z, fall, cat)
  local w = { born = M.now, fall = fall, p = { x = x, y = 1000, z = z } }
  function w:isExist() return M.now - self.born < self.fall end
  function w:getPoint() return self.p end
  function w:getDesc() return { category = cat or Weapon.Category.BOMB } end
  return w
end
function M.carrier() return { getName = function() return "CVN-74 Stennis" end } end
-- default: a bridge (2 spans) plus a house inside the BRIDGE zone, ~7 km NW of the target
M.BX, M.BZ = -230961.2 + 1300, 596825.7 - 7000
M.zone = { point = { x = M.BX + 150, y = 0, z = M.BZ - 100 }, radius = 600 }
M.span1 = M.addScenery("MOST_ZHD_1", M.BX, M.BZ)
M.span2 = M.addScenery("most_zhd_2", M.BX + 40, M.BZ + 10)
M.house = M.addScenery("HOUSE_3", M.BX + 100, M.BZ)
"""


def scenario(name, steps, pre=""):
    L = lupa.LuaRuntime(unpack_returned_tuples=True)
    L.execute(MOCK.replace("__T0__", str(TOT - 1800)))
    if pre:
        L.execute(pre)
    L.execute(SCRIPT)
    M = L.globals().MOCKSTATE
    L.execute(steps)
    print(f"\n===== {name}")
    for i in range(1, len(M.msgs) + 1):
        print(" ", M.msgs[i].replace("\n", " | "))
    print("  opts:", [M.opts[i] for i in range(1, len(M.opts) + 1)])
    print("  scrambled/activated:", M.activated, " smoke:", M.smoke, " lasers:", len(M.lasers))
    return L, M


import re as _re
from missionbuilder.mapkit import parse_miz
# the mission's scripts, in trigger order (CAPCFG, cap.lua, the Narrow Gate script), from the built .miz
SCRIPT = "\n".join(parse_miz(sys.argv[1])["scripts"]) if sys.argv[1].endswith(".miz") else open(sys.argv[1], encoding="utf-8").read()
TOT = int(_re.search(r"TOT\s*=\s*(\d+)", SCRIPT).group(1))
def _hms(x):
    x = int(x) % 86400
    return f"{x // 3600:02d}:{x % 3600 // 60:02d}:{x % 60:02d}"
common = f"local M=MOCKSTATE local TOT={TOT} local TX,TZ=-230961.2,596825.7\n"


def run(name, body, check=None, pre=""):
    L, M = scenario(name, common + body, pre)
    if check:
        check(L, M)
    return L, M

FLOW = """
local lead = M.player("Geoff", "Enfield 1-1", TX - 30000, TZ - 30000, 225)
local wing = M.player("Wing", "Enfield 1-2", TX - 31000, TZ - 30500, 225)
M.advance(TOT - 900)
M.cmds["Pontiac (CAS)/1. Check in"]()
M.advance(TOT - 890)
M.cmds["Pontiac (CAS)/2. Ready to copy 9-line"]()
M.cmds["Pontiac (CAS)/3. Read back 4, 6, restrictions"]()
M.advance(TOT - 880)
"""

# 1. Full standard flow, both jets on time, cleared hot, laser, OFF + BDA, recovery debrief
def chk1(L, M):
    assert not M.activated, "on time should not scramble"
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    for needle in ["checking in", "GAME PLAN: Type 2", "9-line follows", "Readback correct",
                   "Enfield 1-1, CLEARED HOT", "Enfield 1-2, CLEARED HOT", "Laser on, code 1688",
                   "Copy spot", "BDA:", "direct hit", "ON TIME: Geoff", "ON TIME: Wing",
                   "all cleared hot", "Terminate, laser off"]:
        assert needle in txt, needle
    assert "WITHOUT" not in txt
run("FULL FLOW: on time, both jets", FLOW + """
-- move to the IP area, heading 054
lead.p.x, lead.p.z, lead.hdg = TX - 10000, TZ - 14000, 54
wing.p.x, wing.p.z, wing.hdg = TX - 12000, TZ - 16000, 50
M.advance(TOT - 45)
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.cmds["Enfield 1-1/Ten seconds (laser on)"]()
M.advance(TOT - 42)
M.cmds["Enfield 1-1/Spot"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX+5, TZ, 40) })
M.advance(TOT - 35)
M.cmds["Enfield 1-1/OFF (request BDA)"]()
M.advance(TOT - 20)
M.cmds["Enfield 1-2/IN (heading auto)"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = wing, weapon = M.bomb(TX+40, TZ+30, 45) })
-- the lead's bomb kills T1
M.advance(TOT - 2)
M.units["T1"].alive = false
M.event({ id = world.event.S_EVENT_DEAD, initiator = M.units["T1"] })
M.advance(TOT + 40)
M.cmds["Enfield 1-1/Terminate (laser off)"]()
M.advance(TOT + 120)
M.event({ id = world.event.S_EVENT_LAND, initiator = lead, place = M.carrier() })
""", chk1)

# 2. Aborts: no readback, wrong heading, too early, too far
def chk2(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    for needle in ["No readback", "outside final attack heading", "Too early", "Call IN from the IP",
                   "WITHOUT clearance", "1 WITHOUT CLEARANCE"]:
        assert needle in txt, needle
run("ABORTS + uncleared drop", """
local lead = M.player("Geoff", "Enfield 1-1", TX - 10000, TZ - 14000, 54)
M.advance(TOT - 300)
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.cmds["Pontiac (CAS)/1. Check in"]()
M.advance(TOT - 290)
M.cmds["Pontiac (CAS)/2. Ready to copy 9-line"]()
M.cmds["Pontiac (CAS)/3. Read back 4, 6, restrictions"]()
M.advance(TOT - 280)
M.cmds["Enfield 1-1/IN (heading auto)"]()            -- too early
lead.hdg = 140
M.advance(TOT - 50)
M.cmds["Enfield 1-1/IN (heading auto)"]()            -- wrong heading
lead.hdg = 54; lead.p.x = TX - 60000
M.cmds["Enfield 1-1/IN (heading auto)"]()            -- too far
lead.p.x = TX - 10000
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX, TZ, 30) })
M.advance(TOT + 200)
M.event({ id = world.event.S_EVENT_LAND, initiator = lead, place = M.carrier() })
""", chk2)

# 3. Late: scramble, CAP commit, cleared hot with warning, BDA via auto (no OFF call)
def chk3(L, M):
    assert M.activated and M.capActive
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    for needle in ["No bombs landed in the impact window", "Chevy 1-1", "SA-6 is UP", "LATE: Geoff", "BDA:", "m north"]:
        assert needle in txt, needle
run("LATE + CAP + auto BDA", FLOW + """
local lead = M.units["Enfield 1-1"]
lead.p.x, lead.p.z, lead.hdg = TX - 10000, TZ - 14000, 54
M.advance(TOT + 100)
M.cmds["Strike/Request CAP cover"]()
M.cmds["Strike/Request CAP cover"]()
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX + 120, TZ, 30) })
M.advance(TOT + 200)
""", chk3)

# 4. Early drop graded EARLY, miss outside 2.5 km not graded
def chk4(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "EARLY: Geoff" in txt and "Wing" not in txt.split("EARLY")[1].split("\n")[0]
    assert M.activated
run("EARLY + far miss", """
local lead = M.player("Geoff", "Enfield 1-1", TX - 8000, TZ - 8000, 54)
local wing = M.player("Wing", "Enfield 1-2", TX - 8000, TZ - 8000, 54)
M.advance(TOT - 210)
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX, TZ, 30) })
M.event({ id = world.event.S_EVENT_SHOT, initiator = wing, weapon = M.bomb(TX + 5000, TZ, 30) })
M.advance(TOT + 130)
""", chk4)

# 5. Laser auto-shift and stop when all destroyed; smoke; AAM ignored; time check shows flow status
def chk5(L, M):
    assert L.globals().MOCKSHIFT and L.globals().MOCKLASERDEAD
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Shift. Spot moving" in txt and "red smoke" in txt and "readback correct" in txt
    assert M.smoke == 1
run("LASER shift/stop, smoke, AAM ignored, time check", FLOW + """
local lead = M.units["Enfield 1-1"]
M.cmds["Pontiac (CAS)/Request mark (red smoke)"]()
M.cmds["Strike/Time check"]()
local aam = M.bomb(TX, TZ, 3, Weapon.Category.MISSILE)
aam.getDesc = function() return { category = 1, missileCategory = 1 } end
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = aam })
M.cmds["Enfield 1-1/Ten seconds (laser on)"]()
M.advance(TOT - 870)
local first = M.lasers[1].pt.x
M.units["T1"].alive = false
M.event({ id = world.event.S_EVENT_DEAD, initiator = M.units["T1"] })
M.advance(TOT - 865)
MOCKSHIFT = (M.lasers[1].pt.x ~= first)
M.units["T2"].alive = false; M.units["T3"].alive = false
M.event({ id = world.event.S_EVENT_DEAD, initiator = M.units["T3"] })
M.advance(TOT - 855)
MOCKLASERDEAD = M.lasers[1].dead
""", chk5)

# 6. Bridge removed: no bridge menu or text anywhere
def chk6(L, M):
    keys = [k for k in M.cmds.keys()]
    assert not any("ridge" in k for k in keys), keys
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "ridge" not in txt and "Secondary - Clean recovery: ACHIEVED" in txt
run("NO BRIDGE + clean recovery achieved", FLOW + """
local lead = M.units["Enfield 1-1"]
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = lead })
M.cmds["Strike/Time check"]()
M.advance(TOT + 300)
M.event({ id = world.event.S_EVENT_LAND, initiator = lead, place = M.carrier() })
""", chk6)

# 8. Clean recovery failed: wing ejects, lead traps low on fuel
def chk8(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    for needle in ["Wing is down", "LOW FUEL at trap (12%)", "Clean recovery: FAILED", "Wing ejected", "Geoff landed with 12% fuel"]:
        assert needle in txt, needle
run("CLEAN RECOVERY failed", FLOW + """
local lead = M.units["Enfield 1-1"]; local wing = M.units["Enfield 1-2"]
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = lead })
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = wing })
M.advance(TOT + 300)
M.event({ id = world.event.S_EVENT_EJECTION, initiator = wing })
lead.fuel = 0.12
M.event({ id = world.event.S_EVENT_LAND, initiator = lead, place = M.carrier() })
""", chk8)

# 9. Split windows: jammers TOT-150..TOT+120, early impact under jamming, SAM state timeline, earliest IN
def chk9(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Ahead of the impact window" in txt and "EARLY: Geoff" in txt
    assert f"Earliest IN {_hms(TOT - 110)}L" in txt, "earliest IN = TOT-110"
    assert f"planned off {_hms(TOT + 120)}L" in txt
    opts = [M.opts[i] for i in range(1, len(M.opts) + 1)]
    t = L.globals().MOCKSAMLOG
    assert t["at_m151"] == "on" and t["at_m149"] == "off" and t["at_p119"] == "off" and t["at_p121"] == "on", dict(t)
run("SPLIT WINDOWS", FLOW + """
local lead = M.units["Enfield 1-1"]
lead.p.x, lead.p.z, lead.hdg = TX - 10000, TZ - 14000, 54
MOCKSAMLOG = {}
local function sam() return TOTS.state.samActive and "on" or "off" end
M.advance(TOT - 151); MOCKSAMLOG.at_m151 = sam()
M.advance(TOT - 149); MOCKSAMLOG.at_m149 = sam()
M.advance(TOT - 130)
M.cmds["Enfield 1-1/IN (heading auto)"]()          -- before earliest IN -> abort
M.cmds["Strike/Time check"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX, TZ, 30) })   -- impact TOT-100
M.advance(TOT + 119); MOCKSAMLOG.at_p119 = sam()
M.advance(TOT + 124); MOCKSAMLOG.at_p121 = sam()   -- 3 s debounce on FORD leaving
""", chk9)

# 9. Split windows: on-time pass is covered by jammers; IN at IP accepted before the impact window;
#    early-but-jammed impact graded EARLY without the "live SA-6" text; SA-6 + MiGs only at TOT+120
def chk9(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Enfield 1-1, CLEARED HOT" in txt, "IN at TOT-100 should be cleared"
    assert "package TOT was missed" in txt and "bombed into a live SA-6" not in txt
    assert L.globals().SAM_AT_ENTRY == "suppressed", L.globals().SAM_AT_ENTRY
    assert L.globals().SCRAMBLED_AT_61 is False and M.activated, "scramble only when jammers go off"
run("SPLIT: jammers cover the pass, impact scored +/-60", FLOW + """
local lead = M.units["Enfield 1-1"]
M.advance(TOT - 112)                       -- lead crosses into SA-6 range on an on-time pass
SAM_AT_ENTRY = TOTS.state.samActive and "live" or "suppressed"
lead.p.x, lead.p.z, lead.hdg = TX - 10000, TZ - 14000, 54
M.advance(TOT - 100)
M.cmds["Enfield 1-1/IN (heading auto)"]()
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX, TZ, 30) })   -- lands TOT-70
M.advance(TOT + 61)
SCRAMBLED_AT_61 = M.activated
M.advance(TOT + 125)
""", chk9)

# 10. Guns stay live through the jammer window; SA-6 toggles
def chk10(L, M):
    opts = [M.opts[i] for i in range(1, len(M.opts) + 1)]
    aaa = [o for o in opts if o.startswith("Depot AAA:")]
    assert aaa == ["Depot AAA:9=2", "Depot AAA:0=2"], aaa
    assert "Depot SAM:0=4" in opts and "Depot SAM:9=1" in opts
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Guns and SA-13 are still up" in txt and "NOT jammed" in txt and "17,000" in txt
run("GUNS never jammed", FLOW + """
M.advance(TOT + 200)
""", chk10)

# 11. Campaign outcome grading
def outcome_case(name, kills, ontime, lose, expect, nxt, rescue):
    def chk(L, M):
        txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
        assert "OUTCOME: " + expect + "." in txt, (name, txt[-400:])
        assert "NEXT MISSION: " + nxt in txt
        assert ("Operation_Sandy_Lift.miz" in txt) == rescue
        assert M.flags["90"] == {"SUCCESS": 1, "PARTIAL": 2, "FAILURE": 3, "SUCCESS, LATE": 4}[expect]
    body = FLOW + """
local lead = M.units["Enfield 1-1"]
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = lead })
"""
    if ontime:
        body += """
M.advance(TOT - 30)
M.event({ id = world.event.S_EVENT_SHOT, initiator = lead, weapon = M.bomb(TX, TZ, 30) })
"""
    for i in range(kills):
        body += f"""
M.advance(TOT + {5 + i})
M.units["T{i+1}"].alive = false
M.event({{ id = world.event.S_EVENT_DEAD, initiator = M.units["T{i+1}"] }})
"""
    body += """
M.advance(TOT + 200)
"""
    body += ('M.event({ id = world.event.S_EVENT_EJECTION, initiator = lead })\n' if lose else
             'M.event({ id = world.event.S_EVENT_LAND, initiator = lead, place = M.carrier() })\n')
    run("OUTCOME " + name, body, chk)

outcome_case("success", 3, True, False, "SUCCESS", "Operation_Long_Road.miz", False)
outcome_case("all dead but late", 3, False, False, "SUCCESS, LATE", "Operation_Long_Road_Own_SEAD.miz", False)
outcome_case("partial", 2, True, False, "PARTIAL", "Operation_Stone_Ford.miz", False)
outcome_case("failure + jet lost", 1, True, True, "FAILURE", "Operation_Stone_Ford_Hard.miz", True)

# 12. FORD: activates on time, jamming follows its position; FORD lost mid-window closes the window early;
#     FORD lost before arriving means no jamming at all
def chk12(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert M.act["Ford"] and "FORD 1-1, two jets, inbound from the south" in txt
    assert "FORD: Jammers on, SA-6 SUPPRESSED" in txt and "FORD is down! Jamming lost." in txt
    assert L.globals().JAM_EARLY_OFF is True, "window should close when FORD dies"
run("FORD lost mid-window", FLOW + """
M.advance(TOT - 100)
JAM_WAS_ON = TOTS.state.windowOpen
M.units["Ford 1-1"].alive = false; M.units["Ford 1-2"].alive = false
M.advance(TOT - 95)
JAM_EARLY_OFF = JAM_WAS_ON and not TOTS.state.windowOpen and TOTS.state.samActive
M.advance(TOT + 200)
""", chk12)

def chk13(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "FORD is down before it reached you. There will be no jamming" in txt
    assert "FORD: Jammers on" not in txt and "FORD is down: NO jamming" in txt
run("FORD lost before arriving", FLOW + """
M.advance(TOT - 400)
M.units["Ford 1-1"].alive = false; M.units["Ford 1-2"].alive = false
M.advance(TOT - 390)
M.cmds["Strike/Time check"]()
M.advance(TOT + 200)
""", chk13)


# 14. Patrol up (MiG-29s): MAGIC reports it; when the jammers come on it pushes and MAGIC commits Chevy
#     to screen FORD on its own; Chevy resets when the patrol is destroyed; summary reports it all
def chk14(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert M.act["Red Patrol 29"] and not M.act["Red Patrol 21"]
    assert "two MiG-29s, orbiting off Gudauta" in txt and "I'll commit Chevy to screen FORD" in txt
    assert M.flags["62"] is True, "patrol push flag"
    assert "Chevy 1-1, commit. Gudauta group, two MiG-29s, hot on FORD." in txt and "committing on FORD" in txt
    assert "Negative, Chevy is committed on FORD." in txt, "request refused while busy"
    assert "FORD is clean. Reset CAP station. Chevy has 10 missiles." in txt
    tasks = [M.opts[i] for i in range(1, len(M.opts) + 1) if M.opts[i].startswith("Chevy:task")]
    assert len(tasks) == 2, tasks
    assert "Gudauta patrol: two MiG-29s, 2 shot down, destroyed." in txt and "CAP: Chevy committed: FORD." in txt
    assert "FORD: both jets continued north." in txt
run("PATROL up, MAGIC commits Chevy, reset", """
M.flags["60"] = true; M.flags["61"] = true
""" + FLOW[1:] + """
M.advance(TOT - 140)
M.cmds["Strike/Request CAP cover"]()
M.advance(TOT - 100)
M.units["Red Patrol 29 1"].alive = false; M.units["Red Patrol 29 2"].alive = false
M.units["Chevy 1-1"].ammo = M.aam(4)
M.advance(TOT - 80)
M.event({ id = world.event.S_EVENT_TAKEOFF, initiator = M.units["Enfield 1-1"] })
M.cmds["Strike/Mission summary now"]()
""", chk14)

# 15. No patrol: MAGIC says clean, no automatic commit; a request is approved for the egress and resets later
def chk15(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "No Gudauta patrol this morning" in txt and "off CAP station to cover your egress" in txt and M.capActive
    assert "commit." not in txt, "nothing met the commit criteria"
    assert not M.act["Red Patrol 21"] and not M.act["Red Patrol 29"]
    assert "your egress is clean. Reset CAP station." in txt, "request resets after ~8 quiet minutes"
run("PATROL not up, request approved", FLOW + """
M.advance(TOT - 600)
M.cmds["Strike/Request CAP cover"]()
M.advance(TOT - 50)
""", chk15)

# 16. Jamming gap: FORD defends out of range mid-window, SA-6 comes up, jamming resumes when it is back;
#     no scramble from a gap
def chk16(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    g = L.globals()
    assert "FORD: Defending! Jammers off you." in txt and "FORD: Back on track, jammers on." in txt
    assert g.GAP_SAM is True and g.BACK_SAM is False and not M.activated
    assert "interrupted, SA-6 UP" in txt
run("JAM GAP and resume", FLOW + """
M.advance(TOT - 100)
M.fordOut = true
M.advance(TOT - 90)
GAP_SAM = TOTS.state.samActive
M.cmds["Strike/Time check"]()
M.fordOut = false
M.advance(TOT - 80)
BACK_SAM = TOTS.state.samActive
""", chk16)

# 17. Chevy Winchester on the FORD screen: RTB, alert-5 Uzi launches and becomes the CAP;
#     the late alert MiGs then get Uzi (pending commit served when Uzi is on station? no: Uzi is free, MAGIC commits it)
def chk17(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Chevy is Winchester, RTB. Mother is launching the alert-5, Uzi" in txt
    assert M.spawned and M.spawned.name == "Uzi" and M.spawned.units[1].name == "Uzi 1-1"
    assert M.spawned.units[1].callsign[1] == 3, "Uzi callsign index 3"
    assert "Negative, no CAP on station. Uzi is on the way" in txt
    assert "Two MiG-21s off the Gudauta alert, hot toward the target area. No CAP to commit; Uzi due" in txt
    assert "Uzi 1-1, two Hornets off the alert" in txt
    assert "Uzi 1-1, commit. Two MiG-21s off the Gudauta alert" in txt, "the pending threat goes to Uzi"
    assert "Negative, Uzi is committed on your egress." in txt
    assert M.tasks["Chevy"].params.route.points[1].type == "Land"
run("CHEVY Winchester, Uzi relief", """
M.flags["60"] = true
""" + FLOW[1:] + """
M.advance(TOT - 100)
M.units["Chevy 1-1"].ammo = M.aam(1); M.units["Chevy 1-2"].ammo = M.aam(0)
M.advance(TOT - 90)
M.cmds["Strike/Request CAP cover"]()
M.advance(TOT + 130)
M.advance(TOT - 90 + 310)
M.units["Red Patrol 21 1"].alive = false; M.units["Red Patrol 21 2"].alive = false
M.units["MiG1"].alive = false
M.cmds["Strike/Request CAP cover"]()
""", chk17)

# 18. Chevy loses a jet in the fight: the survivor holds, the alert launches; then Uzi is lost: no more alert
def chk18(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Chevy is down to one jet. Mother is launching the alert-5" in txt
    assert "A single Chevy holds until Uzi is on station" in txt
    assert M.tasks["Chevy"].params.route.points[1].type == "Land", "survivor recovers once Uzi is on station"
    assert "Uzi is down. No more alert jets on Mother." in txt
run("CHEVY loses a jet, then Uzi lost", """
M.flags["60"] = true
""" + FLOW[1:] + """
M.advance(TOT - 100)
M.units["Chevy 1-2"].alive = false
M.advance(TOT + 900)
M.units["Uzi 1-1"].alive = false; M.units["Uzi 1-2"].alive = false
M.advance(TOT + 910)
""", chk18)

# 19. Busy CAP: late alert MiGs launch while Chevy is still screening FORD -> no CAP for the egress until
#     Chevy resets, then MAGIC re-commits it to the egress
def chk19(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Chevy is committed on FORD; no CAP for your egress until it resets." in txt
    assert "FORD is clean. Re-commit: Two MiG-21s off the Gudauta alert" in txt
    assert "committing on your egress" in txt
run("BUSY: FORD screen, then alert MiGs", """
M.flags["60"] = true
""" + FLOW[1:] + """
local sp = TOTS.cfg.CAP_SCREEN      -- the patrol is still fighting near FORD's track
M.units["Red Patrol 21 1"].p = { x = sp.x + 5000, y = 6000, z = sp.z }
M.units["Red Patrol 21 2"].p = { x = sp.x + 5200, y = 6000, z = sp.z }
M.advance(TOT + 200)
M.units["Red Patrol 21 1"].alive = false; M.units["Red Patrol 21 2"].alive = false
M.advance(TOT + 215)
""", chk19)

# 20. Fleet defence: a Red jet within 22 nm of Mother diverts the CAP off the FORD screen; resets when clean
def chk20(L, M):
    txt = "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))
    assert "Chevy, break off FORD. Divert: 1 bandit inside 22 nm of Mother." in txt
    assert "the boat is clean." in txt
run("FLEET DEFENCE divert", """
M.flags["60"] = true
""" + FLOW[1:] + """
M.advance(TOT - 140)
local cv = M.units["CVN-74 Stennis"].p
M.units["Red Patrol 21 1"].p = { x = cv.x + 20000, y = 6000, z = cv.z }
M.advance(TOT - 120)
M.units["Red Patrol 21 1"].alive = false
M.advance(TOT - 40)
""", chk20)

print("\nALL SCENARIOS PASSED")
