-- Operation Stone Ford (Narrow Gate campaign, partial / failure branch)
-- Close air support at the Inguri. Red attacks in waves toward Blue's bridgehead at Ganmukhuri;
-- Red wins if enough vehicles reach it. Ground JTAC AXEMAN, Type 1 control. Requires common.lua.

SF = SF or {}
local T = SF
local N = NG

T.cfg = T.cfg or {
  NAME = "OPERATION STONE FORD", START = 37800,
  WAVES = { { group = "Wave 1", time = 39000 } },
  BLUE_GROUP = "Bridgehead", JTAC_UNIT = "Axeman", LASER_CODE = 1688,
  BRIDGE = { x = 0, z = 0 }, BRIDGE_R = 1200, CONTACT_R = 3000, DANGER_R = 1000, FRAT_R = 150,
  LOST_AT = 3, HELD_MAX = 1,
  FAH_TEXT = "020-070 or 200-250", FAH = { { 20, 70 }, { 200, 250 } },
  IP = { x = 0, z = 0 }, MIG_GROUP = "Red CAP", MIG_TIME = 0, MIG_TEXT = "",
  CAP_GROUP = "Chevy", CAP_FLAG = "51", CAP_MODE = "commit", JETS = { "Enfield 1-1", "Enfield 1-2" },
  VIS_NM = 8, NEXT_RESCUE = "Operation_Sandy_Lift.miz",
}
local C = T.cfg
local CLEAR_VALID = 120

T.s = { through = 0, total = 0, active = {}, contact = {}, frat = 0, jet = {}, nine = nil, readFor = nil,
        checkedIn = false, over = false, startPos = {} }
local S = T.s

local function jet(n)
  S.jet[n] = S.jet[n] or { cleared = nil, released = 0, uncleared = 0, impacts = {}, passes = 0, bdaPending = false }
  return S.jet[n]
end

local function redUnits(onlyActive)
  local out = {}
  for _, w in ipairs(C.WAVES) do
    if not onlyActive or S.active[w.group] then
      for _, u in ipairs(N.liveUnits(w.group)) do out[#out + 1] = { u = u, g = w.group } end
    end
  end
  return out
end
local function killed() return S.total - #redUnits(false) - S.through end

-- priority target: the active group whose nearest vehicle is closest to the bridgehead
local function priority()
  local best, bd
  for _, w in ipairs(C.WAVES) do
    if S.active[w.group] then
      for _, u in ipairs(N.liveUnits(w.group)) do
        local d = N.dist(u:getPoint(), C.BRIDGE)
        if not bd or d < bd then best, bd = w.group, d end
      end
    end
  end
  return best, bd
end
local function groupLead(gname)
  local list = N.liveUnits(gname)
  table.sort(list, function(a, b) return N.dist(a:getPoint(), C.BRIDGE) < N.dist(b:getPoint(), C.BRIDGE) end)
  return list[1], #list
end
local function nearestBlue(p)
  local best
  for _, u in ipairs(N.liveUnits(C.BLUE_GROUP)) do
    local d = N.dist(p, u:getPoint())
    if not best or d < best then best = d end
  end
  local j = N.liveUnit(C.JTAC_UNIT)
  if j then local d = N.dist(p, j:getPoint()); if not best or d < best then best = d end end
  return best or 1e9
end

------------------------------------------------------------------ battle
function T.activateWave(w)
  N.activate(w.group)
  S.active[w.group] = true
  local g = Group.getByName(w.group)
  if g then
    local c = g:getController()
    c:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.WEAPON_HOLD)
    c:setOption(AI.Option.Ground.id.ALARM_STATE, AI.Option.Ground.val.ALARM_STATE.RED)
  end
  local lead, n = groupLead(w.group)
  if not lead then return end
  local p = lead:getPoint()
  N.msg(string.format("AXEMAN: %s is moving, %d vehicles, %.1f km %s of the bridgehead. Expect contact in about %d minutes.",
        w.group, n, N.dist(p, C.BRIDGE) / 1000, N.compass(N.bearing(C.BRIDGE, p)),
        math.max(1, math.floor((N.dist(p, C.BRIDGE) - C.CONTACT_R) / 6 / 60 + 0.5))), 20)
