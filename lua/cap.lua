-- CAPCTL: controller-run CAP for the Narrow Gate campaign. Pure DCS scripting engine.
--
-- MAGIC commits the CAP on briefed criteria (a mission script calls CAPCTL.commit when a Red group meets
-- them, and any Red aircraft near the boat triggers fleet defence on its own). The strike lead can only
-- REQUEST cover; MAGIC approves or says why not. After a commit the CAP resets to its station when the
-- picture is clean. When the CAP is Winchester, Bingo, down to one jet or lost, Mother launches the
-- alert-5 (UZI) to relieve it. There is one alert section.
--
-- Config: the builder defines the global CAPCFG before this file runs (see common_build.cap_lua_cfg).

CAPCTL = CAPCTL or {}
local K = CAPCTL
local BLUE = coalition.side.BLUE
local RED = coalition.side.RED
local atan2 = math.atan2 or math.atan

local function cfg() return CAPCFG end
local function msg(text, secs) trigger.action.outTextForCoalition(BLUE, text, secs or 15) end
local function hms(abs)
  abs = math.floor(abs + 0.5) % 86400
  return string.format("%02d:%02d:%02d", math.floor(abs / 3600), math.floor(abs % 3600 / 60), abs % 60)
end
local function now() return timer.getAbsTime() end
local function d2(a, b) local dx, dz = a.x - b.x, a.z - b.z return math.sqrt(dx * dx + dz * dz) end

local PRIORITY = { boat = 3, threat = 2, request = 1 }

K.cap = nil            -- the CAP on station: { group, call, mode, task, relief, reliefCalled, reliefDue, wasPair }
K.history = {}         -- one line per event, for the mission summary
K.pending = nil        -- a commit MAGIC could not serve because the CAP was busy

