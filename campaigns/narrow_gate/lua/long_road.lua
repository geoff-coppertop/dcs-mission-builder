-- Operation Long Road (Narrow Gate campaign, success branch)
-- Interdiction of a stalled column. SEAD leads: a HARM hit on the SA-6 radar opens a 90 s
-- suppression window; destroying the radar (DEAD) closes the SA-6 for good. Requires common.lua.

LR = LR or {}
local T = LR
local N = NG

T.cfg = T.cfg or {
  START = 41400, RESTART = 43800,          -- column moves at this time (s since midnight, local)
  COLUMN_GROUP = "Column", COLUMN_AD = "Column AD", SAM_GROUP = "Brigade SA-6", SAM_RADAR = "SA-6 Straight Flush",
  MIG_GROUP = "Red CAP", MIG_TIME = 42600,
  CAP_GROUP = "Chevy", CAP_FLAG = "51",
  JTAC_UNIT = "Pontiac", LASER_CODE = 1688,
  ROUTE = { { x = 0, z = 0 }, { x = 0, z = 0 } },  -- column route after restart
  COVER = { x = 0, z = 0 }, COVER_R = 1500,
  SUPPRESS_S = 90, HARM_KILL_R = 150,
  JETS = { "Enfield 1-1", "Enfield 1-2" },
  COLT_PREFIX = "Colt", COLT_FLAG = "53",
  NEXT_RESCUE = "Operation_Sandy_Lift.miz",
}
local C = T.cfg
local CLEAR_VALID = 120

T.s = { sam = "LIVE", supUntil = 0, windows = 0, harms = 0, escaped = 0, moving = false, migs = false,
        jet = {}, noSeadHits = 0, total = 0, startPos = {}, coltAt = nil, coltHarms = 0 }
local S = T.s

local function jet(n)
  S.jet[n] = S.jet[n] or { cleared = nil, target = nil, released = 0, uncleared = 0, impacts = {}, bdaPending = false }
  return S.jet[n]
end

local function columnUnits() return N.liveUnits(C.COLUMN_GROUP) end
local function destroyed() return S.total - #columnUnits() - S.escaped end

------------------------------------------------------------------ SA-6 state
local function radar() return N.liveUnit(C.SAM_RADAR) end
local function samDown() return S.sam == "DEAD" or (S.sam == "SUPPRESSED" and timer.getAbsTime() < S.supUntil) end
local function samStatus()
  if S.sam == "DEAD" then return "SA-6 DEAD (radar destroyed)" end
  if S.sam == "SUPPRESSED" then
    local left = S.supUntil - timer.getAbsTime()
    if left > 0 then return string.format("SA-6 SUPPRESSED, %d s left", math.floor(left)) end
  end
  return "SA-6 LIVE"
end

function T.samDead()
  if S.sam == "DEAD" then return end
  S.sam = "DEAD"
  N.setAD(C.SAM_GROUP, false)
  N.msg("PONTIAC: Good effects! Straight Flush destroyed. SA-6 is DEAD, the column is open.", 20)
end

function T.suppress()
  if S.sam == "DEAD" then return end
  S.sam = "SUPPRESSED"
  S.windows = S.windows + 1
  S.supUntil = timer.getAbsTime() + C.SUPPRESS_S
  N.setAD(C.SAM_GROUP, false)
  N.msg(string.format("PONTIAC: Good HARM effects, Straight Flush is off the air. SA-6 SUPPRESSED until %sL.\n" ..
        "Strikers, you have %d seconds: call IN on the column.", N.hms(S.supUntil), C.SUPPRESS_S), 20)
  local mine = S.windows
  timer.scheduleFunction(function()
    if S.sam == "SUPPRESSED" and S.windows == mine then
      S.sam = "LIVE"
      N.setAD(C.SAM_GROUP, true)
      N.msg("PONTIAC: Straight Flush is back up. SA-6 LIVE. Another Magnum, or kill the radar.", 15)
    end
    return nil
  end, nil, timer.getTime() + C.SUPPRESS_S)