end

function T.tick(_, t)
  for _, w in ipairs(C.WAVES) do
    if S.active[w.group] then
      for _, u in ipairs(N.liveUnits(w.group)) do
        local d = N.dist(u:getPoint(), C.BRIDGE)
        if d <= C.BRIDGE_R then
          S.through = S.through + 1
          pcall(function() u:destroy() end)
          N.msg(string.format("AXEMAN: Vehicle THROUGH the line! %d through, %d more and the bridges are lost.",
                S.through, math.max(0, C.LOST_AT - S.through)), 15)
        elseif d <= C.CONTACT_R and not S.contact[w.group] then
          S.contact[w.group] = true
          local g = Group.getByName(w.group)
          if g then g:getController():setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.OPEN_FIRE) end
          N.msg("AXEMAN: TROOPS IN CONTACT with " .. w.group .. ". Taking fire at the bridgehead!", 15)
        end
      end
    end
  end
  local allActive = true
  for _, w in ipairs(C.WAVES) do if not S.active[w.group] then allActive = false end end
  if allActive and #redUnits(false) == 0 and not S.over then
    S.over = true
    N.msg(string.format("AXEMAN: All waves accounted for. %d destroyed, %d through. %s",
          killed(), S.through, S.through >= C.LOST_AT and "The bridges are lost." or "The bridgehead HOLDS."), 25)
  end
  return t + 3
end

------------------------------------------------------------------ JTAC flow
function T.checkIn()
  S.checkedIn = true
  local n = 0
  for _, name in ipairs(C.JETS) do if N.liveUnit(name) then n = n + 1 end end
  N.msg(string.format("ENFIELD: Axeman, Enfield 1-1, checking in, %d F/A-18C. GBU-12, Rockeye, Mavericks, LITENING, laser %d. Playtime 30.",
        math.max(n, 1), C.LASER_CODE), 15)
  timer.scheduleFunction(function()
    N.msg("AXEMAN: Enfield, Axeman. Situation: the battalion that got past the depot is attacking our bridgehead at " ..
      "Ganmukhuri in waves from the north-west. We are light infantry, almost out of anti-armour. " ..
      "Friendlies are in and around the village. Anything that reaches the village edge, " .. C.BRIDGE_R ..
      " m from the bridges, is through.\n" ..
      "Threats: " .. C.MIG_TEXT .. "\nGAME PLAN: Type 1 control, I need to see you on every pass. Laser from my position, code " ..
      C.LASER_CODE .. ". Final attack headings " .. C.FAH_TEXT .. ", along the front, never toward the village.\n" ..
      "A new 9-line for each target group, read back lines 4, 6 and restrictions each time. Advise ready to copy.", 40)
    return nil
  end, nil, timer.getTime() + 3)
end

function T.nineLine()
  if not S.checkedIn then N.msg("AXEMAN: Enfield, check in first.", 8) return end
  local g, d = priority()
  if not g then N.msg("AXEMAN: No targets at this time. Hold at the IP.", 10) return end
  local lead, n = groupLead(g)
  local p = lead:getPoint()
  local ll, mgrs, elev = N.coord(p)
  local fd = math.floor(nearestBlue(p) / 10 + 0.5) * 10
  local danger = fd <= C.DANGER_R
  local ipb = math.floor(N.bearing(C.IP, p) + 0.5)
  local ipd = N.dist(C.IP, p) / 1852
  S.nine = { group = g, danger = danger, elev = elev, mgrs = mgrs, t = timer.getAbsTime() }
  S.readFor = nil
  N.msg(string.format("AXEMAN: 9-line follows, target %s.\n1. IP: \"IP\"\n2. %03d true, offset left\n3. %.1f nm\n4. %s\n" ..
    "5. %d armoured vehicles moving south-east\n6. %s  (%s)\n7. Laser, Axeman, code %d\n8. Friendlies %d m %s of target, bridgehead at Ganmukhuri\n" ..
    "9. Egress west over the water\nRemarks: final attack heading %s.%s Read back 4, 6 and restrictions.",
    g, ipb, ipd, elev, n, mgrs, ll, C.LASER_CODE, fd, N.compass(N.bearing(p, C.BRIDGE)), C.FAH_TEXT,
    danger and " DANGER CLOSE, my initials WH." or ""), 60)
