-- Operation Narrow Gate
-- FORD jamming window, Gudauta patrol, CAP relief, standard JTAC/CAS flow (Type 2), TOT grading, late scramble,
-- on-call CAP commit, recovery debrief. Pure DCS scripting engine (no MIST/MOOSE).

TOTS = TOTS or {}
local T = TOTS

-- __CONFIG__ (values are filled in by the mission builder)
T.cfg = T.cfg or {
  TOT          = 38100,        -- seconds since midnight, mission local time
  WINDOW       = 60,           -- +/- seconds of impact counted as ON TIME
  SUP_BEFORE   = 150,          -- planned: FORD's jamming reaches the SA-6 this many seconds before TOT
  SUP_AFTER    = 120,          -- and off this many seconds after
  ZULU_OFFSET  = 4 * 3600,     -- Caucasus local = Zulu + 4
  TARGET_GROUP = "Depot Targets",
  SAM_GROUP    = "Depot SAM",
  AAA_GROUP    = "Depot AAA",     -- ZSUs + SA-13: FORD jams the SA-6 radar only
  SCRAMBLE_GROUP = "Red Scramble",
  CAP_GROUP    = "Chevy",
  CAP_FLAG     = "51",
  JTAC_UNIT    = "Pontiac",
  CARRIER_UNIT = "CVN-74 Stennis",
  LASER_CODE   = 1688,
  TARGET_POINT = { x = 0, z = 0 },
  IMPACT_RADIUS = 2500,        -- metres from target centre that counts as "on target"
  TANKER_INFO  = "Arco, 251.0 AM, TACAN 60Y",
  IP_HDG = "054", IP_DIST = "11.3", EGRESS_HDG = "252", FAH = "030-080",
  FAH_MIN = 30, FAH_MAX = 80,
  FRIENDLIES = "Blue ground forces at the Inguri, 20 nm south-east",
  JETS = { "Enfield 1-1", "Enfield 1-2" },
  FORD_GROUP = "Ford", FORD_UNITS = { "Ford 1-1", "Ford 1-2" }, FORD_SPAWN = 0,
  JAM_R = 40000, SAM_POINT = { x = 0, z = 0 },   -- jamming is on while a FORD jet is within JAM_R of the SA-6
  PATROL_FLAG = "60", PATROL_TYPE_FLAG = "61", PATROL_PUSH_FLAG = "62",   -- Gudauta dawn patrol (random at start)
  PATROL_21 = "Red Patrol 21", PATROL_29 = "Red Patrol 29",
  CAP_SCREEN = { x = 0, z = 0 }, CAP_EGRESS = { x = 0, z = 0 },
  MIN_FUEL = 0.18,             -- fraction of internal fuel (~2,000 lb) for a "clean" recovery
  NEXT_SUCCESS = "Operation_Long_Road.miz",
  NEXT_SUCCESS_LATE = "Operation_Long_Road_Own_SEAD.miz",   -- depot destroyed, but outside the window
  NEXT_PARTIAL = "Operation_Stone_Ford.miz",
  NEXT_FAILURE = "Operation_Stone_Ford_Hard.miz",
  NEXT_RESCUE  = "Operation_Sandy_Lift.miz",
  OUTCOME_FLAG = "90",         -- 1 success, 2 partial, 3 failure, 4 success but late (for campaign wiring)
  RESCUE_FLAG  = "91",         -- true if any jet was lost
}

local C = T.cfg
local atan2 = math.atan2 or math.atan   -- Lua 5.1 (DCS) has atan2; newer Lua folds it into atan
local BLUE = coalition.side.BLUE
local CLEAR_VALID = 120        -- seconds a "cleared hot" stays valid
local IN_MAX_NM = 25           -- IN call must be within this range of the target
local SUP_ON  = C.TOT - C.SUP_BEFORE
local SUP_OFF = C.TOT + C.SUP_AFTER
local IN_EARLIEST = C.TOT - C.WINDOW - 50   -- an IN earlier than this would put bombs ahead of the window

T.state = {
  samActive   = true,
  windowOpen  = false,
  windowDone  = false,
  onTime      = false,
  scrambled   = false,
  capCalled   = false,
  targetDead  = false,
  grades      = {},   -- [playerName] = { delta=, impact=, verdict= }
  recovered   = {},   -- [playerName] = true
  -- CAS flow (flight level)
  checkedIn   = false,
  nineLine    = false,
  readback    = false,
  -- CAS flow (per jet, keyed by unit name)
  jet         = {},   -- [unitName] = { cleared=t, inAt=t, released=n, unclearedDrops=n, impacts={...}, passes=n }
  -- laser
  airborne    = {},   -- [playerName] = unitName (took off)
  lost        = {},   -- [playerName] = reason
  lowFuel     = {},   -- [playerName] = fuel fraction at landing
  summaryDone = false,
  laserOn     = false,
  laser       = nil,
  laserTarget = nil,
  losWarned   = false,
}
local S = T.state
local function cap() return CAPCTL end   -- controller-run CAP (cap.lua), loaded before this script

------------------------------------------------------------------ helpers

-- where a lost player's pilot is: "land" (ejected over land: needs a rescue), "water" (ejected over the sea:
-- picked up by a Navy helicopter, no rescue mission) or "killed" (no ejection)
local function lossKind(e)
  if e.id ~= world.event.S_EVENT_EJECTION then return "killed" end
  local ok, p = pcall(e.initiator.getPoint, e.initiator)
  if not ok or not p or not land.getSurfaceType or not land.SurfaceType then return "land" end
  local ok2, st = pcall(land.getSurfaceType, { x = p.x, y = p.z })
  if ok2 and (st == land.SurfaceType.WATER or st == land.SurfaceType.SHALLOW_WATER) then return "water" end
  return "land"
end

