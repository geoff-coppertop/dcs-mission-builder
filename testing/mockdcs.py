"""Reusable stand-in for the DCS scripting API, for testing campaign mission scripts outside DCS.

Groups/units are created from the scenario (M.mkGroup / M.mkUnit). Positions use DCS map metres
(x = north, z = east). The test drives time with M.advance(abs_seconds) and fires events with M.event{}.
"""
import importlib, os
import lupa as _lupa_default
lupa = importlib.import_module("lupa." + os.environ["NG_LUA"]) if os.environ.get("NG_LUA") else _lupa_default

BASE = r"""
local M = { now = __T0__, t0 = __T0__, flags = {}, sched = {}, msgs = {}, opts = {}, cmds = {}, tasks = {},
            menus = {}, activated = {}, smoke = 0, lasers = {}, handlers = {}, destroyed = {} }
MOCKSTATE = M
local function log(s) M.msgs[#M.msgs+1] = string.format("[%s] %s", M.now, s) end
env = { info = function(s) M.msgs[#M.msgs+1] = "[env] " .. s end }
timer = {
  getTime = function() return M.now - M.t0 end,
  getAbsTime = function() return M.now end,
  scheduleFunction = function(fn, arg, t) M.sched[#M.sched+1] = {fn=fn, arg=arg, t=t} end,
}
coalition = { side = { RED = 1, BLUE = 2 } }
trigger = { action = {
    outTextForCoalition = function(side, text) log(text) end,
    smoke = function() M.smoke = M.smoke + 1 end,
    activateGroup = function(g) M.activated[g.name] = true end,
    setUserFlag = function(f, v) M.flags[f] = v end },
  smokeColor = { Green = 0, Red = 1, White = 2, Orange = 3, Blue = 4 },
  misc = { getZone = function(n) return M.zones and M.zones[n] end } }
AI = { Option = {
  Ground = { id = { ALARM_STATE = 9, ROE = 0 },
             val = { ALARM_STATE = { AUTO = 0, GREEN = 1, RED = 2 }, ROE = { OPEN_FIRE = 2, RETURN_FIRE = 3, WEAPON_HOLD = 4 } } },
  Air = { id = { ROE = 0 }, val = { ROE = { WEAPON_HOLD = 4 } } } } }
Weapon = { Category = { SHELL = 0, MISSILE = 1, ROCKET = 2, BOMB = 3 },
           MissileCategory = { AAM = 1, SAM = 2, BM = 3, ANTI_SHIP = 4, CRUISE = 5, OTHER = 6 } }
world = { event = { S_EVENT_SHOT = 1, S_EVENT_HIT = 2, S_EVENT_TAKEOFF = 3, S_EVENT_LAND = 4, S_EVENT_CRASH = 5,
                    S_EVENT_EJECTION = 6, S_EVENT_DEAD = 8, S_EVENT_PILOT_DEAD = 9, S_EVENT_UNIT_LOST = 30 },
          addEventHandler = function(h) M.handlers[#M.handlers+1] = h end }
land = { isVisible = function() return true end, getHeight = function() return 12 end }
coord = { LOtoLL = function(p) return 42.74, 41.505, 0 end,
          LLtoMGRS = function() return { UTMZone = "37T", MGRSDigraph = "GH", Easting = 123, Northing = 45678 } end }
missionCommands = {
  addSubMenuForCoalition = function(side, name, parent) M.menus[#M.menus+1] = name; return { name } end,
  addCommandForCoalition = function(side, name, parent, fn) M.cmds[(parent and parent[1] or "") .. "/" .. name] = fn end }

M.units, M.groups = {}, {}
function M.mkUnit(name, x, z, typ)
  local u = { name = name, typ = typ or "Unit", life = 10, alive = true, p = { x = x, y = 5, z = z }, hdg = 0 }
  function u:isExist() return self.alive end
  function u:getLife() return self.alive and self.life or 0 end
  function u:getName() return self.name end
  function u:getTypeName() return self.typ end
  function u:getPoint() return self.p end
  function u:destroy() self.alive = false; M.destroyed[#M.destroyed+1] = self.name end
  function u:getAmmo()
    if self.ammo then return self.ammo end
    if self.name:find("^Chevy") or self.name:find("^Uzi") then
      return { { count = 6, desc = { category = 1, missileCategory = 1, typeName = "AIM_120C" } } }
    end
    return {}
  end
  function u:getFuel() return self.fuel or 0.6 end
  function u:getID() return 1000 + #self.name end
  function u:isActive() return not self.group or not self.group.late or M.activated[self.group.name] == true end
  function u:getPosition() local r = math.rad(self.hdg) return { x = { x = math.cos(r), y = 0, z = math.sin(r) }, p = self.p } end
  M.units[name] = u
  return u
end
local function mkCtl(gname)
  return { setOption = function(_, k, v) M.opts[#M.opts+1] = gname .. ":" .. k .. "=" .. v end,
           setCommand = function(_, c) M.opts[#M.opts+1] = gname .. ":" .. c.id end,
           setTask = function(_, t) M.tasks[gname] = t end,
           pushTask = function(_, t) M.tasks[gname] = t end }
end
function M.mkGroup(name, units)
  local g = { name = name, units = units }
  function g:isExist() return true end
  function g:getName() return self.name end
  function g:getUnits() local o = {} for _, u in ipairs(self.units) do if u.alive then o[#o+1] = u end end return o end
  function g:getController() return mkCtl(name) end
  function g:activate() M.activated[name] = true end
  g.late = name:find("^Red") ~= nil      -- Red air groups are late-activated in the missions
  M.groups[name] = g
  for _, u in ipairs(units) do M.units[u.name] = u; u.group = g end
  return g
end
Group = { getByName = function(n) return M.groups[n] end, Category = { AIRPLANE = 0, HELICOPTER = 1, GROUND = 2 } }
country = { id = { USA = 2 } }
M.redAir = {}      -- names of Red air groups, for coalition.getGroups
coalition.getGroups = function(side, cat)
  local out = {}
  if side ~= coalition.side.RED then return out end
  for n, g in pairs(M.groups) do if n:find("^Red") and g.isAir ~= false then out[#out+1] = g end end
  return out
end
coalition.addGroup = function(c, cat, data)
  local us = {}
  for _, d in ipairs(data.units) do us[#us+1] = M.mkUnit(d.name, d.x, d.y, d.type) end
  M.spawned = data
  return M.mkGroup(data.name, us)
end
Unit = { getByName = function(n) return M.units[n] end }
Spot = { createLaser = function(src, off, pt, code)
  local s = { pt = pt, code = code, src = src }
  function s:setPoint(p) self.pt = p end
  function s:destroy() self.dead = true end
  M.lasers[#M.lasers+1] = s
  return s end }

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
  local u = M.mkUnit(unitName, x or 0, z or 0, "FA-18C_hornet")
  u.p.y = alt or 6096
  u.hdg = hdg or 0
  u.getPlayerName = function() return name end
  u.fuel = 0.5
  function u:getFuel() return self.fuel end
  return u
end
-- weapon that exists for `fall` seconds then "impacts" at (x,z); kind: "BOMB" | "HARM" | "AAM"
function M.weapon(x, z, fall, kind)
  local w = { born = M.now, fall = fall, p = { x = x, y = 1000, z = z }, kind = kind or "BOMB" }
  function w:isExist() return M.now - self.born < self.fall end
  function w:getPoint() return self.p end
  function w:getTypeName() return self.kind == "HARM" and "AGM_88C" or (self.kind == "AAM" and "AIM_9X" or "GBU_12") end
  function w:getDesc()
    if self.kind == "BOMB" then return { category = Weapon.Category.BOMB } end
    if self.kind == "HARM" then return { category = Weapon.Category.MISSILE, missileCategory = Weapon.MissileCategory.OTHER } end
    return { category = Weapon.Category.MISSILE, missileCategory = Weapon.MissileCategory.AAM }
  end
  return w
end
function M.carrier() return { getName = function() return "CVN-74 Stennis" end } end
function M.text() local t = {} for i = 1, #M.msgs do t[#t+1] = M.msgs[i] end return table.concat(t, "\n") end
"""


def make(t0, setup_lua, scripts):
    """New Lua runtime with the mock, scenario setup (groups/units), then mission scripts in order."""
    L = lupa.LuaRuntime(unpack_returned_tuples=True)
    L.execute(BASE.replace("__T0__", str(t0)))
    L.execute(setup_lua)
    for s in scripts:
        L.execute(s)
    return L, L.globals().MOCKSTATE


def text(M):
    return "\n".join(M.msgs[i] for i in range(1, len(M.msgs) + 1))


def scripts_from_miz(path):
    """Return the DO SCRIPT texts embedded in a .miz, in trigger order."""
    import zipfile
    L = lupa.LuaRuntime(unpack_returned_tuples=True)
    with zipfile.ZipFile(path) as z:
        L.execute(z.read("mission").decode("utf-8"))
        L.execute(z.read("l10n/DEFAULT/dictionary").decode("utf-8"))
    mis, dic = L.globals().mission, L.globals().dictionary
    acts = mis.trigrules[1].actions
    return [dic[acts[i].text] for i in range(1, len(acts) + 1)]