end

function T.readBack()
  if not S.nine then N.msg("AXEMAN: No 9-line passed yet.", 8) return end
  S.readFor = S.nine.group
  N.msg("ENFIELD: " .. S.nine.elev .. ", " .. S.nine.mgrs .. ", final attack heading " .. C.FAH_TEXT ..
        (S.nine.danger and ", danger close, initials WH." or "."), 12)
  timer.scheduleFunction(function()
    N.msg("AXEMAN: Readback correct. Call IN with heading.", 10)
    return nil
  end, nil, timer.getTime() + 2)
end

local function fahOK(h)
  for _, r in ipairs(C.FAH) do if h >= r[1] and h <= r[2] then return true end end
  return false
end

function T.callIn(name)
  local u = N.liveUnit(name)
  if not u then N.msg("AXEMAN: " .. name .. " not on station.", 8) return end
  local js = jet(name)
  local h = N.heading(u)
  local p = u:getPoint()
  N.msg(string.format("%s: IN, heading %03d.", name:upper(), math.floor(h + 0.5)), 8)
  local function abort(why) N.msg("AXEMAN: " .. name .. ", ABORT ABORT ABORT. " .. why, 15) end
  if not S.nine or S.readFor ~= S.nine.group then abort("No readback for the current 9-line.") return end
  if #N.liveUnits(S.nine.group) == 0 then abort(S.nine.group .. " is destroyed. Copy a new 9-line.") return end
  if not fahOK(h) then abort(string.format("Heading %03d is outside final attack heading %s.", math.floor(h + 0.5), C.FAH_TEXT)) return end
  local j = N.liveUnit(C.JTAC_UNIT)
  local jp = j and j:getPoint() or C.BRIDGE
  local eye = { x = jp.x, y = jp.y + 2, z = jp.z }
  if N.dist(p, jp) / 1852 > C.VIS_NM or not land.isVisible(eye, p) then
    N.msg("AXEMAN: " .. name .. ", CONTINUE. No joy, I don't see you. Call IN again inside " .. C.VIS_NM .. " nm.", 12)
    return
  end
  js.cleared, js.passes = timer.getAbsTime(), js.passes + 1
  js.impacts, js.bdaPending = {}, false
  N.msg("AXEMAN: " .. name .. ", I have you in sight. CLEARED HOT on " .. S.nine.group .. "." ..
        (S.nine.danger and " Danger close." or "") .. (N.laser.on and "" or " Call ten seconds for laser."), 12)
end

function T.tenSeconds(name)
  N.msg(name:upper() .. ": Ten seconds.", 6)
  local g = S.nine and S.nine.group or priority()
  if not g then N.msg("AXEMAN: Unable laser, no target.", 8) return end
  N.laserStart(C.JTAC_UNIT, function() local l = groupLead(g); return l and l:getPoint() or nil end, C.LASER_CODE, "AXEMAN",
    function() N.msg("AXEMAN: " .. g .. " destroyed, laser off. Copy a new 9-line.", 10) end)
  timer.scheduleFunction(function() N.msg("AXEMAN: Laser on, code " .. C.LASER_CODE .. ".", 8) return nil end, nil, timer.getTime() + 1)
end

