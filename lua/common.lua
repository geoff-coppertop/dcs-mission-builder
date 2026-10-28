-- Narrow Gate campaign: shared mission-script library (load before each mission's own script).
-- Pure DCS scripting engine, Lua 5.1 compatible. Everything lives in the global table NG.

NG = NG or {}
local N = NG
N.BLUE = coalition.side.BLUE
N.ZULU = 4 * 3600
local atan2 = math.atan2 or math.atan
N.atan2 = atan2

------------------------------------------------------------------ text and time
function N.msg(text, secs) trigger.action.outTextForCoalition(N.BLUE, text, secs or 15) end

function N.hms(abs)
  abs = math.floor(abs + 0.5) % 86400
  return string.format("%02d:%02d:%02d", math.floor(abs / 3600), math.floor(abs % 3600 / 60), abs % 60)
end
function N.hm(abs) return string.sub(N.hms(abs), 1, 5) end
function N.clock(abs) return N.hms(abs) .. "L / " .. N.hms(abs - N.ZULU) .. "Z" end
function N.mmss(d)
  local sign = d < 0 and "-" or "+"
  d = math.abs(math.floor(d + 0.5))
  return string.format("%s%d:%02d", sign, math.floor(d / 60), d % 60)
end

------------------------------------------------------------------ geometry (x = north, z = east)
function N.dist(a, b)
  local dx, dz = a.x - b.x, a.z - b.z
  return math.sqrt(dx * dx + dz * dz)
end
function N.bearing(a, b) return (math.deg(atan2(b.z - a.z, b.x - a.x)) + 360) % 360 end
function N.compass(deg)
  local names = { "north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west" }
  return names[math.floor(((deg + 22.5) % 360) / 45) + 1]
end
function N.heading(unit)
  local pos = unit:getPosition()
  return (math.deg(atan2(pos.x.z, pos.x.x)) + 360) % 360
end

function N.coord(p)
  local lat, lon = coord.LOtoLL(p)
  local function ddm(v, pos, neg, w)
    local h = v >= 0 and pos or neg
    v = math.abs(v)
    local d = math.floor(v)
    return string.format("%s %0" .. w .. "d°%06.3f'", h, d, (v - d) * 60)
  end
  local m = coord.LLtoMGRS(lat, lon)
  local mgrs = string.format("MGRS %s %s %05d %05d", m.UTMZone, m.MGRSDigraph, math.floor(m.Easting), math.floor(m.Northing))
  local elev = land.getHeight({ x = p.x, y = p.z })
  return ddm(lat, "N", "S", 2) .. "  " .. ddm(lon, "E", "W", 3), mgrs,
         string.format("%d ft MSL", math.floor(elev * 3.28084 + 0.5))
end

------------------------------------------------------------------ units
function N.playerName(unit)
  if not unit or not unit.getPlayerName then return nil end
  local ok, name = pcall(unit.getPlayerName, unit)
  if ok then return name end
  return nil
end

function N.liveUnits(groupName)
  local g = Group.getByName(groupName)
  local out = {}
  if not g or not g:isExist() then return out end
  for _, u in ipairs(g:getUnits() or {}) do
    if u and u:isExist() and u:getLife() > 1 then out[#out + 1] = u end
  end
  return out
end

function N.liveUnit(name)
  local u = Unit.getByName(name)
  if u and u:isExist() and u:getLife() > 1 then return u end
  return nil
end

function N.setAD(groupName, live)
  local g = Group.getByName(groupName)
  if not g or not g:isExist() then return end
  local c = g:getController()
  if live then
    c:setOption(AI.Option.Ground.id.ALARM_STATE, AI.Option.Ground.val.ALARM_STATE.RED)
    c:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.OPEN_FIRE)
  else
    c:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.WEAPON_HOLD)
    c:setOption(AI.Option.Ground.id.ALARM_STATE, AI.Option.Ground.val.ALARM_STATE.GREEN)
  end
end

function N.activate(groupName)
  local g = Group.getByName(groupName)
  if not g then return false end
  local ok = pcall(function() g:activate() end)
  if not ok then trigger.action.activateGroup(g) end
  return true
end