------------------------------------------------------------------ unit helpers
local function live(gname)
  local g = gname and Group.getByName(gname)
  local out = {}
  if not g or not g:isExist() then return out end
  for _, u in ipairs(g:getUnits()) do
    if u and u:isExist() and u:getLife() > 1 then out[#out + 1] = u end
  end
  return out
end
K.live = live

local function missiles(gname)
  local n = 0
  for _, u in ipairs(live(gname)) do
    local ok, ammo = pcall(u.getAmmo, u)
    if ok and ammo then
      for _, a in ipairs(ammo) do
        local d = a.desc or {}
        if d.category == Weapon.Category.MISSILE and d.missileCategory == Weapon.MissileCategory.AAM then
          n = n + (a.count or 0)
        end
      end
    end
  end
  return n
end
K.missiles = missiles

local function fuel(gname)
  local f = 1
  for _, u in ipairs(live(gname)) do
    local ok, v = pcall(u.getFuel, u)
    if ok and v and v < f then f = v end
  end
  return f
end

-- live, active Red aircraft within r metres of p
function K.redAirNear(p, r)
  local out = {}
  local ok, groups = pcall(coalition.getGroups, RED, Group.Category.AIRPLANE)
  if not ok or not groups then return out end
  for _, g in ipairs(groups) do
    for _, u in ipairs(g:getUnits() or {}) do
      local okA, active = pcall(u.isActive, u)
      if u:isExist() and u:getLife() > 1 and (not okA or active) and d2(u:getPoint(), p) <= r then
        out[#out + 1] = u
      end
    end
  end
  return out
end

------------------------------------------------------------------ tasking
local function airTask(pt, radius, speed)
  local c = cfg()
  return {
    id = "Mission",
    params = { route = { points = { {
      x = pt.x, y = pt.z, alt = c.ALT, alt_type = "BARO", speed = speed or c.SPD,
      type = "Turning Point", action = "Turning Point",
      task = { id = "ComboTask", params = { tasks = {
        { number = 1, auto = false, enabled = true, id = "EngageTargetsInZone",
          params = { point = { x = pt.x, y = pt.z }, x = pt.x, y = pt.z, zoneRadius = radius,
                     targetTypes = { "Air" }, noTargetTypes = {}, priority = 0 } },
        { number = 2, auto = false, enabled = true, id = "Orbit",
          params = { pattern = "Circle", point = { x = pt.x, y = pt.z }, altitude = c.ALT, speed = speed or c.SPD } },
      } } },
    } } } },
  }
end
K.airTask = airTask

local function setTask(gname, t)
  local g = Group.getByName(gname)
  if not g or #live(gname) == 0 then return false end
  return pcall(function() g:getController():setTask(t) end)
end

local function carrierPoint()
  local cv = Unit.getByName(cfg().CARRIER)
  if cv and cv:isExist() then return cv:getPoint(), cv end
  return nil
end

local function recover(gname)
  local p, cv = carrierPoint()
  if not p then return end
  local ok, id = pcall(cv.getID, cv)
  setTask(gname, { id = "Mission", params = { route = { points = {
    { x = p.x, y = p.z, alt = 600, alt_type = "BARO", speed = 150, type = "Land", action = "Landing",
      linkUnit = ok and id or nil, helipadId = ok and id or nil },
  } } } })
end

------------------------------------------------------------------ status for other scripts
function K.status()
  local c = K.cap
  if not c or c.mode == "out" then return "out" end
  return c.mode or "station"
end

function K.call() return K.cap and K.cap.call or "Chevy" end

-- radio name of whoever leads the CAP now ("Chevy 1-1", or "Chevy 1-2" if the lead is gone)
local function lead(c)
  local a = live(c.group)
  if #a == 0 then return c.call end
  local ok, n = pcall(a[1].getName, a[1])
  return ok and n or (c.call .. " 1-1")
end

-- one line for a radio call: who covers you now
function K.advice()
  local c = K.cap
  if not c then return "" end
  if c.mode == "out" then
    if c.reliefDue then return "\nNo CAP on station: Uzi due about " .. hms(c.reliefDue) .. "L." end
    return "\nNo CAP available."
  end
  if cfg().FLEET_ONLY then return "\n" .. c.call .. " is on fleet defence and will not come to you." end
  if c.mode then return "\n" .. c.call .. " is committed on " .. c.task.label .. "." end
  return "\n" .. c.call .. " is on CAP. MAGIC will commit it on the briefed criteria; you can request cover from F10."
end

------------------------------------------------------------------ commits
-- kind: "boat" | "threat" | "request"; point {x,z}; label for radio; why: who triggered it;
-- clear(): optional, true when the threat is over (default: no Red air within radius of the point)
function K.commit(kind, point, label, why, opts)
  opts = opts or {}
  local c = K.cap
  local req = { kind = kind, point = point, label = label, why = why, clear = opts.clear,
                radius = opts.radius or 60000, at = now(), timeout = opts.timeout or 900 }
  if not c then return false end
  if c.mode == "out" then
    if kind ~= "request" then
      msg("MAGIC: " .. why .. ". No CAP to commit" ..
          (c.reliefDue and ("; Uzi due on station about " .. hms(c.reliefDue) .. "L.") or "."), 15)
      K.pending = req
    end
    return false
  end
  if cfg().FLEET_ONLY and kind ~= "boat" then
    if kind ~= "request" then
      msg("MAGIC: " .. why .. ". " .. c.call .. " stays on fleet defence: CAG's orders, threats to the boat only. " ..
          "You are on your own.", 15)
    end
    return false, "fleet"
  end
  if c.mode and c.task.label == label and PRIORITY[kind] >= PRIORITY[c.task.kind] then
    -- already there: take on the new threat in place
    c.task.kind, c.task.why, c.task.clear, c.task.at = kind, why, req.clear, req.at
    c.task.radius, c.task.timeout, c.task.quietSince = req.radius, req.timeout, nil
    msg("MAGIC: " .. c.call .. ", new group: " .. why:sub(1, 1):lower() .. why:sub(2) .. ". You're already there: stay on " .. label .. ".", 15)
    return true
  end
  if c.mode then
    if PRIORITY[kind] > PRIORITY[c.task.kind] then
      msg("MAGIC: " .. c.call .. ", break off " .. c.task.label .. ". Divert: " .. why .. ".", 15)
    else
      if kind ~= "request" then
        msg("MAGIC: " .. why .. ". " .. c.call .. " is committed on " .. c.task.label ..
            "; no CAP for " .. label .. " until it resets.", 15)
        K.pending = req
      end
      return false, "busy"
    end
  end
  c.mode = "committed"
  c.task = req
  K.history[#K.history + 1] = c.call .. " committed: " .. label
  setTask(c.group, airTask(point, req.radius, cfg().SPD * 1.15))
  if cfg().FLAG then trigger.action.setUserFlag(cfg().FLAG, true) end
  if kind ~= "request" then
    msg("MAGIC: " .. lead(c) .. ", commit. " .. why .. ".\nEnfield, " .. c.call ..
        " is committing on " .. label .. ".", 15)
  end
  return true
end

-- the strike lead asks for cover over `point`
function K.request(point, label)
  local c = K.cap
  if not c then msg("MAGIC: Negative, no CAP available.", 10) return end
  if c.mode == "out" then
    msg("MAGIC: Negative, no CAP on station." ..
        (c.reliefDue and (" Uzi is on the way, on station about " .. hms(c.reliefDue) .. "L.") or ""), 12)
    return
  end
  if cfg().FLEET_ONLY then
    msg("MAGIC: Negative. CAG has " .. c.call .. " on fleet defence. They engage only threats to the boat.", 12)
    return
  end
  if c.mode then
    msg("MAGIC: Negative, " .. c.call .. " is committed on " .. c.task.label .. ".", 12)
    return
  end
  local threats = K.redAirNear(point, 90000)
  K.commit("request", point, label, "Enfield requests cover", { timeout = #threats > 0 and 900 or 480 })
  msg("MAGIC: Copy, Enfield. " .. lead(c) .. ((#live(c.group) == 1) and ", single Hornet," or ", two Hornets,") ..
      " off CAP station to cover " .. label .. ". " ..
      (#threats > 0 and "Bandits in the area." or "Picture is clean there; " .. c.call .. " resets in about 8 minutes if it stays that way."), 15)
end

------------------------------------------------------------------ relief
function K.launchRelief()
  local c = cfg()
  local base = carrierPoint() or c.STATION
  local r = atan2(c.STATION.z - base.z, c.STATION.x - base.x)
  local units = {}
  for i = 1, 2 do
    local ox = 2000 * math.cos(r) - (i - 1) * 150 * math.sin(r)
    local oz = 2000 * math.sin(r) + (i - 1) * 150 * math.cos(r)
    units[i] = { name = "Uzi 1-" .. i, type = "FA-18C_hornet", skill = "Good",
                 x = base.x + ox, y = base.z + oz, alt = 450, alt_type = "BARO", speed = 150, heading = r,
                 payload = { pylons = c.PYLONS, fuel = 4900, flare = 60, chaff = 60, gun = 100 },
                 callsign = { 3, 1, i, name = "Uzi1" .. i }, onboard_num = tostring(300 + i) }
  end
  local st = airTask(c.STATION, 40000).params.route.points[1]
  local data = { name = "Uzi", task = "CAP", units = units, route = { points = {
    { x = units[1].x, y = units[1].y, alt = 450, alt_type = "BARO", speed = 150, type = "Turning Point",
      action = "Turning Point", task = { id = "ComboTask", params = { tasks = {} } } },
    st } } }
  local ok = pcall(coalition.addGroup, country.id.USA, Group.Category.AIRPLANE, data)
  K.cap = { group = "Uzi", call = "Uzi", mode = nil, relief = true, reliefCalled = true }
  if ok then
    K.history[#K.history + 1] = "Uzi launched off the alert"
    msg("MAGIC: Uzi 1-1, two Hornets off the alert, climbing to CAP station. Uzi is the CAP from here.", 15)
  else
    K.cap.mode = "out"
    msg("MAGIC: Mother can't launch the alert. No CAP.", 15)
  end
end

function K.callRelief(why, gapText)
  local c = K.cap
  local C = cfg()
  c.reliefCalled = true
  c.reliefDue = now() + C.ALERT_DELAY + C.ALERT_TRANSIT
  msg("MAGIC: " .. why .. ". Mother is launching the alert-5, Uzi, two Hornets.\n" ..
      gapText .. ", about " .. hms(c.reliefDue) .. "L.", 20)
  local old = c.group
  timer.scheduleFunction(function()
    K.launchRelief()
    timer.scheduleFunction(function()
      if #live(old) > 0 then recover(old) end
      return nil
    end, nil, timer.getTime() + C.ALERT_TRANSIT)
    return nil
  end, nil, timer.getTime() + C.ALERT_DELAY)
end

------------------------------------------------------------------ watch
local function threatOver(t)
  if t.clear then
    local ok, v = pcall(t.clear)
    if ok and v then return true end
    if ok and v == false then return false end
  end
  if now() - t.at > t.timeout then return true end
  if #K.redAirNear(t.point, t.radius) > 0 then
    t.quietSince = nil
    return false
  end
  t.quietSince = t.quietSince or now()
  local quiet = now() - t.quietSince > 60
  if t.kind == "request" then return quiet and now() - t.at > 480 end
  return quiet
end

function K.tick(_, t)
  local c = K.cap
  local C = cfg()
  if not c or c.mode == "out" then return t + 5 end
  local alive = live(c.group)
  local m = missiles(c.group)

  local why
  if #alive == 0 then why = c.call .. " is down"
  elseif m <= C.MIN_MISSILES then why = c.call .. " is Winchester, RTB"
  elseif fuel(c.group) < C.BINGO then why = c.call .. " is Bingo, RTB" end
  if #alive >= 2 then c.wasPair = true end

  if why then
    K.history[#K.history + 1] = why
    if #alive > 0 then recover(c.group) end
    c.mode = "out"
    if c.relief then
      msg("MAGIC: " .. why .. ". No more alert jets on Mother. No CAP for the rest of the mission.", 15)
    elseif c.reliefCalled then
      msg("MAGIC: " .. why .. ". No CAP until Uzi is on station, about " .. hms(c.reliefDue) .. "L.", 15)
    else
      K.callRelief(why, "No CAP until Uzi is on station")
    end
    return t + 5
  end

  if #alive == 1 and c.wasPair and not c.reliefCalled and not c.relief then
    K.history[#K.history + 1] = c.call .. " lost a jet"
    K.callRelief(c.call .. " is down to one jet", "A single " .. c.call .. " holds until Uzi is on station")
  end

  -- fleet defence: anything Red near the boat is committed on, whatever the CAP is doing
  local cvp = carrierPoint()
  if cvp and not (c.mode and c.task.kind == "boat") then
    local near = K.redAirNear(cvp, C.BOAT_R)
    if #near > 0 then
      K.commit("boat", cvp, "the boat", #near .. " bandit" .. (#near > 1 and "s" or "") ..
               " inside " .. math.floor(C.BOAT_R / 1852 + 0.5) .. " nm of Mother", { radius = C.BOAT_R + 20000 })
    end
  end

  if not c.mode and K.pending then
    local p = K.pending
    K.pending = nil
    if not threatOver(p) then
      K.commit(p.kind, p.point, p.label, p.why, { clear = p.clear, radius = p.radius, timeout = p.timeout })
    end
    return t + 5
  end

  if c.mode and threatOver(c.task) then
    local done = c.task
    c.mode, c.task = nil, nil
    local p = K.pending
    K.pending = nil
    if p and not threatOver(p) then
      msg("MAGIC: " .. c.call .. ", " .. done.label .. " is clean. Re-commit: " .. p.why .. ". " ..
          c.call .. " has " .. m .. " missiles.", 15)
      K.commit(p.kind, p.point, p.label, p.why, { clear = p.clear, radius = p.radius, timeout = p.timeout })
    else
      setTask(c.group, airTask(C.STATION, 40000))
      msg("MAGIC: " .. c.call .. ", " .. done.label .. " is clean. Reset CAP station. " ..
          c.call .. " has " .. m .. " missiles.", 15)
    end
  end
  return t + 5
end

function K.summaryLine()
  if #K.history == 0 then return "CAP: not needed." end
  return "CAP: " .. table.concat(K.history, "; ") .. "."
end

function K.init()
  local C = cfg()
  K.cap = { group = C.GROUP, call = C.CALL or "Chevy", mode = nil }
  timer.scheduleFunction(K.tick, nil, timer.getTime() + 5)
end

K.init()
