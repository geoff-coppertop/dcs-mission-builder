-- Operation Deep Cut: Escape (follow-up when a Deep Cut pilot ejects over land)
-- HATCHET has brought the downed pilot onto Senaki-Kolkhi, where Red keeps an alert F-14A. Start it, get
-- airborne before the guards notice, and run for the boat with the Kutaisi alert behind you. CHEVY (cap.lua)
-- holds at the coast. Requires common.lua (NG) and cap.lua (CAPCTL).

ESC = ESC or {}
local T = ESC
local N = NG

-- __CONFIG__ (values are filled in by the mission builder)
T.cfg = T.cfg or {
  NAME = "OPERATION DEEP CUT: ESCAPE", START = 32400, DISCOVER = 480, TAKEOFF_NOTICE = 20, ALERT_REACT = 90,
  FIELD = "Senaki-Kolkhi", FIELD_AD = { "Senaki Guns North", "Senaki Guns South", "Senaki SA-13" },
  SOUTH_GROUP = "Red South", SOUTH_KIND = "two MiG-29s", SOUTH_BASE = "Kutaisi",
  JET = "Enfield 1-1", OUTCOME_FLAG = "90",
}
local C = T.cfg
T.s = { found = nil, launched = nil, airborne = false, kills = 0, over = false }
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

function T.status()
  local now = timer.getAbsTime()
  local line
  if S.found then line = "Red knows: " .. S.found.why .. "." .. (S.launched and " Fighters airborne." or " Fighters launching.")
  else line = "Not seen yet. Guards expected at about " .. N.hms(C.START + C.DISCOVER) .. "L (" ..
             N.mmss(C.START + C.DISCOVER - now):sub(2) .. ")." end
  N.msg("Time " .. N.clock(now) .. "\n" .. line .. "\n" .. N.capSummary(), 15)
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
  if home then outcome, why = "SUCCESS", "The pilot is home, in a jet Red had to watch leave."
  elseif kind == "water" then outcome, why = "PARTIAL", "Down over the water: the Navy picks the crew up. The jet is gone."
  else outcome, why = "FAILURE", "Down over Red territory again." end
  trigger.action.setUserFlag(C.OUTCOME_FLAG, ({ SUCCESS = 1, PARTIAL = 2, FAILURE = 3 })[outcome])
  N.msg(C.NAME .. " - SUMMARY\n" ..
    (S.found and ("Seen at " .. N.hms(S.found.t) .. "L: " .. S.found.why .. ".") or "Never seen.") .. "\n" ..
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
  missionCommands.addCommandForCoalition(N.BLUE, "Mission summary now", root, function() N.rec.summaryDone = false; N.recCheck(true) end)
  N.msg(C.NAME .. ". You're in the Tomcat on the " .. C.FIELD .. " ramp. HATCHET thinks the guards check this end at about " ..
        N.hms(C.START + C.DISCOVER) .. "L. Be gone by then. F10 > Escape for status.", 25)
end

T.init()