function N.quiet(groupName)   -- untouchable, silent helper (drones, survivors)
  local g = Group.getByName(groupName)
  if not g then return end
  local c = g:getController()
  c:setCommand({ id = "SetInvisible", params = { value = true } })
  c:setCommand({ id = "SetImmortal", params = { value = true } })
end

------------------------------------------------------------------ weapons
function N.weaponKind(w)
  local ok, desc = pcall(w.getDesc, w)
  if not ok or not desc then return nil end
  local okn, tn = pcall(w.getTypeName, w)
  tn = okn and tn and string.upper(tn) or ""
  if tn:find("AGM_88") or tn:find("HARM") then return "HARM" end
  local cat = desc.category
  if cat == Weapon.Category.BOMB or cat == Weapon.Category.ROCKET then return "GROUND" end
  if cat == Weapon.Category.MISSILE then
    local mc = desc.missileCategory
    if mc == Weapon.MissileCategory.OTHER or mc == Weapon.MissileCategory.ANTI_SHIP or mc == Weapon.MissileCategory.CRUISE then
      return "GROUND"
    end
  end
  return nil
end

-- follow a weapon until it ceases to exist; onImpact(lastPoint) when it does
function N.track(w, onImpact)
  local last
  timer.scheduleFunction(function(_, t)
    local ok, alive = pcall(w.isExist, w)
    if ok and alive then
      local okp, p = pcall(w.getPoint, w)
      if okp and p then last = p end
      return t + 0.1
    end
    if last then onImpact(last) end
    return nil
  end, nil, timer.getTime() + 0.1)
end

------------------------------------------------------------------ laser (one spot, any source unit)
N.laser = { on = false, spot = nil }
function N.laserStop(silent, who)
  if N.laser.spot then pcall(function() N.laser.spot:destroy() end) end
  N.laser.spot = nil
  N.laser.on = false
  if not silent then N.msg((who or "PONTIAC") .. ": Terminate, laser off.", 10) end
end

-- aimFn() returns a point (with y) to lase, or nil to stop
function N.laserStart(srcName, aimFn, code, who, onStop)
  N.laserStop(true)
  N.laser.on = true
  N.laser.src, N.laser.aim, N.laser.code = srcName, aimFn, code
  timer.scheduleFunction(function(_, t)
    if not N.laser.on then return nil end
    local src = Unit.getByName(srcName)
    local aim = aimFn()
    if not src or not src:isExist() or not aim then
      N.laserStop(true)
      if onStop then onStop() end
      return nil
    end
    local a = { x = aim.x, y = aim.y + 2, z = aim.z }
    if not land.isVisible(src:getPoint(), a) then return t + 1 end
    if N.laser.spot then N.laser.spot:setPoint(a)
    else N.laser.spot = Spot.createLaser(src, { x = 0, y = -2, z = 0 }, a, code) end
    return t + 1
  end, nil, timer.getTime() + 0.5)
end

------------------------------------------------------------------ CAP commit
-- MAGIC commits the CAP (cap.lua); the strike lead can only request cover.
function N.requestCAP()
  if not CAPCTL or not CAPCFG.REQ then N.msg("MAGIC: Negative, no CAP available.", 10) return end
  CAPCTL.request(CAPCFG.REQ, CAPCFG.REQ_LABEL)
end

-- a Red group has met the commit criteria for the player's area
function N.capThreat(why)
  if CAPCTL and CAPCFG.REQ then CAPCTL.commit("threat", CAPCFG.REQ, CAPCFG.REQ_LABEL, why) end
end

function N.capSummary() return CAPCTL and CAPCTL.summaryLine() or "" end


-- where a lost player's pilot is: "land" (ejected over land: needs a rescue), "water" (ejected over the sea:
-- picked up by a Navy helicopter, no rescue mission) or "killed" (no ejection)
function N.lossKind(e)
  if e.id ~= world.event.S_EVENT_EJECTION then return "killed" end
  local ok, p = pcall(e.initiator.getPoint, e.initiator)
  if not ok or not p or not land.getSurfaceType or not land.SurfaceType then return "land" end
  local ok2, st = pcall(land.getSurfaceType, { x = p.x, y = p.z })
  if ok2 and (st == land.SurfaceType.WATER or st == land.SurfaceType.SHALLOW_WATER) then return "water" end
  return "land"