local function rescueLines(kinds, file)
  local n = { land = 0, water = 0, killed = 0 }
  for _, k in pairs(kinds) do n[k] = n[k] + 1 end
  local out = ""
  if n.land > 0 then out = out .. "\nAlso fly " .. file .. " to bring the downed pilot home." end
  if n.water > 0 then out = out .. "\nThe pilot who ejected over the water was picked up by a Navy helicopter. No rescue mission needed." end
  if n.killed > 0 then out = out .. "\nNo ejection was seen from the lost jet. There is no one to rescue." end
  return out, n.land > 0
end
local function msg(text, secs)
  trigger.action.outTextForCoalition(BLUE, text, secs or 15)
end

local function hms(abs)
  abs = math.floor(abs + 0.5) % 86400
  return string.format("%02d:%02d:%02d", math.floor(abs / 3600), math.floor(abs % 3600 / 60), abs % 60)
end

local function clock(abs)
  return hms(abs) .. "L / " .. hms(abs - C.ZULU_OFFSET) .. "Z"
end

local function signedMMSS(d)
  local sign = d < 0 and "-" or "+"
  d = math.abs(math.floor(d + 0.5))
  return string.format("%s%d:%02d", sign, math.floor(d / 60), d % 60)
end

local function dist2d(a, b)
  local dx, dz = a.x - b.x, a.z - b.z
  return math.sqrt(dx * dx + dz * dz)
end

-- bearing from a to b in degrees (map grid, x = north, z = east)
local function bearing(a, b)
  local deg = math.deg(atan2(b.z - a.z, b.x - a.x))
  return (deg + 360) % 360
end

local function compass(deg)
  local names = { "north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west" }
  return names[math.floor(((deg + 22.5) % 360) / 45) + 1]
end

local function playerName(unit)
  if not unit or not unit.getPlayerName then return nil end
  local ok, name = pcall(unit.getPlayerName, unit)
  if ok then return name end
  return nil
end

local function jetState(unitName)
  S.jet[unitName] = S.jet[unitName] or { cleared = nil, inAt = nil, released = 0, unclearedDrops = 0,
                                         impacts = {}, passes = 0, killsAtIn = 0, pending = 0 }
  return S.jet[unitName]
end

local function liveJet(unitName)
  local u = Unit.getByName(unitName)
  if u and u:isExist() then return u end
  return nil
end

------------------------------------------------------------------ SAM control
function T.setSAM(active)
  local g = Group.getByName(C.SAM_GROUP)
  S.samActive = active
  if not g or not g:isExist() then return end
  local ctl = g:getController()
  if active then
    ctl:setOption(AI.Option.Ground.id.ALARM_STATE, AI.Option.Ground.val.ALARM_STATE.RED)
    ctl:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.OPEN_FIRE)
  else
    ctl:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.WEAPON_HOLD)
    ctl:setOption(AI.Option.Ground.id.ALARM_STATE, AI.Option.Ground.val.ALARM_STATE.GREEN)
  end
end

function T.setAAA()
  local g = Group.getByName(C.AAA_GROUP)
  if not g or not g:isExist() then return end
  local ctl = g:getController()
  ctl:setOption(AI.Option.Ground.id.ALARM_STATE, AI.Option.Ground.val.ALARM_STATE.RED)
  ctl:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.OPEN_FIRE)
end

