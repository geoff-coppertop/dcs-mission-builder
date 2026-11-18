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
  CODE = "KESTREL", CARRIER = "CVN-74 Stennis", ID_R = 83340, VID_R = 3700, VID_S = 8, KEEP_CLEAR = 18520,
}
local C = T.cfg
T.s = { found = nil, launched = nil, airborne = false, kills = 0, over = false,
        authed = nil, unknown = nil, identified = nil, vid = 0, warned = 0, trapUnknown = false, waitSaid = nil }
local S = T.s

function T.discover(why)
  if S.found then return end
  S.found = { t = timer.getAbsTime(), why = why }
  for _, g in ipairs(C.FIELD_AD) do N.setAD(g, true) end
  N.msg("HATCHET: They've seen you (" .. why .. "). The field's guns are waking up. GO.", 15)
  timer.scheduleFunction(function()
    S.launched = timer.getAbsTime()
    N.activate(C.SOUTH_GROUP)
    N.msg("MAGIC: Pop-up group, " .. C.SOUTH_KIND .. " off " .. C.SOUTH_BASE .. ", hot west after the Tomcat.", 20)
    N.capThreat(C.SOUTH_KIND .. " off " .. C.SOUTH_BASE .. ", chasing Enfield")
    return nil
  end, nil, timer.getTime() + C.ALERT_REACT)
end

------------------------------------------------------------------ identification
local LABEL = "the unknown Tomcat"
local function known() return S.authed or S.identified end
local function jet() local u = N.liveUnit(C.JET) return u and N.playerName(u) and u or nil end
local function mother() local cv = N.liveUnit(C.CARRIER) return cv and cv:getPoint() end

function T.checkIn()
  local u = jet()
  if not u or not S.airborne then N.msg("Nobody can hear you from the ground. Get airborne first.", 8) return end
  if S.authed then N.msg("MAGIC: You're authenticated already. Come home.", 8) return end
  S.authed = timer.getAbsTime()
  N.msg("MAGIC: Unknown Tomcat, authenticate. ... " .. C.CODE .. " is correct. Enfield, good to hear you.\n" ..
        "You're friendly on our scope. Mother has you cleared in. Expect " .. CAPCTL.call() .. " to take a look on the way.", 20)
end

function T.commitIntercept(p)
  CAPCTL.commit("request", { x = p.x, z = p.z }, LABEL, "unknown Tomcat inbound",
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

function T.idTick(_, t)
  if S.over then return nil end
  local u, cvp = jet(), mother()
  if not u or not cvp then return t + 2 end
  local p = u:getPoint()
  if not S.unknown and not known() and S.airborne and N.dist(p, cvp) < C.ID_R then
    S.unknown = timer.getAbsTime()
    N.msg(string.format("MAGIC: Unknown Tomcat, %d nm east of Mother, inbound. Not squawking anything we know.\n" ..
          "%s, intercept and identify. Weapons hold on the Tomcat.", math.floor(N.dist(p, cvp) / 1852 + 0.5), CAPCTL.call()), 20)
    T.commitIntercept(p)
  end
  if S.unknown and not known() then
    local c = CAPCTL.cap
    -- a higher-priority commit (the MiGs) drops the intercept in cap.lua: pick it up again once CHEVY is free
    if c and not c.mode then
      N.msg("MAGIC: " .. CAPCTL.call() .. ", back to the unknown Tomcat. Intercept and identify, weapons hold.", 12)
      S.waitSaid = nil
      T.commitIntercept(p)
    elseif c and c.mode ~= "committed" or (c and c.task and c.task.label ~= LABEL) then
      if S.waitSaid ~= (c and c.mode) then
        S.waitSaid = c and c.mode
        N.msg("MAGIC: Unknown Tomcat, " .. (c.mode == "out" and "there's nobody free to look at you" or
              (CAPCTL.call() .. " is busy with the MiGs")) .. ". Stay outside 10 nm of Mother until you're identified, or authenticate.", 15)
      end
    end
    if c and c.mode == "committed" and c.task and c.task.label == LABEL then
      if (t % 10) < 2 then steer(c.group, p) end
      local close = false
      for _, w in ipairs(N.liveUnits(c.group)) do
        if N.dist(w:getPoint(), p) < C.VID_R then close = true end
      end
      S.vid = close and (S.vid + 2) or 0
      if S.vid >= C.VID_S then
        S.identified = timer.getAbsTime()
        N.msg("CHEVY: Tally one Tomcat, foreign paint. Pilot's waving, he's holding up a kneeboard: ENFIELD. Looks like ours.\n" ..
              "MAGIC: Copy, declaring the Tomcat friendly. Mother has you cleared in.", 20)
      end
    end
  end
  if not known() and N.dist(p, cvp) < C.KEEP_CLEAR and timer.getAbsTime() - S.warned > 30 then
    S.warned = timer.getAbsTime()
    N.msg("MOTHER: Unidentified Tomcat, you are NOT cleared. Remain outside 10 nm until identified.", 10)
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

function N.onTrap(pname)
  if known() then N.msg("MOTHER: " .. pname .. " aboard in somebody else's Tomcat. Welcome home.", 20)
  else
    S.trapUnknown = true
    N.msg("MOTHER: An unidentified Tomcat just trapped without clearance. Marines to the flight deck.", 20)
  end
end

function N.onAllDown()
  if S.over then return end
  S.over = true
  local home, kind = false, nil
  for p in pairs(N.rec.airborne) do
    if N.rec.recovered[p] and not N.rec.lost[p] then home = true end
    kind = N.rec.lossKind[p] or kind
  end
  local outcome, why
  if home and not S.trapUnknown then outcome, why = "SUCCESS", "The pilot is home, in a jet Red had to watch leave."
  elseif home then outcome, why = "PARTIAL", "Home, but unannounced: an unidentified jet on the deck. Expect a long talk with the Captain."
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
        C.CODE .. ". F10 > Escape.", 25)
end

T.init()