end

local function rescueLines_(kinds, file)
  local n = { land = 0, water = 0, killed = 0 }
  for _, k in pairs(kinds) do n[k] = n[k] + 1 end
  local out = ""
  if n.land > 0 then out = out .. "\nAlso fly " .. file .. " to bring the downed pilot home." end
  if n.water > 0 then out = out .. "\nThe pilot who ejected over the water was picked up by a Navy helicopter. No rescue mission needed." end
  if n.killed > 0 then out = out .. "\nNo ejection was seen from the lost jet. There is no one to rescue." end
  return out, n.land > 0
end

-- summary lines about downed pilots, and whether a rescue mission follows
function N.rescue(file) return rescueLines_(N.rec.lossKind, file) end

------------------------------------------------------------------ recovery and clean-recovery tracking
N.rec = { airborne = {}, recovered = {}, lost = {}, lowFuel = {}, minFuel = 0.18, lossKind = {},
          carrier = "CVN-74 Stennis", summaryDone = false }

function N.cleanRecovery()
  local clean, why = true, {}
  for n in pairs(N.rec.airborne) do
    if N.rec.lost[n] then clean = false; why[#why + 1] = n .. " " .. N.rec.lost[n] end
    if N.rec.lowFuel[n] then
      clean = false
      why[#why + 1] = string.format("%s landed with %d%% fuel", n, math.floor(N.rec.lowFuel[n] * 100 + 0.5))
    end
  end
  return clean, why
end

function N.anyLost()
  for _ in pairs(N.rec.lost) do return true end
  return false
end

-- calls N.onAllDown() once every jet that launched has trapped or been lost (or when forced)
function N.recCheck(force)
  if N.rec.summaryDone then return end
  local any = false
  for n in pairs(N.rec.airborne) do
    any = true
    if not N.rec.recovered[n] and not N.rec.lost[n] and not force then return end
  end
  if not any and not force then return end
  N.rec.summaryDone = true
  if N.onAllDown then N.onAllDown() end
end

------------------------------------------------------------------ single event dispatcher
N.hooks = {}
function N.on(fn) N.hooks[#N.hooks + 1] = fn end
N.handler = {}
function N.handler:onEvent(e)
  if not e then return end
  -- recovery bookkeeping first
  if e.initiator then
    local pname = N.playerName(e.initiator)
    if pname then
      if e.id == world.event.S_EVENT_TAKEOFF then
        N.rec.airborne[pname] = e.initiator:getName()
      elseif e.id == world.event.S_EVENT_CRASH or e.id == world.event.S_EVENT_EJECTION or e.id == world.event.S_EVENT_PILOT_DEAD then
        if not N.rec.lost[pname] and not N.rec.recovered[pname] then
          N.rec.lost[pname] = (e.id == world.event.S_EVENT_EJECTION) and "ejected" or "lost"
          N.rec.lossKind[pname] = N.lossKind(e)
          N.rec.airborne[pname] = N.rec.airborne[pname] or "?"
          N.msg("MAGIC: " .. pname .. " is down. Clean recovery is no longer possible.", 15)
        end
      elseif e.id == world.event.S_EVENT_LAND and e.place and e.place.getName
             and e.place:getName() == N.rec.carrier and not N.rec.recovered[pname] then
        N.rec.recovered[pname] = true
        N.rec.airborne[pname] = N.rec.airborne[pname] or e.initiator:getName()
        local okf, fuel = pcall(e.initiator.getFuel, e.initiator)
        if okf and fuel and fuel < N.rec.minFuel then N.rec.lowFuel[pname] = fuel end
        if N.onTrap then N.onTrap(pname, e.initiator:getName()) end
      end
    end
  end
  for _, fn in ipairs(N.hooks) do
    local ok, err = pcall(fn, e)
    if not ok then env.info("NG hook error: " .. tostring(err)) end
  end
  if e.id == world.event.S_EVENT_LAND or e.id == world.event.S_EVENT_CRASH or
     e.id == world.event.S_EVENT_EJECTION or e.id == world.event.S_EVENT_PILOT_DEAD then
    N.recCheck(false)
  end
end
world.addEventHandler(N.handler)