local function bda(name)
  local js = jet(name)
  js.bdaPending = false
  local best
  for _, i in ipairs(js.impacts) do if not best or i.miss < best.miss then best = i end end
  local first = (#js.impacts == 0) and "no impacts observed" or (#js.impacts .. " impact" .. (#js.impacts > 1 and "s" or "") ..
    (best.miss <= 15 and ", direct hit" or string.format(", closest %d m %s of a vehicle", math.floor(best.miss + 0.5), N.compass(best.dir))))
  N.msg(string.format("AXEMAN: %s, BDA: %s.\n%d destroyed, %d through, %d still coming.", name, first, killed(), S.through,
        #redUnits(true)), 20)
end

function T.status()
  local g, d = priority()
  N.msg(string.format("AXEMAN: %d destroyed, %d through (bridges lost at %d), %d vehicles in the attack.%s\nNext wave: %s.",
    killed(), S.through, C.LOST_AT, #redUnits(true),
    g and string.format(" Closest: %s, %.1f km out.", g, d / 1000) or "",
    (function()
      local now = timer.getAbsTime()
      for _, w in ipairs(C.WAVES) do if not S.active[w.group] then return w.group .. " at " .. N.hm(w.time) .. "L" end end
      return "none, all waves committed"
    end)()), 20)
end

------------------------------------------------------------------ events
N.on(function(e)
  if e.id ~= world.event.S_EVENT_SHOT or not e.weapon or not e.initiator or not N.playerName(e.initiator) then return end
  local kind = N.weaponKind(e.weapon)
  if kind ~= "GROUND" then return end
  local name = e.initiator:getName()
  local js = jet(name)
  js.released = js.released + 1
  if not js.cleared or timer.getAbsTime() - js.cleared > CLEAR_VALID then
    js.uncleared = js.uncleared + 1
    N.msg("AXEMAN: " .. name .. ", weapon release observed WITHOUT clearance.", 10)
  end
  N.track(e.weapon, function(p)
    if nearestBlue(p) <= C.FRAT_R then
      S.frat = S.frat + 1
      N.msg("AXEMAN: CEASE FIRE, CEASE FIRE! Impact on friendlies! " .. name .. ", that was on us.", 20)
    end
    local best, ref
    for _, r in ipairs(redUnits(true)) do
      local d = N.dist(p, r.u:getPoint())
      if not best or d < best then best, ref = d, r.u:getPoint() end
    end
    if best and best <= 600 then
      js.impacts[#js.impacts + 1] = { miss = best, dir = N.bearing(ref, p) }
      if not js.bdaPending then
        js.bdaPending = true
        timer.scheduleFunction(function() bda(name) return nil end, nil, timer.getTime() + 20)
      end
    end
  end)
end)

function N.onTrap(pname, uname)
  local js = S.jet[uname]
  local proc = "Procedure: check-in " .. (S.checkedIn and "yes" or "NO")
  if js then
    proc = proc .. string.format(", passes %d, releases %d%s", js.passes, js.released,
      js.uncleared > 0 and (", " .. js.uncleared .. " WITHOUT CLEARANCE") or ", all cleared hot")
  end
  local fuel = N.rec.lowFuel[pname] and string.format(" LOW FUEL at trap (%d%%).", math.floor(N.rec.lowFuel[pname] * 100 + 0.5)) or ""
  N.msg("DEBRIEF - " .. pname .. " recovered aboard." .. fuel .. "\n" .. proc .. ".\n" ..
        string.format("%d destroyed, %d through.", killed(), S.through), 45)
end

function N.onAllDown()
  -- anything still alive when the last jet is down keeps coming
  local alive = 0
  for _, w in ipairs(C.WAVES) do alive = alive + #N.liveUnits(w.group) end
  local through = S.through + alive
  local outcome, why
  if through >= C.LOST_AT then
    outcome, why = "FAILURE", "The bridges at Ganmukhuri are lost. Blue falls back behind the Inguri."
  elseif through <= C.HELD_MAX and S.frat == 0 then
    outcome, why = "SUCCESS", "The bridgehead holds. The Red advance dies at the Inguri."
  else
    outcome, why = "PARTIAL", "The bridgehead holds, at a cost."
  end
  local clean, reasons = N.cleanRecovery()
  trigger.action.setUserFlag("90", outcome == "SUCCESS" and 1 or (outcome == "PARTIAL" and 2 or 3))
  N.msg(C.NAME .. " - MISSION SUMMARY\n" ..
    string.format("Primary: %d of %d vehicles destroyed, %d through the line%s.\n", killed(), S.total, through,
      alive > 0 and string.format(" (including %d still advancing when you left)", alive) or "") ..
    (S.frat > 0 and string.format("FRATRICIDE: %d impact%s on friendlies.\n", S.frat, S.frat > 1 and "s" or "") or "No fratricide.\n") ..
    "Secondary - Clean recovery: " .. (clean and "ACHIEVED." or ("FAILED (" .. table.concat(reasons, "; ") .. ").")) ..
    "\n" .. N.capSummary() ..
    "\n\nOUTCOME: " .. outcome .. ". " .. why .. "\nCAMPAIGN: this is the last mission on this branch." ..
    (N.rescue(C.NEXT_RESCUE)), 90)
end

------------------------------------------------------------------ init
function T.init()
  for _, w in ipairs(C.WAVES) do
    local g = Group.getByName(w.group)
    if g then S.total = S.total + #g:getUnits() end
  end
  N.quiet(C.JTAC_UNIT)
  local bg = Group.getByName(C.BLUE_GROUP)
  if bg then
    local c = bg:getController()
    c:setCommand({ id = "SetImmortal", params = { value = true } })
    c:setOption(AI.Option.Ground.id.ROE, AI.Option.Ground.val.ROE.RETURN_FIRE)
  end
  local now = timer.getAbsTime()
  local function at(abs, fn) timer.scheduleFunction(function() fn() return nil end, nil, timer.getTime() + math.max(1, abs - now)) end
  for _, w in ipairs(C.WAVES) do at(w.time, function() T.activateWave(w) end) end
  if C.MIG_TIME > 0 then
    at(C.MIG_TIME, function()
      N.activate(C.MIG_GROUP)
      N.msg("MAGIC: Pop-up group, Red fighters heading for the Inguri.", 20)
      N.capThreat("Red fighters heading for the Inguri")
    end)
  end
  timer.scheduleFunction(T.tick, nil, timer.getTime() + 3)

  local root = missionCommands.addSubMenuForCoalition(N.BLUE, "Stone Ford")
  missionCommands.addCommandForCoalition(N.BLUE, "Axeman: battle status", root, T.status)
  missionCommands.addCommandForCoalition(N.BLUE, "Request CAP cover", root, N.requestCAP)
  missionCommands.addCommandForCoalition(N.BLUE, "Mission summary now", root, function() N.rec.summaryDone = false; N.recCheck(true) end)
  local jm = missionCommands.addSubMenuForCoalition(N.BLUE, "JTAC Axeman", root)
  missionCommands.addCommandForCoalition(N.BLUE, "1. Check in", jm, T.checkIn)
  missionCommands.addCommandForCoalition(N.BLUE, "2. Ready to copy 9-line", jm, T.nineLine)
  missionCommands.addCommandForCoalition(N.BLUE, "3. Read back 4, 6, restrictions", jm, T.readBack)
  missionCommands.addCommandForCoalition(N.BLUE, "Terminate (laser off)", jm, function() N.laserStop(false, "AXEMAN") end)
  for _, name in ipairs(C.JETS) do
    local sm = missionCommands.addSubMenuForCoalition(N.BLUE, name, jm)
    missionCommands.addCommandForCoalition(N.BLUE, "IN (heading auto)", sm, function() T.callIn(name) end)
    missionCommands.addCommandForCoalition(N.BLUE, "Ten seconds (laser on)", sm, function() T.tenSeconds(name) end)
    missionCommands.addCommandForCoalition(N.BLUE, "Spot", sm, function()
      N.msg(name:upper() .. ": Spot.", 6)
      N.msg(N.laser.on and "AXEMAN: Copy spot." or "AXEMAN: Negative, laser is off. Call ten seconds.", 8)
    end)
    missionCommands.addCommandForCoalition(N.BLUE, "OFF (request BDA)", sm, function() bda(name) end)
  end
  N.msg(C.NAME .. ". First wave moves at " .. N.clock(C.WAVES[1].time) .. ". Bridges are lost if " .. C.LOST_AT ..
        " vehicles reach the bridgehead. F10 > Stone Ford.", 25)
end

T.init()