end

------------------------------------------------------------------ column
function T.restart()
  if S.moving or #columnUnits() == 0 then return end
  S.moving = true
  local function route(gname)
    local g = Group.getByName(gname)
    if not g or not g:isExist() then return end
    local pts = {}
    local u = g:getUnits()[1]
    if u then local p = u:getPoint(); pts[1] = { x = p.x, y = p.z, type = "Turning Point", action = "Off Road", speed = 8 } end
    for _, w in ipairs(C.ROUTE) do pts[#pts + 1] = { x = w.x, y = w.z, type = "Turning Point", action = "Off Road", speed = 8 } end
    pts[#pts + 1] = { x = C.COVER.x, y = C.COVER.z, type = "Turning Point", action = "Off Road", speed = 8 }
    g:getController():setTask({ id = "Mission", params = { route = { points = pts } } })
  end
  route(C.COLUMN_GROUP)
  route(C.COLUMN_AD)
  N.msg("PONTIAC: The column is MOVING, turning inland for the hills. Anything that reaches cover is gone.", 20)
end

function T.escapeTick(_, t)
  for _, u in ipairs(columnUnits()) do
    if N.dist(u:getPoint(), C.COVER) <= C.COVER_R then
      S.escaped = S.escaped + 1
      pcall(function() u:destroy() end)
      N.msg(string.format("PONTIAC: One vehicle into cover. %d escaped.", S.escaped), 8)
    end
  end
  if #columnUnits() == 0 then return nil end
  return t + 5
end

------------------------------------------------------------------ laser
local function leadVehicle()
  local list = columnUnits()
  if #list == 0 then return nil end
  if S.moving then   -- the vehicle nearest cover is the one to stop
    table.sort(list, function(a, b) return N.dist(a:getPoint(), C.COVER) < N.dist(b:getPoint(), C.COVER) end)
  end
  return list[1]
end

function T.laserColumn()
  if #columnUnits() == 0 then N.msg("PONTIAC: No column vehicles left.", 8) return end
  N.laserStart(C.JTAC_UNIT, function() local u = leadVehicle(); return u and u:getPoint() or nil end, C.LASER_CODE,
               "PONTIAC", function() N.msg("PONTIAC: No more column vehicles to lase.", 8) end)
  N.msg("PONTIAC: Laser on the column, code " .. C.LASER_CODE .. ". Spot shifts as vehicles die.", 12)
end

function T.laserRadar()
  if not radar() then N.msg("PONTIAC: Straight Flush is already dead.", 8) return end
  N.laserStart(C.JTAC_UNIT, function() local r = radar(); return r and r:getPoint() or nil end, C.LASER_CODE, "PONTIAC")
  N.msg("PONTIAC: Laser on the Straight Flush radar, code " .. C.LASER_CODE .. ".", 12)
end

------------------------------------------------------------------ COLT
function T.pushColt()
  if S.coltAt then N.msg("COLT: Already pushed.", 8) return end
  local alive = 0
  for _, n in ipairs({ C.COLT_PREFIX .. " 1-1", C.COLT_PREFIX .. " 1-2" }) do if N.liveUnit(n) then alive = alive + 1 end end
  if alive == 0 then N.msg("MAGIC: Negative, COLT is not available.", 10) return end
  S.coltAt = timer.getAbsTime()
  trigger.action.setUserFlag(C.COLT_FLAG, true)
  N.msg("COLT 1-1: Copy, pushing on the Straight Flush. Magnum in about 3 minutes. Strikers, be ready to follow us in.", 15)
end

------------------------------------------------------------------ calls
function T.callIn(name, target)
  local u = N.liveUnit(name)
  if not u then N.msg("PONTIAC: " .. name .. " not on station.", 8) return end
  local js = jet(name)
  N.msg(string.format("%s: IN on the %s, heading %03d.", name:upper(), target == "SAM" and "SA-6" or "column",
        math.floor(N.heading(u) + 0.5)), 8)
  if target == "COLUMN" then
    if #columnUnits() == 0 then N.msg("PONTIAC: " .. name .. ", ABORT. No column vehicles left.", 10) return end
    if not samDown() then
      N.msg("PONTIAC: " .. name .. ", ABORT ABORT ABORT. SA-6 is LIVE. SEAD first: Magnum on the Straight Flush, or kill it.", 15)
      return
    end
  else
    if S.sam == "DEAD" then N.msg("PONTIAC: " .. name .. ", ABORT. SA-6 is already dead.", 10) return end
  end
  js.cleared, js.target = timer.getAbsTime(), target
  js.impacts, js.bdaPending = {}, false
  N.msg("PONTIAC: " .. name .. ", CLEARED HOT on the " .. (target == "SAM" and "Straight Flush." or
        ("column. " .. samStatus() .. ".")), 12)
end

function T.update()
  local lv = leadVehicle()
  local lines = { "PONTIAC: Target update." }
  if lv then
    local ll, mgrs = N.coord(lv:getPoint())
    lines[#lines + 1] = string.format("Column: %d vehicles %s, %d destroyed, %d escaped.", #columnUnits(),
      S.moving and "MOVING inland" or "stationary on the coast road", destroyed(), S.escaped)
    lines[#lines + 1] = (S.moving and "Lead vehicle: " or "Column head: ") .. mgrs .. "  (" .. ll .. ")"
  else
    lines[#lines + 1] = string.format("Column: none left. %d destroyed, %d escaped.", destroyed(), S.escaped)
  end
  local r = radar()
  if r then
    local ll, mgrs = N.coord(r:getPoint())
    lines[#lines + 1] = samStatus() .. ". Straight Flush: " .. mgrs .. "  (" .. ll .. ")"
  else
    lines[#lines + 1] = "SA-6 DEAD."
  end
  if not S.moving then lines[#lines + 1] = "Column expected to move at " .. N.hms(C.RESTART) .. "L." end
  N.msg(table.concat(lines, "\n"), 30)
end

local function bda(name)
  local js = jet(name)
  js.bdaPending = false
  local best
  for _, i in ipairs(js.impacts) do if not best or i.miss < best.miss then best = i end end
  local first = (#js.impacts == 0) and "no impacts observed" or
    (#js.impacts .. " impact" .. (#js.impacts > 1 and "s" or "") ..
     (best.miss <= 15 and ", direct hit" or string.format(", closest %d m %s of a %s", math.floor(best.miss + 0.5),
       N.compass(best.dir), best.what)))
  N.msg(string.format("PONTIAC: %s, BDA: %s.\nColumn %d of %d destroyed, %d escaped. %s.", name, first,
        destroyed(), S.total, S.escaped, samStatus()), 20)
end

------------------------------------------------------------------ events
N.on(function(e)
  local okn, iname = false, nil
  if e.initiator then okn, iname = pcall(e.initiator.getName, e.initiator) end
  local isColt = okn and iname and string.find(iname, "^" .. C.COLT_PREFIX) ~= nil
  if e.id == world.event.S_EVENT_SHOT and e.weapon and e.initiator and (N.playerName(e.initiator) or isColt) then
    local kind = N.weaponKind(e.weapon)
    local name = iname
    if isColt and kind ~= "HARM" then return end
    if kind == "HARM" then
      S.harms = S.harms + 1
      if isColt then S.coltHarms = S.coltHarms + 1 end
      N.msg(name:upper() .. ": Magnum.", 6)
      N.track(e.weapon, function(p)
        -- compare with the radar's last known position: a HARM that kills it leaves no radar to measure from
        if S.radarPos and S.sam ~= "DEAD" and N.dist(p, S.radarPos) <= C.HARM_KILL_R then
          timer.scheduleFunction(function()
            if radar() then T.suppress() else T.samDead() end
            return nil
          end, nil, timer.getTime() + 2)
        end
      end)
    elseif kind == "GROUND" then
      local js = jet(name)
      js.released = js.released + 1
      if not js.cleared or timer.getAbsTime() - js.cleared > CLEAR_VALID then
        js.uncleared = js.uncleared + 1
        N.msg("PONTIAC: " .. name .. ", weapon release observed WITHOUT clearance.", 10)
      end
      N.track(e.weapon, function(p)
        local best, what, ref
        for _, u in ipairs(columnUnits()) do
          local d = N.dist(p, u:getPoint())
          if not best or d < best then best, what, ref = d, "column vehicle", u:getPoint() end
        end
        local r = radar()
        if r then
          local d = N.dist(p, r:getPoint())
          if not best or d < best then best, what, ref = d, "Straight Flush", r:getPoint() end
        end
        if best and best <= 600 then
          js.impacts[#js.impacts + 1] = { miss = best, what = what, dir = N.bearing(ref, p) }
          if what == "column vehicle" and not samDown() then
            S.noSeadHits = S.noSeadHits + 1
            N.msg("PONTIAC: " .. name .. ", that attack went in with the SA-6 LIVE.", 10)
          end
          if not js.bdaPending then
            js.bdaPending = true
            timer.scheduleFunction(function() bda(name) return nil end, nil, timer.getTime() + 20)
          end
        end
      end)
    end
  elseif (e.id == world.event.S_EVENT_DEAD or e.id == world.event.S_EVENT_UNIT_LOST) and e.initiator then
    local ok, nm = pcall(e.initiator.getName, e.initiator)
    if ok and nm == C.SAM_RADAR then T.samDead() end
  end
end)

function N.onTrap(pname, uname)
  local js = S.jet[uname]
  local proc = js and string.format("Releases %d%s.", js.released,
    js.uncleared > 0 and (", " .. js.uncleared .. " WITHOUT CLEARANCE") or ", all cleared hot") or "No releases."
  local fuel = N.rec.lowFuel[pname] and string.format(" LOW FUEL at trap (%d%%).", math.floor(N.rec.lowFuel[pname] * 100 + 0.5)) or ""
  N.msg("DEBRIEF - " .. pname .. " recovered aboard." .. fuel .. "\n" .. proc .. "\nColumn " .. destroyed() .. " of " ..
        S.total .. " destroyed, " .. S.escaped .. " escaped. " .. samStatus() .. ".", 45)
end

function N.onAllDown()
  local d = destroyed()
  local outcome, why
  if d >= math.ceil(0.7 * S.total) then
    outcome, why = "SUCCESS", "The brigade's main body is wrecked on the coast road. The advance on the Inguri is over."
  elseif d >= math.ceil(0.4 * S.total) then
    outcome, why = "PARTIAL", "The column is badly hurt but the survivors reach the hills. The advance is delayed, not stopped."
  else
    outcome, why = "FAILURE", "Most of the column reaches cover. The brigade will try again."
  end
  local clean, reasons = N.cleanRecovery()
  trigger.action.setUserFlag("90", outcome == "SUCCESS" and 1 or (outcome == "PARTIAL" and 2 or 3))
  N.msg("MISSION SUMMARY - OPERATION LONG ROAD\n" ..
    string.format("Primary: column %d of %d destroyed, %d escaped.\n", d, S.total, S.escaped) ..
    "SEAD/DEAD: " .. (S.sam == "DEAD" and "SA-6 DESTROYED (bonus)" or "SA-6 survived") ..
    (C.COLT and string.format(", %d HARMs (%d from COLT), %d suppression windows opened. COLT %s.\n", S.harms, S.coltHarms, S.windows,
      S.coltAt and ("pushed at " .. N.hm(S.coltAt) .. "L") or "never pushed")
      or string.format(", %d HARMs, %d suppression windows opened.\n", S.harms, S.windows)) ..
    (S.noSeadHits > 0 and string.format("%d column attacks went in with the SA-6 live.\n", S.noSeadHits) or "Every column attack went in behind SEAD.\n") ..
    "Secondary - Clean recovery: " .. (clean and "ACHIEVED." or ("FAILED (" .. table.concat(reasons, "; ") .. ").")) ..
    "\n" .. N.capSummary() ..
    "\n\nOUTCOME: " .. outcome .. ". " .. why .. "\nCAMPAIGN: this is the last mission on the success branch." ..
    (N.rescue(C.NEXT_RESCUE)), 90)
end

------------------------------------------------------------------ init
function T.init()
  S.total = #columnUnits()
  local r0 = radar()
  S.radarPos = r0 and r0:getPoint() or nil
  N.setAD(C.SAM_GROUP, true)
  N.setAD(C.COLUMN_AD, true)
  N.quiet(C.JTAC_UNIT)
  local now = timer.getAbsTime()
  local function at(abs, fn) timer.scheduleFunction(function() fn() return nil end, nil, timer.getTime() + math.max(1, abs - now)) end
  at(C.RESTART - 600, function() if not S.moving then N.msg("PONTIAC: Column crews are mounting up. Expect it to move in 10 minutes.", 15) end end)
  at(C.RESTART - 120, function() if not S.moving then N.msg("PONTIAC: Engines starting on the column. Two minutes.", 12) end end)
  at(C.RESTART, T.restart)
  at(C.MIG_TIME, function()
    S.migs = true
    N.activate(C.MIG_GROUP)
    N.msg("MAGIC: Pop-up group, two MiG-29s out of Gudauta, heading for the column.", 20)
    N.capThreat("Two MiG-29s out of Gudauta, heading for the column")
  end)
  timer.scheduleFunction(T.escapeTick, nil, timer.getTime() + 5)

  local root = missionCommands.addSubMenuForCoalition(N.BLUE, "Long Road")
  missionCommands.addCommandForCoalition(N.BLUE, "Pontiac: target update", root, T.update)
  if C.COLT then missionCommands.addCommandForCoalition(N.BLUE, "PUSH COLT (SEAD)", root, T.pushColt) end
  missionCommands.addCommandForCoalition(N.BLUE, "Request CAP cover", root, N.requestCAP)
  missionCommands.addCommandForCoalition(N.BLUE, "Mission summary now", root, function() N.rec.summaryDone = false; N.recCheck(true) end)
  local lm = missionCommands.addSubMenuForCoalition(N.BLUE, "Pontiac laser", root)
  missionCommands.addCommandForCoalition(N.BLUE, "Laser on Straight Flush (1688)", lm, T.laserRadar)
  missionCommands.addCommandForCoalition(N.BLUE, "Laser on column (1688)", lm, T.laserColumn)
  missionCommands.addCommandForCoalition(N.BLUE, "Terminate (laser off)", lm, function() N.laserStop(false) end)
  for _, name in ipairs(C.JETS) do
    local sm = missionCommands.addSubMenuForCoalition(N.BLUE, name, root)
    missionCommands.addCommandForCoalition(N.BLUE, "IN on SA-6 radar (DEAD)", sm, function() T.callIn(name, "SAM") end)
    missionCommands.addCommandForCoalition(N.BLUE, "IN on column", sm, function() T.callIn(name, "COLUMN") end)
    missionCommands.addCommandForCoalition(N.BLUE, "OFF (request BDA)", sm, function() bda(name) end)
  end
  N.msg("OPERATION LONG ROAD. The column moves at " .. N.clock(C.RESTART) .. ". SEAD leads: " ..
        (C.COLT and "push COLT from F10; " or "your own HARMs, no COLT today; ") .. "a HARM hit on " ..
        "the Straight Flush opens a " .. C.SUPPRESS_S .. " s window, killing it ends the SA-6. F10 > Long Road.", 25)
end

T.init()