------------------------------------------------------------------ targets
local function targetUnits()
  local g = Group.getByName(C.TARGET_GROUP)
  local out = {}
  if not g or not g:isExist() then return out end
  for _, u in ipairs(g:getUnits() or {}) do
    if u and u:isExist() and u:getLife() > 1 then out[#out + 1] = u end
  end
  return out
end

T.totalTargets = nil
local function killed()
  return (T.totalTargets or 0) - #targetUnits()
end

local function pickTarget()
  local list = targetUnits()
  if #list == 0 then return nil end
  if S.laserTarget then
    for _, u in ipairs(list) do
      if u:getName() == S.laserTarget then return u end
    end
  end
  return list[1]
end

local function coordText(p)
  local lat, lon = coord.LOtoLL(p)
  local function ddm(v, pos, neg)
    local h = v >= 0 and pos or neg
    v = math.abs(v)
    local deg = math.floor(v)
    return string.format("%s %02d°%06.3f'", h, deg, (v - deg) * 60)
  end
  local m = coord.LLtoMGRS(lat, lon)
  local mgrs = string.format("%s %s %05d %05d", m.UTMZone, m.MGRSDigraph, math.floor(m.Easting), math.floor(m.Northing))
  local elev = land.getHeight({ x = p.x, y = p.z })
  return ddm(lat, "N", "S") .. "  " .. ddm(lon, "E", "W"), "MGRS " .. mgrs,
         string.format("%d ft MSL", math.floor(elev * 3.28084 + 0.5))
end

------------------------------------------------------------------ timeline
local function activateGroup(name)
  local g = name and Group.getByName(name)
  if not g then return false end
  local ok = pcall(function() g:activate() end)
  if not ok then trigger.action.activateGroup(g) end
  return true
end

local function liveIn(names)
  local out = {}
  for _, n in ipairs(names) do
    local u = Unit.getByName(n)
    if u and u:isExist() and u:getLife() > 1 then out[#out + 1] = u end
  end
  return out
end

local function liveOfGroup(gname)
  local g = gname and Group.getByName(gname)
  local out = {}
  if not g or not g:isExist() then return out end
  for _, u in ipairs(g:getUnits()) do
    if u and u:isExist() and u:getLife() > 1 then out[#out + 1] = u end
  end
  return out
end

local function fordJets() return liveIn(C.FORD_UNITS) end

-- first jammers-on gets the full brief; later ones are resumes after a gap
function T.windowOpens()
  S.windowOpen = true
  T.setSAM(false)
  if S.jamStarted then
    msg("FORD: Back on track, jammers on. SA-6 SUPPRESSED again. Guns and SA-13 still up.", 12)
    return
  end
  S.jamStarted = true
  local extra
  if S.readback then
    extra = "PONTIAC: Enfield, FORD has the SA-6 jammed. Call IN from the IP."
  else
    extra = "PONTIAC: Enfield, FORD has the SA-6 jammed. Readback not received: no clearance until you read back lines 4, 6 and restrictions."
  end
  msg("FORD: Jammers on, SA-6 SUPPRESSED. Guns and SA-13 are still up, stay above 17,000.\nJamming until FORD is out of range, planned " ..
      clock(SUP_OFF) .. ". Impact window " .. hms(C.TOT - C.WINDOW) .. "-" ..
      hms(C.TOT + C.WINDOW) .. "L.\n" .. extra, 20)
  T.patrolPush()
end

-- a temporary break: FORD is alive but defending and out of range
function T.jamGap()
  S.windowOpen = false
  S.gaps = (S.gaps or 0) + 1
  T.setSAM(true)
  msg("FORD: Defending! Jammers off you. SA-6 is UP until we're back on track.", 12)
end

-- the end of FORD's jamming for this mission
function T.windowCloses(why)
  if S.windowDone then return end
  S.windowOpen = false
  S.windowDone = true
  T.setSAM(true)
  msg((why or "FORD: Jammers off, continuing north.") ..
      (S.onTime and " Defenses coming back up. Good timing, Enfield." or " Defenses coming back up."), 20)
end

-- Jamming follows FORD's real position. A FORD jet that is alive but out of range before the planned end
-- (it is defending) leaves a gap that ends when it is back; past the planned end, out of range means done.
function T.fordTick(_, t)
  if S.windowDone then return nil end
  local now = timer.getAbsTime()
  local jets = fordJets()
  local inRange = false
  for _, u in ipairs(jets) do
    if dist2d(u:getPoint(), C.SAM_POINT) <= C.JAM_R then inRange = true end
  end
  if inRange then S.outFor = 0 else S.outFor = (S.outFor or 0) + 1 end

  if #jets == 0 and S.fordUp then
    if S.jamStarted then
      T.windowCloses("MAGIC: FORD is down! Jamming lost.")
    elseif not S.fordLost then
      S.fordLost = true
      msg("MAGIC: FORD is down before it reached you. There will be no jamming. Your call, Enfield.", 20)
    end
    return nil
  end
  if inRange and not S.windowOpen then
    T.windowOpens()
  elseif S.windowOpen and S.outFor >= 3 then
    if now >= SUP_OFF - 15 then T.windowCloses() else T.jamGap() end
  elseif not S.windowOpen and S.jamStarted and now >= SUP_OFF then
    T.windowCloses("FORD: Past the SA-6, jammers off, continuing north.")
  end
  if S.windowDone then return nil end
  return t + 1
end

-- LATE is judged at the planned end of the jamming, whatever happened to FORD
function T.lateCheck()
  if S.onTime then return end
  T.scramble()
end

function T.scramble(why)
  if S.scrambled then return end
  S.scrambled = true
  activateGroup(C.SCRAMBLE_GROUP)
  msg((why or "MAGIC: No bombs landed in the impact window.") .. (S.samActive and " SA-6 is UP." or "") .. "\n" ..
      "MAGIC: Pop-up group, two MiG-21s off the Gudauta alert, hot toward the target area.", 25)
  if cap() then
    cap().commit("threat", C.CAP_EGRESS, "your egress", "Two MiG-21s off the Gudauta alert, hot toward the target area",
      { radius = 70000 })
  end
end

------------------------------------------------------------------ Gudauta patrol
-- Up on some mornings only: two mission-start RANDOM triggers set PATROL_FLAG (is it up) and
-- PATROL_TYPE_FLAG (MiG-29s rather than MiG-21s). Red's controllers send it at FORD when the jammers come on.
local function flagOn(f)
  local ok, v = pcall(trigger.misc.getUserFlag, f)
  return ok and v and v ~= 0 and v ~= false
end

function T.patrolInit()
  if not flagOn(C.PATROL_FLAG) then
    S.patrol = nil
    timer.scheduleFunction(function()
      msg("MAGIC: Picture north is clean. No Gudauta patrol this morning.", 12)
      return nil
    end, nil, timer.getTime() + 120)
    return
  end
  local is29 = flagOn(C.PATROL_TYPE_FLAG)
  S.patrol = { group = is29 and C.PATROL_29 or C.PATROL_21, kind = is29 and "MiG-29s" or "MiG-21s", hot = nil, done = false }
  activateGroup(S.patrol.group)
  timer.scheduleFunction(function()
    msg("MAGIC: Enfield, picture: single group, two " .. S.patrol.kind .. ", orbiting off Gudauta, angels 20. " ..
        "That's the dawn patrol, and it's up this morning.\nExpect Red to send it at FORD when the jammers come on. " ..
        "If they push, I'll commit Chevy to screen FORD.", 20)
    return nil
  end, nil, timer.getTime() + 120)
end

function T.patrolAlive()
  if not S.patrol then return 0 end
  return #liveOfGroup(S.patrol.group)
end

function T.patrolPush()
  local p = S.patrol
  if not p or p.hot or T.patrolAlive() == 0 then return end
  p.hot = timer.getAbsTime()
  trigger.action.setUserFlag(C.PATROL_PUSH_FLAG, true)
  msg("MAGIC: Gudauta group, two " .. p.kind .. ", committing south, hot on FORD.", 15)
  if cap() then
    cap().commit("threat", C.CAP_SCREEN, "FORD", "Gudauta group, two " .. p.kind .. ", hot on FORD",
      { radius = 60000, clear = function() return not T.patrolThreat() or (S.fordUp and #fordJets() == 0) end })
  end
end

-- the patrol stops being a threat when it is dead, or after it has had its run at FORD and gone home
function T.patrolThreat()
  local p = S.patrol
  if not p or p.done then return false end
  local alive = liveOfGroup(p.group)
  if #alive == 0 then
    p.done = "destroyed"
    return false
  end
  if p.hot and timer.getAbsTime() - p.hot > 120 then
    local far = true
    for _, u in ipairs(alive) do
      if dist2d(u:getPoint(), C.CAP_SCREEN) < 70000 then far = false end
    end
    if far then
      p.done = "returned to base"
      return false
    end
  end
  return true
end

------------------------------------------------------------------ CAP (CAPCTL, cap.lua)
-- MAGIC commits the CAP on the briefed criteria; Enfield can only request cover.

function T.capAdvice() return cap() and cap().advice() or "" end

function T.requestCAP()
  if not cap() then msg("MAGIC: Negative, no CAP available.", 10) return end
  S.capRequested = true
  cap().request(C.CAP_EGRESS, "your egress")
end

------------------------------------------------------------------ laser
function T.laserOff(silent)
  if S.laser then pcall(function() S.laser:destroy() end) end
  S.laser = nil
  S.laserOn = false
  if not silent then msg("PONTIAC: Terminate, laser off.", 10) end
end

local function jtacUnit()
  local u = Unit.getByName(C.JTAC_UNIT)
  if u and u:isExist() then return u end
  return nil
end

-- Runs every second while the laser is on: keeps the spot on a live target,
-- shifts to the next vehicle when one dies, checks line of sight.
function T.laserTick(_, t)
  if not S.laserOn then return nil end
  local j = jtacUnit()
  local tgt = pickTarget()
  if not j or not tgt then
    T.laserOff(true)
    if not tgt then msg("PONTIAC: No more targets to lase. Laser off.", 10) end
    return nil
  end
  local tp = tgt:getPoint()
  local aim = { x = tp.x, y = tp.y + 2, z = tp.z }
  local jp = j:getPoint()
  if not land.isVisible(jp, aim) then
    if not S.losWarned then
      S.losWarned = true
      msg("PONTIAC: Momentary loss of line of sight, stand by.", 8)
    end
    return t + 1
  end
  S.losWarned = false
  if S.laserTarget ~= tgt:getName() then
    if S.laserTarget then
      msg("PONTIAC: Shift. Spot moving to the next vehicle, code " .. C.LASER_CODE .. ".", 12)
    end
    S.laserTarget = tgt:getName()
  end
  if S.laser then
    S.laser:setPoint(aim)
  else
    S.laser = Spot.createLaser(j, { x = 0, y = -2, z = 0 }, aim, C.LASER_CODE)
  end
  return t + 1
end

local function startLaser()
  if S.laserOn then return true end
  if not jtacUnit() or #targetUnits() == 0 then return false end
  S.laserOn = true
  timer.scheduleFunction(T.laserTick, nil, timer.getTime() + 0.5)
  return true
end

------------------------------------------------------------------ CAS flow (flight level)
function T.checkIn()
  local lead
  for _, n in ipairs(C.JETS) do lead = lead or liveJet(n) end
  local pos = "position unknown"
  if lead then
    local p = lead:getPoint()
    local brg = bearing(C.TARGET_POINT, p)
    pos = string.format("%d nm %s of the target, angels %d", math.floor(dist2d(p, C.TARGET_POINT) / 1852 + 0.5),
                        compass(brg), math.floor(p.y * 3.28084 / 1000 + 0.5))
  end
  local n = 0
  for _, name in ipairs(C.JETS) do if liveJet(name) then n = n + 1 end end
  if n == 0 then n = 1 end
  S.checkedIn = true
  msg(string.format("ENFIELD: Pontiac, Enfield 1-1, checking in. %d F/A-18C, %s.\n" ..
      "Each jet 4 GBU-12, 3 AIM-120C, 2 AIM-9X, LITENING, laser %d. Playtime 30 minutes. Abort code: plain language.",
      n, pos, C.LASER_CODE), 20)
  local tgtCount = #targetUnits()
  timer.scheduleFunction(function()
    msg("PONTIAC: Enfield, Pontiac. Situation: Red mechanised battalion halted at a depot NE of Ochamchire, " ..
        tgtCount .. " vehicles in the open.\nThreats: SA-6 1 km north of the target, jammed by FORD " ..
        hms(SUP_ON) .. "-" .. hms(SUP_OFF) .. "L only (planned). NOT jammed: two ZSU-23-4 north and south of the depot, SA-13 on the east side: " ..
        "stay above 17,000 ft. MiG-21 alert pair at Gudauta.\n" ..
        "Friendlies: " .. C.FRIENDLIES .. ".\n" ..
        "GAME PLAN: Type 2 control, bomb on target. GBU-12, one per pass, Pontiac lasing code " .. C.LASER_CODE ..
        ". Lead impacts at TOT, wingman 30 seconds after.\nAdvise ready to copy 9-line.", 30)
    return nil
  end, nil, timer.getTime() + 3)
end

function T.nineLine()
  if not S.checkedIn then
    msg("PONTIAC: Enfield, check in first.", 8)
    return
  end
  local tgt = pickTarget()
  if not tgt then msg("PONTIAC: No targets remaining. Cleared to RTB.", 12) return end
  S.nineLine = true
  local ll, mgrs, elev = coordText(tgt:getPoint())
  msg("PONTIAC: 9-line follows.\n" ..
      "1. IP: \"IP\" (waypoint 3)\n" ..
      "2. " .. C.IP_HDG .. " true, offset left\n" ..
      "3. " .. C.IP_DIST .. " nm\n" ..
      "4. " .. elev .. "\n" ..
      "5. " .. #targetUnits() .. " vehicles, T-72s and trucks, in the open\n" ..
      "6. " .. mgrs .. "  (" .. ll .. ")\n" ..
      "7. Laser, Pontiac, code " .. C.LASER_CODE .. "\n" ..
      "8. Nearest friendlies " .. C.FRIENDLIES .. "\n" ..
      "9. Egress left, west to EGRESS (waypoint 5), " .. C.EGRESS_HDG .. " true\n" ..
      "Remarks: final attack heading " .. C.FAH .. ". TOT " .. clock(C.TOT) .. ". Window " ..
      hms(C.TOT - C.WINDOW) .. "-" .. hms(C.TOT + C.WINDOW) .. "L. Jamming " .. hms(SUP_ON) .. "-" .. hms(SUP_OFF) ..
      "L. 2x ZSU-23-4 and SA-13 not jammed, stay above 17,000 ft.\n" ..
      "Laser-target line roughly south-west to north-east from Pontiac's orbit.\n" ..
      "Read back lines 4, 6 and restrictions.", 60)
  S.nine = { elev = elev, mgrs = mgrs }
end

function T.readBack()
  if not S.nineLine then
    msg("PONTIAC: Enfield, no 9-line passed yet. Ready to copy 9-line first.", 8)
    return
  end
  S.readback = true
  msg("ENFIELD: " .. S.nine.elev .. ", " .. S.nine.mgrs .. ", final attack heading " .. C.FAH ..
      ", TOT " .. hms(C.TOT) .. "L.", 12)
  timer.scheduleFunction(function()
    msg("PONTIAC: Readback correct. Call IN with heading." ..
        (S.windowOpen and "" or (" Jamming expected from " .. clock(SUP_ON) .. ".")), 15)
    return nil
  end, nil, timer.getTime() + 2)
end

function T.smoke()
  local tgt = pickTarget()
  if not tgt then msg("PONTIAC: No targets remaining.", 8) return end
  local p = tgt:getPoint()
  trigger.action.smoke({ x = p.x + 30, y = p.y, z = p.z }, trigger.smokeColor.Red)
  msg("PONTIAC: Mark is red smoke, target 30 metres south of the smoke.", 10)
end

------------------------------------------------------------------ CAS flow (per jet)
local function abort(name, reason)
  msg("PONTIAC: " .. name .. ", ABORT ABORT ABORT. " .. reason, 15)
end

function T.callIn(name)
  local u = liveJet(name)
  if not u then msg("PONTIAC: " .. name .. " not on station.", 8) return end
  local js = jetState(name)
  local p = u:getPoint()
  local pos = u:getPosition()
  local hdg = (math.deg(atan2(pos.x.z, pos.x.x)) + 360) % 360
  local rng = dist2d(p, C.TARGET_POINT) / 1852
  local now = timer.getAbsTime()
  msg(string.format("%s: IN, heading %03d.", name:upper(), math.floor(hdg + 0.5)), 8)

  if not S.readback then
    abort(name, "No readback. Read back lines 4, 6 and restrictions.")
    return
  end
  if rng > IN_MAX_NM then
    abort(name, string.format("You are %d nm out. Call IN from the IP.", math.floor(rng + 0.5)))
    return
  end
  if hdg < C.FAH_MIN or hdg > C.FAH_MAX then
    abort(name, string.format("Heading %03d is outside final attack heading %s.", math.floor(hdg + 0.5), C.FAH))
    return
  end
  if now < IN_EARLIEST then
    abort(name, "Too early, your bombs would land ahead of the window. Earliest IN " .. hms(IN_EARLIEST) .. "L." ..
          ((not S.windowOpen and not S.windowDone) and " FORD's jammers are not on yet, the SA-6 is live." or ""))
    return
  end
  if #targetUnits() == 0 then
    abort(name, "No targets remaining.")
    return
  end
  js.cleared = now
  js.inAt = now
  js.passes = js.passes + 1
  js.impacts = {}
  js.bdaDone = false
  local warn = ""
  if not S.windowOpen then warn = " Be advised, SA-6 is UP." end
  if not S.laserOn then warn = warn .. " Call ten seconds for laser." end
  msg("PONTIAC: " .. name .. ", CLEARED HOT." .. warn, 12)
end

function T.tenSeconds(name)
  msg(name:upper() .. ": Ten seconds.", 6)
  if startLaser() then
    timer.scheduleFunction(function()
      msg("PONTIAC: Laser on, code " .. C.LASER_CODE .. ".", 10)
      return nil
    end, nil, timer.getTime() + 1)
  else
    msg("PONTIAC: Unable laser.", 8)
  end
end

function T.spot(name)
  msg(name:upper() .. ": Spot.", 6)
  if S.laserOn then
    msg("PONTIAC: Copy spot.", 6)
  else
    msg("PONTIAC: Negative, laser is off. Call ten seconds.", 8)
  end
end

function T.terminate(name)
  msg(name:upper() .. ": Terminate.", 6)
  T.laserOff(false)
end

local function bda(name)
  local js = jetState(name)
  local remaining = #targetUnits()
  local lines = {}
  if #js.impacts == 0 then
    lines[#lines + 1] = "no impacts observed"
  else
    local best = nil
    for _, imp in ipairs(js.impacts) do
      if not best or imp.miss < best.miss then best = imp end
    end
    lines[#lines + 1] = #js.impacts .. " impact" .. (#js.impacts > 1 and "s" or "")
    if best.miss <= 15 then
      lines[#lines + 1] = "direct hit"
    else
      lines[#lines + 1] = string.format("closest %d m %s of the target", math.floor(best.miss + 0.5), compass(best.dir))
    end
  end
  lines[#lines + 1] = "target status " .. killed() .. " of " .. (T.totalTargets or 0) .. " destroyed"
  local tail
  if remaining == 0 then
    tail = "All targets destroyed. Mission success, cleared to egress."
  elseif S.windowDone then
    tail = remaining .. " remaining. Window is closed; re-attack at your own risk, SA-6 is up."
  else
    tail = remaining .. " remaining. Re-attack approved, call IN."
  end
  msg("PONTIAC: " .. name .. ", BDA: " .. table.concat(lines, ", ") .. ".\n" .. tail, 20)
end

function T.off(name)
  local js = jetState(name)
  msg(name:upper() .. ": OFF, egressing " .. C.EGRESS_HDG .. ".", 8)
  js.cleared = nil
  js.bdaDone = true
  local waited = 0
  -- wait for this jet's weapons still in the air, then give BDA
  timer.scheduleFunction(function(_, t)
    waited = waited + 2
    if (js.pending or 0) > 0 and waited < 60 then return t + 2 end
    timer.scheduleFunction(function() bda(name) return nil end, nil, timer.getTime() + 3)
    return nil
  end, nil, timer.getTime() + 2)
  if (js.pending or 0) > 0 then
    msg("PONTIAC: " .. name .. ", copy OFF. Stand by for BDA, weapons still in the air.", 8)
  end
end

------------------------------------------------------------------ grading
function T.grade(name, impactAbs)
  if S.grades[name] then return end
  local d = impactAbs - C.TOT
  local verdict
  if d < -C.WINDOW then
    verdict = "EARLY"
    S.earlyLive = impactAbs < SUP_ON
  elseif d > C.WINDOW then
    verdict = "LATE"
  else
    verdict = "ON TIME"
    S.onTime = true
  end
  S.grades[name] = { delta = d, impact = impactAbs, verdict = verdict }

  local extra = ""
  if verdict == "EARLY" then
    extra = S.earlyLive and "\nFORD's jammers were not on yet. You bombed into a live SA-6."
            or "\nAhead of the impact window: the package TOT was missed."
  elseif verdict == "LATE" and S.scrambled then
    extra = "\nThe window had already closed. Fighters are airborne."
  end
  msg(string.format("TOT %s: %s impact %s (%s vs TOT %s)%s",
      verdict, name, clock(impactAbs), signedMMSS(d), hms(C.TOT) .. "L", extra), 20)
end

local function isGroundWeapon(weapon)
  local ok, desc = pcall(weapon.getDesc, weapon)
  if not ok or not desc then return false end
  local cat = desc.category
  if cat == Weapon.Category.BOMB or cat == Weapon.Category.ROCKET then return true end
  if cat == Weapon.Category.MISSILE then
    local mc = desc.missileCategory
    return mc == Weapon.MissileCategory.OTHER or mc == Weapon.MissileCategory.ANTI_SHIP
        or mc == Weapon.MissileCategory.CRUISE
  end
  return false
end

-- positions cached at mission start, so a hit on a vehicle that has just died still measures correctly
T.targetPos = {}
local function nearestTarget(p)
  local best, bestD = nil, nil
  for _, tp in ipairs(T.targetPos) do
    local d = dist2d(p, tp)
    if not bestD or d < bestD then best, bestD = tp, d end
  end
  return best, bestD
end

function T.trackWeapon(weapon, pname, uname)
  local last = nil
  local function step(_, t)
    local ok, alive = pcall(weapon.isExist, weapon)
    if ok and alive then
      local okp, p = pcall(weapon.getPoint, weapon)
      if okp and p then last = p end
      return t + 0.1
    end
    if uname then
      local jsp = jetState(uname)
      jsp.pending = math.max(0, (jsp.pending or 0) - 1)
    end
    if last and dist2d(last, C.TARGET_POINT) <= C.IMPACT_RADIUS then
      T.grade(pname, timer.getAbsTime())
      if uname then
        local js = jetState(uname)
        local tp, miss = nearestTarget(last)
        local dir = 0
        if tp then dir = bearing(tp, last) end
        js.impacts[#js.impacts + 1] = { miss = miss or dist2d(last, C.TARGET_POINT), dir = dir }
        -- automatic BDA if the jet never calls OFF
        if not js.autoBda then
          js.autoBda = true
          timer.scheduleFunction(function()
            js.autoBda = false
            if not js.bdaDone then bda(uname) end
            return nil
          end, nil, timer.getTime() + 25)
        end
      end
    end
    return nil
  end
  timer.scheduleFunction(step, nil, timer.getTime() + 0.1)
end

------------------------------------------------------------------ time check
function T.timeCheck()
  local now = timer.getAbsTime()
  local d = C.TOT - now
  local status
  if S.windowOpen then status = "Jammers ON (FORD in range), planned off " .. hms(SUP_OFF) .. "L"
  elseif S.windowDone then status = "Jammers OFF, SA-6 up"
  elseif S.jamStarted then status = "FORD defending: jamming interrupted, SA-6 UP"
  elseif S.fordLost then status = "FORD is down: NO jamming"
  else status = "Jammers expected in " .. signedMMSS(SUP_ON - now):sub(2) .. " (" .. hms(SUP_ON) .. "L, when FORD is in range)" end
  status = status .. ". Impact window " .. hms(C.TOT - C.WINDOW) .. "-" .. hms(C.TOT + C.WINDOW) .. "L"
  local flow = "Check-in " .. (S.checkedIn and "done" or "pending") .. ", 9-line " ..
               (S.nineLine and "copied" or "pending") .. ", readback " .. (S.readback and "correct" or "pending")
  msg(string.format("Time %s\nTOT  %s (%s)\n%s\n%s", clock(now), clock(C.TOT),
      d >= 0 and ("in " .. signedMMSS(d):sub(2)) or (signedMMSS(-d):sub(2) .. " ago"), status, flow), 12)
end

------------------------------------------------------------------ clean recovery
local function playerNames(set)
  local out = {}
  for k in pairs(set) do out[#out + 1] = k end
  return out
end

function T.summary(force)
  if S.summaryDone then return end
  local launched = playerNames(S.airborne)
  if #launched == 0 then return end
  for _, n in ipairs(launched) do
    if not S.recovered[n] and not S.lost[n] and not force then return end
  end
  S.summaryDone = true
  local clean, why = true, {}
  for _, n in ipairs(launched) do
    if S.lost[n] then clean = false; why[#why + 1] = n .. " " .. S.lost[n] end
    if S.lowFuel[n] then clean = false; why[#why + 1] = string.format("%s landed with %d%% fuel", n, math.floor(S.lowFuel[n] * 100 + 0.5)) end
  end
  local total = T.totalTargets or 0
  local killedN = total - #targetUnits()
  local prim = killedN .. " of " .. total .. " vehicles destroyed"
  -- campaign outcome: Success >= 80% and window met; Success (late) >= 80% outside the window;
  -- Partial >= 40%; Failure below 40%
  local outcome, nextFile, why2
  if total > 0 and killedN >= math.ceil(0.8 * total) and S.onTime then
    outcome, nextFile = "SUCCESS", C.NEXT_SUCCESS
    why2 = "The lead battalion is stopped. The brigade's main body is backing up on the coast road.\n" ..
           "CAG: \"Good work. The follow-up is yours to plan and lead, and COLT is yours with it.\""
  elseif total > 0 and killedN >= math.ceil(0.8 * total) then
    outcome, nextFile = "SUCCESS, LATE", C.NEXT_SUCCESS_LATE
    why2 = "The depot is gone and the lead battalion is stopped, but your section bombed outside the window.\n" ..
           "CAG: \"The depot's gone and I'll give you that. But you were late, inside a live SA-6 with MiGs up. " ..
           "COLT goes to a package that hits its TOT. The follow-up is still yours: do your own SEAD.\""
  elseif total > 0 and killedN >= math.ceil(0.4 * total) then
    outcome, nextFile = "PARTIAL", C.NEXT_PARTIAL
    why2 = "The lead battalion moves on at reduced strength toward the Inguri.\n" ..
           "CAG: \"Not what you promised. Same assets. The Army needs you at the Inguri.\""
  else
    outcome, nextFile = "FAILURE", C.NEXT_FAILURE
    why2 = "The lead battalion moves on to the Inguri at full strength.\n" ..
           "CAG: \"Your plan didn't stop them, and I can't spare more. CHEVY stays with the boat.\""
  end
  local rescueText, lostAny = rescueLines(S.lossKind or {}, C.NEXT_RESCUE)
  trigger.action.setUserFlag(C.OUTCOME_FLAG, ({ ["SUCCESS"] = 1, ["PARTIAL"] = 2, ["FAILURE"] = 3, ["SUCCESS, LATE"] = 4 })[outcome])
  trigger.action.setUserFlag(C.RESCUE_FLAG, lostAny)
  msg("MISSION SUMMARY - OPERATION NARROW GATE\n" ..
      "Primary: depot, " .. prim .. ". TOT window " .. (S.onTime and "met." or "missed.") .. "\n" ..
      "Secondary - Clean recovery: " .. (clean and "ACHIEVED, all jets aboard with fuel." or ("FAILED (" .. table.concat(why, "; ") .. ")."))
      .. (S.scrambled and "\nMiGs scrambled." or "") .. ((cap() and #cap().history > 0) and " CAP committed." or "") ..
      "\n" .. T.supportLine() ..
      "\n\nOUTCOME: " .. outcome .. ". " .. why2 ..
      "\nNEXT MISSION: " .. nextFile ..
      rescueText, 90)
end

function T.supportLine()
  local f = #fordJets()
  local fl
  if not S.fordUp then fl = "FORD: not yet airborne."
  elseif f == 2 then fl = "FORD: both jets continued north."
  else fl = "FORD: lost " .. (2 - f) .. " of 2 over the water, SAR responding." end
  if (S.gaps or 0) > 0 then fl = fl .. " Jamming interrupted " .. S.gaps .. "x while FORD defended." end
  local pl
  if not S.patrol then pl = "Gudauta patrol: not up."
  else
    local n = T.patrolAlive()
    pl = "Gudauta patrol: two " .. S.patrol.kind .. ", " .. (2 - n) .. " shot down" ..
         (S.patrol.done and (", " .. S.patrol.done) or "") .. "."
  end
  local cl = cap() and cap().summaryLine() or "CAP: none."
  return fl .. "\n" .. pl .. "\n" .. cl
end

------------------------------------------------------------------ debrief
function T.debrief(pname, uname)
  local g = S.grades[pname]
  local line
  if g then
    line = string.format("%s: %s (%s)", pname, g.verdict, signedMMSS(g.delta))
  else
    line = pname .. ": no weapons on target"
  end
  local js = uname and S.jet[uname] or nil
  local proc = "Procedure: check-in " .. (S.checkedIn and "yes" or "NO") .. ", readback " ..
               (S.readback and "yes" or "NO")
  if js then
    proc = proc .. ", passes " .. js.passes .. ", releases " .. js.released ..
           (js.unclearedDrops > 0 and (", " .. js.unclearedDrops .. " WITHOUT CLEARANCE") or ", all cleared hot")
  end
  local fuelLine = ""
  if S.lowFuel[pname] then fuelLine = string.format(" LOW FUEL at trap (%d%%).", math.floor(S.lowFuel[pname] * 100 + 0.5)) end
  msg("DEBRIEF - " .. line .. ", recovered aboard." .. fuelLine .. "\n" .. proc .. "\nTargets remaining: " .. #targetUnits() ..
      "\nJamming window " .. (S.onTime and "used" or "missed") ..
      (S.scrambled and ", MiGs scrambled" or "") .. ((cap() and #cap().history > 0) and ", CAP committed." or "."), 45)
end

------------------------------------------------------------------ events
T.handler = {}
function T.handler:onEvent(e)
  if not e then return end
  if e.id == world.event.S_EVENT_SHOT and e.weapon and e.initiator then
    local pname = playerName(e.initiator)
    if pname and isGroundWeapon(e.weapon) then
      local uname = e.initiator.getName and e.initiator:getName() or nil
      if uname then
        local js = jetState(uname)
        js.released = js.released + 1
        js.pending = (js.pending or 0) + 1
        local now = timer.getAbsTime()
        if not js.cleared or now - js.cleared > CLEAR_VALID then
          js.unclearedDrops = js.unclearedDrops + 1
          msg("PONTIAC: " .. uname .. ", weapon release observed WITHOUT clearance.", 10)
        end
      end
      T.trackWeapon(e.weapon, pname, uname)
    end

  elseif (e.id == world.event.S_EVENT_DEAD or e.id == world.event.S_EVENT_UNIT_LOST) and e.initiator then
    if not S.targetDead then
      timer.scheduleFunction(function()
        if not S.targetDead and #targetUnits() == 0 then
          S.targetDead = true
          T.laserOff(true)
          msg("PONTIAC: Good effects, all vehicles destroyed. Cleared off.\nTanker " ..
              C.TANKER_INFO .. " on the egress track. Mother is CVN-74, TACAN 74X, ICLS 11.", 30)
        end
        return nil
      end, nil, timer.getTime() + 1)
    end

  elseif e.id == world.event.S_EVENT_TAKEOFF and e.initiator then
    local pname = playerName(e.initiator)
    if pname then S.airborne[pname] = e.initiator:getName() end

  elseif (e.id == world.event.S_EVENT_CRASH or e.id == world.event.S_EVENT_EJECTION or
          e.id == world.event.S_EVENT_PILOT_DEAD) and e.initiator then
    local pname = playerName(e.initiator)
    if pname and not S.lost[pname] and not S.recovered[pname] then
      S.lost[pname] = (e.id == world.event.S_EVENT_EJECTION) and "ejected" or "lost"
      S.lossKind = S.lossKind or {}
      S.lossKind[pname] = lossKind(e)
      S.airborne[pname] = S.airborne[pname] or "?"
      msg("MAGIC: " .. pname .. " is down. Clean recovery is no longer possible.", 15)
      T.summary(false)
    end

  elseif e.id == world.event.S_EVENT_LAND and e.initiator then
    local pname = playerName(e.initiator)
    local place = e.place
    if pname and place and place.getName and place:getName() == C.CARRIER_UNIT and not S.recovered[pname] then
      S.recovered[pname] = true
      S.airborne[pname] = S.airborne[pname] or e.initiator:getName()
      local okf, fuel = pcall(e.initiator.getFuel, e.initiator)
      if okf and fuel and fuel < C.MIN_FUEL then S.lowFuel[pname] = fuel end
      T.debrief(pname, e.initiator.getName and e.initiator:getName() or nil)
      T.summary(false)
    end
  end
end

------------------------------------------------------------------ init
function T.init()
  world.addEventHandler(T.handler)
  T.setSAM(true)
  T.setAAA()
  T.totalTargets = #targetUnits()
  for _, u in ipairs(targetUnits()) do T.targetPos[#T.targetPos + 1] = u:getPoint() end

  local j = Group.getByName(C.JTAC_UNIT)
  if j then
    local ctl = j:getController()
    ctl:setCommand({ id = "SetInvisible", params = { value = true } })
    ctl:setCommand({ id = "SetImmortal", params = { value = true } })
    ctl:setOption(AI.Option.Air.id.ROE, AI.Option.Air.val.ROE.WEAPON_HOLD)
  end

  local now = timer.getAbsTime()
  local function at(abs, fn)
    local delay = abs - now
    if delay < 1 then delay = 1 end
    timer.scheduleFunction(function() fn() return nil end, nil, timer.getTime() + delay)
  end

  at(C.TOT - 600, function()
    msg("MAGIC: Enfield, package check. TOT " .. clock(C.TOT) .. " in 10 minutes." ..
        (S.checkedIn and "" or "\nPONTIAC is up for check-in: F10 > Strike > JTAC Pontiac."), 15)
  end)
  at(C.FORD_SPAWN, function()
    S.fordUp = true
    local g = Group.getByName(C.FORD_GROUP)
    if g then
      local ok = pcall(function() g:activate() end)
      if not ok then trigger.action.activateGroup(g) end
    end
    msg("FORD: FORD 1-1, two jets, inbound from the south, transiting to our tasking up north. Jammers on the SA-6 as we pass, " ..
        "planned " .. hms(SUP_ON) .. "-" .. hms(SUP_OFF) .. "L.", 15)
    timer.scheduleFunction(T.fordTick, nil, timer.getTime() + 1)
  end)
  at(SUP_OFF + 5, T.lateCheck)   -- after FORD's tick has closed the window (3 s debounce)
  timer.scheduleFunction(function() T.patrolInit() return nil end, nil, timer.getTime() + 2)
  at(C.TOT - 300, function()
    msg("FORD: On track. Jammers on the Straight Flush about " .. clock(SUP_ON) ..
        ". Do not arrive early, the SA-6 is live until then.", 20)
  end)

  local root = missionCommands.addSubMenuForCoalition(BLUE, "Strike")
  missionCommands.addCommandForCoalition(BLUE, "Time check", root, T.timeCheck)
  missionCommands.addCommandForCoalition(BLUE, "Request CAP cover", root, T.requestCAP)
  local jm = missionCommands.addSubMenuForCoalition(BLUE, "JTAC Pontiac", root)
  missionCommands.addCommandForCoalition(BLUE, "1. Check in", jm, T.checkIn)
  missionCommands.addCommandForCoalition(BLUE, "2. Ready to copy 9-line", jm, T.nineLine)
  missionCommands.addCommandForCoalition(BLUE, "3. Read back 4, 6, restrictions", jm, T.readBack)
  missionCommands.addCommandForCoalition(BLUE, "Request mark (red smoke)", jm, T.smoke)
  missionCommands.addCommandForCoalition(BLUE, "Mission summary now", root, function() T.summary(true) end)
  for _, name in ipairs(C.JETS) do
    local sm = missionCommands.addSubMenuForCoalition(BLUE, name, jm)
    missionCommands.addCommandForCoalition(BLUE, "IN (heading auto)", sm, function() T.callIn(name) end)
    missionCommands.addCommandForCoalition(BLUE, "Ten seconds (laser on)", sm, function() T.tenSeconds(name) end)
    missionCommands.addCommandForCoalition(BLUE, "Spot", sm, function() T.spot(name) end)
    missionCommands.addCommandForCoalition(BLUE, "Terminate (laser off)", sm, function() T.terminate(name) end)
    missionCommands.addCommandForCoalition(BLUE, "OFF (request BDA)", sm, function() T.off(name) end)
  end

  msg("OPERATION NARROW GATE. TOT " .. clock(C.TOT) .. ", impact window +/-" .. C.WINDOW ..
      " s, jamming " .. hms(SUP_ON) .. "-" .. hms(SUP_OFF) .. "L. F10 > Strike for time checks, CAP and JTAC Pontiac.", 20)
end

T.init()
