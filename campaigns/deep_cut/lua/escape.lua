-- Operation Deep Cut: Escape (follow-up when a Deep Cut pilot ejects over land)
-- HATCHET has brought the downed pilot onto Senaki-Kolkhi, where Red has an F-14A readied for a ferry flight. Start it, get
-- airborne before the guards notice, and run for the boat with the Kutaisi alert behind you. CHEVY (cap.lua)
-- holds at the coast. The Navy was told an escape was coming, not when: the jet is unknown until the pilot
-- checks in with MAGIC (code word) or CHEVY gets eyes on it inside the ID zone, and Mother won't clear an
-- unknown Tomcat to land. Requires common.lua (NG) and cap.lua (CAPCTL).

ESC = ESC or {}
local T = ESC
local N = NG

-- __CONFIG__ (values are filled in by the mission builder)
T.cfg = T.cfg or {
  NAME = "OPERATION DEEP CUT: ESCAPE", START = 32400, DISCOVER = 480, TAKEOFF_NOTICE = 20, ALERT_REACT = 90,
  FIELD = "Senaki-Kolkhi", FIELD_AD = { "Senaki Guns North", "Senaki Guns South", "Senaki SA-13" },
  SOUTH_GROUP = "Red South", SOUTH_KIND = "two MiG-29s", SOUTH_BASE = "Kutaisi",
  JET = "Enfield 1-1", OUTCOME_FLAG = "90",
  CODE = "KESTREL", CARRIER = "CVN-74 Stennis", ID_R = 148160, VID_R = 3700, VID_S = 8,
  FLEET_WARN_R = 37040, FLEET_R = 18520, MISSILE_TOF = 20,
  PARK = { x = 0, z = 0 }, PARK_R = 30, CAUGHT_WINDOW = 60,
  GUARD_CAR = "Senaki Guard Car", GUARDS = "Senaki Guards", GUARD_TYPE = "Soldier AK",
}
local C = T.cfg
T.s = { found = nil, launched = nil, airborne = false, kills = 0, over = false,
        authed = nil, unknown = nil, identified = nil, vid = 0, warned = 0, waitSaid = nil,
        missile = nil, fleetShot = false, captured = nil }
local S = T.s

-- caught before wheels-up: still parked, they have you; already rolling, you get CAUGHT_WINDOW to be airborne
function T.capture(where)
  if S.captured or S.over then return end
  S.captured = where
  N.msg("HATCHET: They're all over the jet. It's over, Enfield. Hands where they can see them.", 20)
  N.recCheck(true)
end

