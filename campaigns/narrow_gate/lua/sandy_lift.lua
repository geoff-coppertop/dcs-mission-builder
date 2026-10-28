-- Operation Sandy Lift (Narrow Gate campaign, rescue branch)
-- Rescue escort: sanitise the area, call DODGE (SH-60B) in from F10, cover the pickup, bring the survivor home.
-- Requires common.lua.

SL = SL or {}
local T = SL
local N = NG

T.cfg = T.cfg or {
  START = 30600, SURVIVOR = "Survivor", SURVIVOR_GROUP = "Survivor",
  HELO_GROUP = "Dodge", HELO_UNIT = "Dodge 1-1", HELO_FLAG = "52",
  SEARCH_GROUP = "Search Party", SEARCH_TIME = 30900, SEARCH_SPEED = 2.5,
  THREAT_GROUPS = { "Depot AAA", "Search Party" }, MIG_GROUP = "Red CAP", MIG_TIME = 32100,
  CAP_GROUP = "Chevy", CAP_FLAG = "51", JTAC_UNIT = "Pontiac", LASER_CODE = 1688,
  LZ = { x = 0, z = 0 }, CAPTURE_R = 300, PICKUP_R = 250, BOARD_S = 40, THREAT_R = 5000,
  HOLD = { x = 0, z = 0 }, HELO_MS = 60, JETS = { "Enfield 1-1", "Enfield 1-2" },
  WHERE = "near Ochamchire", TITLE = "OPERATION SANDY LIFT", MIG_KIND = "MiG-21s",
}
local C = T.cfg

T.s = { helo = "HOLDING", survivor = "DOWN", calledAt = nil, threatsAtCall = 0, jetsDown = false,
        summaryDone = false, startThreats = 0, searchMoving = false }
local S = T.s

------------------------------------------------------------------ helpers
local function threats()
  local out = {}
  for _, g in ipairs(C.THREAT_GROUPS) do
    for _, u in ipairs(N.liveUnits(g)) do
      local d = N.dist(u:getPoint(), C.LZ)
      if d <= C.THREAT_R then out[#out + 1] = { u = u, d = d } end
    end
  end
  table.sort(out, function(a, b) return a.d < b.d end)
  return out
end
local function helo() return N.liveUnit(C.HELO_UNIT) end
local function survivor() return N.liveUnit(C.SURVIVOR) end
local function threatLine(list, max)
  local parts = {}
  for i = 1, math.min(#list, max or 4) do
    local ok, tn = pcall(list[i].u.getTypeName, list[i].u)
    parts[#parts + 1] = string.format("%s %.1f km %s", ok and tn or "vehicle", list[i].d / 1000,
                                      N.compass(N.bearing(C.LZ, list[i].u:getPoint())))
  end
  return table.concat(parts, "; ")
end

------------------------------------------------------------------ summary (needs jets down AND helo resolved)
function T.trySummary(force)
  if S.summaryDone then return end
  local heloDone = S.helo == "ABOARD" or S.helo == "LOST" or S.survivor == "CAPTURED"
  if not force and not (S.jetsDown and heloDone) then return end
  S.summaryDone = true
  local rescued = S.survivor == "ABOARD" and S.helo == "ABOARD"
  local why
  if rescued then why = "Dodge is aboard Mother with the survivor."
  elseif S.survivor == "CAPTURED" then why = "The search party reached the survivor first."
  elseif S.helo == "LOST" then why = "Dodge was shot down."
  elseif S.survivor == "ABOARD" then why = "The survivor is aboard Dodge, but Dodge is not home yet."
  else why = "Dodge never made the pickup." end
  local clean, reasons = N.cleanRecovery()
  local searchLeft = #N.liveUnits(C.SEARCH_GROUP)
  trigger.action.setUserFlag("92", rescued and 1 or 0)
  N.msg("MISSION SUMMARY - " .. C.TITLE .. "\n" ..
    "Primary: survivor " .. (rescued and "RESCUED" or "NOT RESCUED") .. ". " .. why .. "\n" ..
    string.format("Threats near the LZ when Dodge was called: %s. Search party: %s.\n",
      S.calledAt and tostring(S.threatsAtCall) or "Dodge never called",
      searchLeft == 0 and "destroyed" or (searchLeft .. " still alive")) ..
    "Secondary - Clean recovery: " .. (clean and "ACHIEVED." or ("FAILED (" .. table.concat(reasons, "; ") .. ").")) ..
    "\n" .. N.capSummary() ..
    "\n\nOUTCOME: " .. (rescued and "SUCCESS" or "FAILURE") .. ".", 90)
end
function N.onAllDown() S.jetsDown = true; T.trySummary(false) end

------------------------------------------------------------------ search party
function T.startSearch()
  local g = Group.getByName(C.SEARCH_GROUP)
  if not g or not g:isExist() or #g:getUnits() == 0 then return end
  S.searchMoving = true
  local p = g:getUnits()[1]:getPoint()
  g:getController():setTask({ id = "Mission", params = { route = { points = {
    { x = p.x, y = p.z, type = "Turning Point", action = "Off Road", speed = C.SEARCH_SPEED },
    { x = C.LZ.x, y = C.LZ.z, type = "Turning Point", action = "Off Road", speed = C.SEARCH_SPEED } } } } })
  local d = N.dist(p, C.LZ)
  N.msg(string.format("PONTIAC: Red search party moving toward the survivor from the %s, %.1f km out. At that pace they reach him in about %d minutes.",
        N.compass(N.bearing(C.LZ, p)), d / 1000, math.floor(d / C.SEARCH_SPEED / 60 + 0.5)), 20)
end

------------------------------------------------------------------ helo
function T.callDodge()
  if S.helo ~= "HOLDING" then N.msg("DODGE: Already committed.", 8) return end
  if S.survivor == "CAPTURED" then N.msg("DODGE: Negative, the survivor has been captured.", 10) return end
  local h = helo()
  if not h then N.msg("DODGE: Dodge is not available.", 10) return end
  local list = threats()
  S.helo, S.calledAt, S.threatsAtCall = "INBOUND", timer.getAbsTime(), #list
  trigger.action.setUserFlag(C.HELO_FLAG, true)
  local eta = N.dist(h:getPoint(), C.LZ) / C.HELO_MS / 60
  N.msg(string.format("DODGE: Dodge 1-1 pushing for the survivor, about %d minutes. ", math.floor(eta + 0.5)) ..
        (#list == 0 and "Sandy, thanks for the clean LZ." or
         string.format("Be advised, %d threat%s still within %d km of the LZ: %s.", #list, #list > 1 and "s" or "",
                       C.THREAT_R / 1000, threatLine(list, 3))), 20)
end

function T.boarded()
  if S.helo ~= "ON_GROUND" or S.survivor ~= "DOWN" then return end
  local s = survivor()
  if s then pcall(function() s:destroy() end) end
  S.survivor, S.helo = "ABOARD", "OUTBOUND"
  N.msg("DODGE: Survivor aboard! Lifting, heading for Mother. Sandy, cover our egress west.", 20)
end

function T.tick(_, t)
  -- capture
  if S.survivor == "DOWN" then
    for _, u in ipairs(N.liveUnits(C.SEARCH_GROUP)) do
      if N.dist(u:getPoint(), C.LZ) <= C.CAPTURE_R then
        S.survivor = "CAPTURED"
        local s = survivor()
        if s then pcall(function() s:destroy() end) end
        N.msg("PONTIAC: The search party has reached the survivor. He's been taken. Rescue is OFF.", 25)
        T.trySummary(false)
        break
      end
    end
  end
  -- helo on the ground at the LZ
  local h = helo()
  if h and S.helo == "INBOUND" then
    local p = h:getPoint()
    local agl = p.y - land.getHeight({ x = p.x, y = p.z })
    if N.dist(p, C.LZ) <= C.PICKUP_R and agl < 5 then
      S.helo = "ON_GROUND"
      N.msg("DODGE: Wheels down at the survivor. " .. C.BOARD_S .. " seconds to get him aboard. Keep them off us, Sandy!", 15)
      timer.scheduleFunction(function() if helo() then T.boarded() end return nil end, nil, timer.getTime() + C.BOARD_S)
    end
  end
  if S.summaryDone then return nil end
  return t + 2
end

------------------------------------------------------------------ F10
function T.lzReport()
  local list = threats()
  local s = survivor()
  local loc = ""
  if s then local ll, mgrs = N.coord(s:getPoint()); loc = "Survivor: " .. mgrs .. "  (" .. ll .. ")\n" end
  local sp = N.liveUnits(C.SEARCH_GROUP)
  local spline = #sp == 0 and "Search party destroyed." or
    string.format("Search party: %d, %.1f km from the survivor%s.", #sp, N.dist(sp[1]:getPoint(), C.LZ) / 1000,
                  S.searchMoving and ", closing" or ", searching")
  N.msg("PONTIAC: LZ report.\n" .. loc .. spline .. "\n" ..
        (#list == 0 and "No ground threats within " .. C.THREAT_R / 1000 .. " km of the LZ: LZ is clean."
         or string.format("%d ground threat%s within %d km: %s.", #list, #list > 1 and "s" or "", C.THREAT_R / 1000, threatLine(list, 5))) ..
        "\nDodge: " .. S.helo .. ".", 30)
end

function T.laserThreat()
  local list = threats()
  if #list == 0 then N.msg("PONTIAC: No threats to lase near the LZ.", 8) return end
  local target = list[1].u:getName()
  N.laserStart(C.JTAC_UNIT, function() local u = N.liveUnit(target); return u and u:getPoint() or nil end, C.LASER_CODE,
               "PONTIAC", function() N.msg("PONTIAC: Target destroyed, laser off.", 8) end)
  local ok, tn = pcall(list[1].u.getTypeName, list[1].u)
  N.msg("PONTIAC: Laser on the nearest threat to the LZ, " .. (ok and tn or "vehicle") .. ", code " .. C.LASER_CODE .. ".", 12)
end

function T.smoke()
  local s = survivor()
  if not s then N.msg("PONTIAC: No survivor to mark.", 8) return end
  local p = s:getPoint()
  trigger.action.smoke({ x = p.x + 10, y = p.y, z = p.z }, trigger.smokeColor.Green)
  N.msg("SURVIVOR: Green smoke out.", 10)
end

------------------------------------------------------------------ events
N.on(function(e)
  if not e.initiator then return end
  local ok, nm = pcall(e.initiator.getName, e.initiator)
  if not ok or nm ~= C.HELO_UNIT then return end
  if e.id == world.event.S_EVENT_LAND then
    if e.place and e.place.getName and e.place:getName() == N.rec.carrier then
      if S.survivor == "ABOARD" then
        S.helo = "ABOARD"
        N.msg("MOTHER: Dodge is aboard with the survivor. Good work, Sandy.", 20)
        T.trySummary(false)
      end
    elseif S.helo == "INBOUND" and N.dist(e.initiator:getPoint(), C.LZ) <= C.PICKUP_R then
      T.tick(nil, timer.getTime())   -- the tick confirms position and starts boarding
    end
  elseif e.id == world.event.S_EVENT_DEAD or e.id == world.event.S_EVENT_CRASH or e.id == world.event.S_EVENT_UNIT_LOST then
    if S.helo ~= "LOST" and S.helo ~= "ABOARD" then
      S.helo = "LOST"
      N.msg("MAGIC: Dodge is down! Dodge 1-1 is down!", 25)
      T.trySummary(false)
    end
  end
end)

function N.onTrap(pname, uname)
  local fuel = N.rec.lowFuel[pname] and string.format(" LOW FUEL at trap (%d%%).", math.floor(N.rec.lowFuel[pname] * 100 + 0.5)) or ""
  N.msg("DEBRIEF - " .. pname .. " recovered aboard." .. fuel .. " Survivor: " .. S.survivor .. ". Dodge: " .. S.helo .. ".", 30)
end

------------------------------------------------------------------ init
function T.init()
  N.quiet(C.JTAC_UNIT)
  N.quiet(C.SURVIVOR_GROUP)
  for _, g in ipairs(C.THREAT_GROUPS) do N.setAD(g, true) end
  local now = timer.getAbsTime()
  local function at(abs, fn) timer.scheduleFunction(function() fn() return nil end, nil, timer.getTime() + math.max(1, abs - now)) end
  at(C.SEARCH_TIME, T.startSearch)
  at(C.MIG_TIME, function()
    N.activate(C.MIG_GROUP)
    N.msg("MAGIC: Pop-up group, two " .. C.MIG_KIND .. " out of Gudauta, heading for the survivor's area.", 20)
    N.capThreat("Two " .. C.MIG_KIND .. " heading for the survivor's area")
  end)
  timer.scheduleFunction(T.tick, nil, timer.getTime() + 2)

  local root = missionCommands.addSubMenuForCoalition(N.BLUE, "Sandy Lift")
  missionCommands.addCommandForCoalition(N.BLUE, "Pontiac: LZ report", root, T.lzReport)
  missionCommands.addCommandForCoalition(N.BLUE, "Survivor: pop green smoke", root, T.smoke)
  missionCommands.addCommandForCoalition(N.BLUE, "CALL IN DODGE (rescue helo)", root, T.callDodge)
  missionCommands.addCommandForCoalition(N.BLUE, "Request CAP cover", root, N.requestCAP)
  missionCommands.addCommandForCoalition(N.BLUE, "Mission summary now", root, function() T.trySummary(true) end)
  local lm = missionCommands.addSubMenuForCoalition(N.BLUE, "Pontiac laser", root)
  missionCommands.addCommandForCoalition(N.BLUE, "Laser on nearest threat (1688)", lm, T.laserThreat)
  missionCommands.addCommandForCoalition(N.BLUE, "Terminate (laser off)", lm, function() N.laserStop(false) end)
  N.msg(C.TITLE .. ". A pilot is down " .. C.WHERE .. ". Clear the area, then F10 > Sandy Lift > CALL IN DODGE. " ..
        "The search party starts moving at " .. N.clock(C.SEARCH_TIME) .. ".", 25)
end

T.init()