-- the guards turn out: infantry where they found you (at the jet, or the empty parking spot if you're rolling),
-- and the BRDM-2 from the guard post driving at the jet, re-aimed every 5 s until you're airborne or it's over
function T.guardsOut(at)
  local units = {}
  for i, off in ipairs({ { 15, 12 }, { -12, 16 }, { 18, -14 }, { -16, -10 } }) do
    units[i] = { name = C.GUARDS .. " " .. i, type = C.GUARD_TYPE, x = at.x + off[1], y = at.z + off[2],
                 heading = 0, skill = "Average", playerCanDrive = false }
  end
  pcall(coalition.addGroup, country.id.RUSSIA, Group.Category.GROUND,
        { name = C.GUARDS, task = "Ground Nothing", units = units, route = { points = {} } })
  N.activate(C.GUARD_CAR)
  timer.scheduleFunction(function(_, t)
    if S.airborne or S.over then return nil end
    local u, g = N.liveUnit(C.JET), Group.getByName(C.GUARD_CAR)
    if not u or not g then return nil end
    local p = u:getPoint()
    pcall(function() g:getController():setTask({ id = "Mission", params = { route = { points = {
      { x = p.x, y = p.z, type = "Turning Point", action = "Off Road", speed = 25, ETA = 0, ETA_locked = false } } } } }) end)
    return t + 5
  end, nil, timer.getTime() + 1)
end

local function moved(u)
  local p = u:getPoint()
  local ok, v = pcall(u.getVelocity, u)
  local spd = (ok and v) and math.sqrt(v.x * v.x + v.z * v.z) or 0
  return N.dist(p, C.PARK) > C.PARK_R or spd > 2
end

function T.discover(why)
  if S.found then return end
  S.found = { t = timer.getAbsTime(), why = why }
  for _, g in ipairs(C.FIELD_AD) do N.setAD(g, true) end
  local u = N.liveUnit(C.JET)
  if u and N.playerName(u) and not S.airborne then
    if not moved(u) then
      T.guardsOut(u:getPoint())
      N.msg("HATCHET: Guards! Rifles up, at the ladder, and the armoured car's coming. They saw you in the cockpit (" .. why .. ").", 15)
      T.capture("still parked")
      return
    end
    T.guardsOut(C.PARK)
    N.msg("HATCHET: They've seen you (" .. why .. "). Guards running and an armoured car heading for the taxiway. " ..
          "You have about " .. C.CAUGHT_WINDOW .. " seconds to get that thing in the air. GO.", 15)
    timer.scheduleFunction(function()
      if not S.airborne then T.capture("still on the taxiway") end
      return nil
    end, nil, timer.getTime() + C.CAUGHT_WINDOW)
  else
    N.msg("HATCHET: They've seen you (" .. why .. "). The field's guns are waking up. GO.", 15)
  end
  timer.scheduleFunction(function()
    if S.over then return nil end
    S.launched = timer.getAbsTime()
    N.activate(C.SOUTH_GROUP)
    N.msg("MAGIC: Pop-up group, " .. C.SOUTH_KIND .. " off " .. C.SOUTH_BASE .. ", hot west after the Tomcat.", 20)
    N.capThreat(C.SOUTH_KIND .. " off " .. C.SOUTH_BASE .. ", chasing Enfield")
    return nil
  end, nil, timer.getTime() + C.ALERT_REACT)
end

------------------------------------------------------------------ identification
-- An unknown jet inbound from Red territory is a threat until it is identified. Checking in with MAGIC (code
-- word) identifies it at once. Staying silent costs you: CHEVY's intercept (cap.lua kind "ident") outranks the
-- MiGs, so the CAP is on you instead of on them; and inside FLEET_R of Mother an unidentified jet is engaged by
-- the fleet.
local LABEL = "the unknown Tomcat"
local function known() return S.authed or S.identified end
local function jet() local u = N.liveUnit(C.JET) return u and N.playerName(u) and u or nil end
local function mother() local cv = N.liveUnit(C.CARRIER) return cv and cv:getPoint() end

-- once the Tomcat is known, CHEVY comes off it: onto the MiGs if they're up, otherwise back to its station
local function freeChevy()
  local c = CAPCTL.cap
  if not (c and c.mode == "committed" and c.task and c.task.label == LABEL) then return end
  c.mode, c.task = nil, nil
  CAPCTL.pending = nil
  if S.launched and #N.liveUnits(C.SOUTH_GROUP) > 0 then
    N.capThreat(C.SOUTH_KIND .. " off " .. C.SOUTH_BASE .. ", chasing Enfield")
  else
    local g = Group.getByName(c.group)
    if g then pcall(function() g:getController():setTask(CAPCTL.airTask(CAPCFG.STATION, 40000)) end) end
    N.msg("MAGIC: " .. CAPCTL.call() .. ", the Tomcat's friendly. Reset CAP station.", 10)
  end
end

function T.checkIn()
  local u = jet()
  if not u or not S.airborne then N.msg("Nobody can hear you from the ground. Get airborne first.", 8) return end
  if S.authed then N.msg("MAGIC: You're authenticated already. Come home.", 8) return end
  S.authed = timer.getAbsTime()
  if S.missile then
    S.missile = nil
    N.msg("MOTHER: ABORT, ABORT! " .. C.CODE .. " authenticates. Missiles destructed. That was close, Enfield.", 15)
  end
  N.msg("MAGIC: Unknown Tomcat, authenticate. ... " .. C.CODE .. " is correct. Enfield, good to hear you.\n" ..
        "You're friendly on our scope and Mother has you cleared in. " .. CAPCTL.call() .. " is free to work the MiGs.", 20)
  freeChevy()
end

function T.commitIntercept(p)
  CAPCTL.commit("ident", { x = p.x, z = p.z }, LABEL, "unknown Tomcat inbound",
                { clear = function() return known() and true or false end, timeout = 1800, radius = 30000 })
end

-- CHEVY has to see you: steer it to the jet every 10 s while it is committed on the unknown
local function steer(gname, p)
  local g = Group.getByName(gname)
  if not g then return end
  pcall(function() g:getController():setTask({ id = "Mission", params = { route = { points = { {
    x = p.x, y = p.z, alt = math.max(p.y, 1000), alt_type = "BARO", speed = 300, type = "Turning Point", action = "Turning Point",
    task = { id = "ComboTask", params = { tasks = { { number = 1, auto = false, enabled = true, id = "EngageTargetsInZone",
      params = { point = { x = p.x, y = p.z }, x = p.x, y = p.z, zoneRadius = 30000, targetTypes = { "Air" },
                 noTargetTypes = {}, priority = 0 } } } } } } } } } }) end)
end

local function fleetEngage()
  S.missile = timer.getAbsTime()
  N.msg("MOTHER: Unknown Tomcat inside " .. math.floor(C.FLEET_R / 1852 + 0.5) .. " nm, not answering. ENGAGING. Birds away.", 15)
  timer.scheduleFunction(function()
    if not S.missile or known() then return nil end
    S.fleetShot = true
    local u = jet()
    if u then pcall(trigger.action.explosion, u:getPoint(), 150) end
    N.msg("MOTHER: Splash one unknown Tomcat.", 15)
    return nil
  end, nil, timer.getTime() + C.MISSILE_TOF)
end

function T.idTick(_, t)
  if S.over then return nil end
  local u, cvp = jet(), mother()
  if not u or not cvp or not S.airborne or known() then return t + 2 end
  local now = timer.getAbsTime()
  local p = u:getPoint()
  local d = N.dist(p, cvp)
  if not S.unknown and d < C.ID_R then
    S.unknown = now
    N.msg(string.format("MAGIC: Unknown Tomcat, %d nm east of Mother, inbound. Not squawking anything we know. " ..
          "Treating it as hostile until it's identified.\n%s, intercept and identify. Weapons hold on the Tomcat.",
          math.floor(d / 1852 + 0.5), CAPCTL.call()), 15)
    T.commitIntercept(p)
  end
  if S.unknown then
    local c = CAPCTL.cap
    if c and c.mode == "out" then
      if not S.waitSaid then
        S.waitSaid = true
        N.msg("MAGIC: Unknown Tomcat, there's nobody free to come and look at you. Authenticate, or stay clear of the fleet.", 15)
      end
    elseif c and (not c.mode or (c.task and c.task.label ~= LABEL and c.task.kind ~= "boat")) then
      T.commitIntercept(p)     -- idle, or on the MiGs: the unknown outranks them
    end
    if c and c.mode == "committed" and c.task and c.task.label == LABEL then
      if (t % 10) < 2 then steer(c.group, p) end
      local close = false
      for _, w in ipairs(N.liveUnits(c.group)) do
        if N.dist(w:getPoint(), p) < C.VID_R then close = true end
      end
      S.vid = close and (S.vid + 2) or 0
      if S.vid >= C.VID_S then
        S.identified = now
        if S.missile then S.missile = nil; N.msg("MOTHER: ABORT, ABORT! Missiles destructed.", 10) end
        N.msg("CHEVY: Tally one Tomcat, foreign paint. Pilot's waving, he's holding up a kneeboard: ENFIELD. Looks like ours.\n" ..
              "MAGIC: Copy, declaring the Tomcat friendly. Mother has you cleared in.", 20)
        freeChevy()
        return t + 2
      end
    end
  end
  if not S.missile and not S.fleetShot then
    if d < C.FLEET_R then fleetEngage()
    elseif d < C.FLEET_WARN_R and now - S.warned > 30 then
      S.warned = now
      N.msg(string.format("MOTHER: Unknown Tomcat, you are approaching the fleet's missile zone. Identify yourself or turn away. " ..
            "We engage inside %d nm.", math.floor(C.FLEET_R / 1852 + 0.5)), 10)
    end
  end
  return t + 2
end

function T.status()
  local now = timer.getAbsTime()
  local line
  if S.found then line = "Red knows: " .. S.found.why .. "." .. (S.launched and " Fighters airborne." or " Fighters launching.")
  else line = "Not seen yet. Guards expected at about " .. N.hms(C.START + C.DISCOVER) .. "L (" ..
             N.mmss(C.START + C.DISCOVER - now):sub(2) .. ")." end
  local id = S.authed and "Authenticated with MAGIC." or (S.identified and "Identified by CHEVY." or
             ("Unknown to the Navy: check in with MAGIC (code word " .. C.CODE .. ")."))
  N.msg("Time " .. N.clock(now) .. "\n" .. line .. "\n" .. id .. "\n" .. N.capSummary(), 15)
end

N.on(function(e)
  if not e.initiator then return end
  local pname = N.playerName(e.initiator)
  if e.id == world.event.S_EVENT_TAKEOFF and pname then
    S.airborne = true
    N.msg("HATCHET: Wheels up, nice. They'll have heard that.", 10)
    timer.scheduleFunction(function() T.discover("the takeoff") return nil end, nil, timer.getTime() + C.TAKEOFF_NOTICE)
  elseif e.id == world.event.S_EVENT_SHOT and pname and not S.found then
    T.discover("gunfire on the field")
  elseif e.id == world.event.S_EVENT_DEAD and e.initiator.getName then
    local ok, n = pcall(e.initiator.getName, e.initiator)
    if ok and n and n:sub(1, #C.SOUTH_GROUP) == C.SOUTH_GROUP then S.kills = S.kills + 1 end
  end
end)

function N.onTrap(pname) N.msg("MOTHER: " .. pname .. " aboard in somebody else's Tomcat. Welcome home.", 20) end

function N.onAllDown()
  if S.over then return end
  S.over = true
  local home, kind = false, nil
  for p in pairs(N.rec.airborne) do
    if N.rec.recovered[p] and not N.rec.lost[p] then home = true end
    kind = N.rec.lossKind[p] or kind
  end
  local outcome, why
  if S.captured then outcome, why = "FAILURE", "Captured on the ramp, " .. S.captured .. ". HATCHET got away; you didn't."
  elseif S.fleetShot then outcome, why = "FAILURE", "Shot down by our own fleet, silent and unidentified. The Navy fished you out; the Captain wants a word."
  elseif home then outcome, why = "SUCCESS", "The pilot is home, in a jet Red had to watch leave."
  elseif kind == "water" then outcome, why = "PARTIAL", "Down over the water: the Navy picks the crew up. The jet is gone."
  else outcome, why = "FAILURE", "Down over Red territory again." end
  trigger.action.setUserFlag(C.OUTCOME_FLAG, ({ SUCCESS = 1, PARTIAL = 2, FAILURE = 3 })[outcome])
  N.msg(C.NAME .. " - SUMMARY\n" ..
    (S.found and ("Seen at " .. N.hms(S.found.t) .. "L: " .. S.found.why .. ".") or "Never seen.") .. "\n" ..
    (S.authed and ("Checked in with MAGIC at " .. N.hms(S.authed) .. "L.") or
     (S.identified and ("Identified by CHEVY at " .. N.hms(S.identified) .. "L.") or "Never identified.")) .. "\n" ..
    string.format("%s: %d shot down.\n", C.SOUTH_KIND, S.kills) .. N.capSummary() ..
    "\n\nOUTCOME: " .. outcome .. ". " .. why, 90)
end

function T.init()
  if C.CARRIER then N.rec.carrier = C.CARRIER end
  for _, g in ipairs(C.FIELD_AD) do N.setAD(g, false) end
  timer.scheduleFunction(function()
    if not S.found then T.discover(S.airborne and "the takeoff" or "a guard on his rounds") end
    return nil
  end, nil, timer.getTime() + C.DISCOVER)
  local root = missionCommands.addSubMenuForCoalition(N.BLUE, "Escape")
  missionCommands.addCommandForCoalition(N.BLUE, "Status", root, T.status)
  missionCommands.addCommandForCoalition(N.BLUE, "Check in with MAGIC (" .. C.CODE .. ")", root, T.checkIn)
  timer.scheduleFunction(T.idTick, nil, timer.getTime() + 2)
  missionCommands.addCommandForCoalition(N.BLUE, "Mission summary now", root, function() N.rec.summaryDone = false; N.recCheck(true) end)
  N.msg(C.NAME .. ". You're in the Tomcat on the " .. C.FIELD .. " ramp. HATCHET thinks the guards check this end at about " ..
        N.hms(C.START + C.DISCOVER) .. "L. Be gone by then. Once airborne, check in with MAGIC: code word " ..
        C.CODE .. ". radio menu > F10. Other > Escape.", 25)
end

T.init()
