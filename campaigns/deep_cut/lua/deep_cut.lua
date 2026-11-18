-- Operation Deep Cut
-- Low-level gorge strike on a tunnel portal: radar floor, TOT window opened by a TLAM strike (HAMMER) on the
-- Red fighter base, two-bomb breach-then-kill attack, SAMs at the climb-out, fighters on the egress, scored tiers.
-- HATCHET, a special forces team on the ridge, lases the portal on call. A pilot who ejects over land is
-- sent to the follow-up, Operation Deep Cut: Escape.
-- Requires common.lua (NG). Pure DCS scripting engine, Lua 5.1 compatible.
--
-- The target and every Red ground site are spawned at mission start, placed with DCS's own terrain
-- (land.getHeight): valley sites on the gorge floor nearest their planned point, SAM sites on the high ground.
-- The planned points come from the builder and may be a kilometre or two off the real floor.

DC = DC or {}
local T = DC
local N = NG

-- __CONFIG__ (values are filled in by the mission builder)
T.cfg = T.cfg or {
  NAME = "OPERATION DEEP CUT", START = 36000, TOT = 38400, WINDOW = 45,
  HAMMER = 38220, REPAIR = 600, SAM_UP = 90, REACT = 45, KILL_WINDOW = 90,
  FLOOR_FT = 500, GRACE = 4, WARN = true, BREACH_R = 15, KILL_R = 15, AT_TARGET_R = 400,
  TGT = { x = 0, z = 0 }, TGT_R = 2500, DET_R = 32000, POP_R = 7000,
  SITES = {},                        -- { name, kind = "valley"|"sam"|"guard", x, z, r, live, units = { { type, dx, dz } } }
  CANYON = {},                       -- planned canyon checkpoints, gate to target: { name, x, z }
  SOUTH_GROUP = "Red South", NORTH_GROUP = "Red North", SOUTH_KIND = "two MiG-29s", NORTH_KIND = "two MiG-21s",
  SOUTH_BASE = "Kutaisi", ALERT_REACT = 90,
  TEAM = "Hatchet", TEAM_R_MIN = 1200, TEAM_R_MAX = 3000, LASER_CODE = 1688,
  JETS = { "Enfield 1-1", "Enfield 1-2", "Springfield 1-1", "Springfield 1-2" },
  NEXT_ESCAPE = "Operation_Deep_Cut_Escape.miz", RESCUE_FLAG = "91",
  PTS_BREACH = 15, PTS_KILL = 25, PTS_ONTIME = 12, PTS_UNSEEN = 8, PTS_SURVIVAL = 40,
  OUTCOME_FLAG = "90", SCORE_FLAG = "92",
}
local C = T.cfg
local FT = 0.3048

T.s = { samsLive = false, samWhy = nil, detected = nil, high = {}, warned = {}, hammer = false,
        south = nil, north = nil, firstImpact = nil, breach = nil, kill = nil, sealed = false,
        team = nil, spawned = {}, tgt = nil, floor = {}, misses = {}, shots = 0, diverted = {}, over = false }
local S = T.s

------------------------------------------------------------------ terrain
local function h(x, z) return land.getHeight({ x = x, y = z }) end

-- The gorge floor nearest a planned point. Samples a grid within r; a "channel" sample is one with ground at least
-- WALL m higher SPAN m away on both sides along some axis, and no more than DEPTH m above the lowest sample.
-- The channel sample nearest the planned point wins, refined to the lowest ground within 150 m of it.
local STEP, SPAN, WALL, DEPTH = 100, 300, 40, 200
function T.snapFloor(p, r)
  local n, k = math.floor(r / STEP), SPAN / STEP
  local H, lo = {}, nil
  for i = -n - k, n + k do
    H[i] = {}
    for j = -n - k, n + k do
      local v = h(p.x + i * STEP, p.z + j * STEP)
      H[i][j] = v
      if i * i + j * j <= n * n and (not lo or v < lo) then lo = v end
    end
  end
  local axes = { { 1, 0 }, { 0, 1 }, { 1, 1 }, { 1, -1 } }
  local best, bd
  for i = -n, n do
    for j = -n, n do
      if i * i + j * j <= n * n and H[i][j] <= lo + DEPTH then
        local v = H[i][j]
        for _, a in ipairs(axes) do
          local s1 = H[i + a[1] * k] and H[i + a[1] * k][j + a[2] * k]
          local s2 = H[i - a[1] * k] and H[i - a[1] * k][j - a[2] * k]
          if s1 and s2 and s1 - v >= WALL and s2 - v >= WALL then
            local d = i * i + j * j
            if not bd or d < bd then best, bd = { i, j }, d end
            break
          end
        end
      end
    end
  end
  if not best then   -- no channel found: take the lowest ground
    for i = -n, n do for j = -n, n do
      if i * i + j * j <= n * n and H[i][j] == lo then best = { i, j } end
    end end
  end
  local cx, cz = p.x + best[1] * STEP, p.z + best[2] * STEP
  local fx, fz, fh = cx, cz, h(cx, cz)
  for i = -3, 3 do for j = -3, 3 do
    local x, z = cx + i * 50, cz + j * 50
    local v = h(x, z)
    if v < fh then fx, fz, fh = x, z, v end
  end end
  return { x = fx, z = fz, y = fh }
end

-- dry ground at or near p: the floor of a dammed gorge can be reservoir or river
local function wet(x, z)
  if not land.getSurfaceType or not land.SurfaceType then return false end
  local ok, st = pcall(land.getSurfaceType, { x = x, y = z })
  return ok and (st == land.SurfaceType.WATER or st == land.SurfaceType.SHALLOW_WATER)
end
function T.dry(p)
  if not wet(p.x, p.z) then return p end
  for r = 40, 600, 40 do
    for a = 0, 330, 30 do
      local x, z = p.x + r * math.cos(math.rad(a)), p.z + r * math.sin(math.rad(a))
      if not wet(x, z) then return { x = x, z = z, y = h(x, z) } end
    end
  end
  return p
end

-- the highest ground within r
function T.snapHigh(p, r)
  local n = math.floor(r / STEP)
  local bx, bz, bh = p.x, p.z, h(p.x, p.z)
  for i = -n, n do for j = -n, n do
    if i * i + j * j <= n * n then
      local x, z = p.x + i * STEP, p.z + j * STEP
      local v = h(x, z)
      if v > bh then bx, bz, bh = x, z, v end
    end
  end end
  return { x = bx, z = bz, y = bh }
end

------------------------------------------------------------------ spawning
function T.spawnGround(name, at, units, heading)
  local data = { name = name, task = "Ground Nothing", units = {}, route = { points = {} } }
  for i, u in ipairs(units) do
    data.units[i] = { name = name .. " " .. i, type = u[1], x = at.x + (u[2] or 0), y = at.z + (u[3] or 0),
                      heading = heading or 0, skill = "Average", playerCanDrive = false }
  end
  local ok, err = pcall(coalition.addGroup, country.id.RUSSIA, Group.Category.GROUND, data)
  if not ok then env.info("DC spawn " .. name .. " failed: " .. tostring(err)) end
  return ok
end

function T.spawnStatic(name, typ, shape, at, dx, dz, heading)
  local ok, err = pcall(coalition.addStaticObject, country.id.RUSSIA, {
    name = name, type = typ, shape_name = shape, category = "Fortifications",
    x = at.x + (dx or 0), y = at.z + (dz or 0), heading = heading or 0, dead = false })
  if not ok then env.info("DC static " .. name .. " failed: " .. tostring(err)) end
  return ok
end

function T.spawnAll()
  -- target: the portal on the gorge floor nearest the planned point
  S.tgt = T.dry(T.snapFloor(C.TGT, C.TGT_R))
  local tg = S.tgt
  T.spawnStatic("Portal", "Fire Control Bunker", "fire_control", tg, 0, 0, 0)
  T.spawnStatic("Portal Shelter 1", "Shelter", "ukrytie", tg, 70, 60, 30)
  T.spawnStatic("Portal Shelter 2", "Shelter", "ukrytie", tg, -60, 80, 300)
  T.spawnStatic("Portal Command", ".Command Center", "ComCenter", tg, 120, -40, 0)
  T.placeTeam()
  for _, st in ipairs(C.SITES) do
    local at
    if st.kind == "sam" then at = T.snapHigh(st, st.r)
    elseif st.kind == "guard" then at = { x = tg.x + st.x, z = tg.z + st.z }
    else at = T.dry(T.snapFloor(st, st.r)) end
    if T.spawnGround(st.name, at, st.units, st.heading) then
      S.spawned[#S.spawned + 1] = { name = st.name, kind = st.kind, at = at }
      if st.kind == "sam" then N.setAD(st.name, false) else N.setAD(st.name, true) end
    end
  end
  -- the canyon as Red's floor finder sees it: F10 map guide for the players
  local prev
  for i, cp in ipairs(C.CANYON) do
    local f = (i == #C.CANYON) and { x = tg.x, z = tg.z, y = tg.y } or T.snapFloor(cp, cp.r or 1500)
    S.floor[i] = { name = cp.name, x = f.x, z = f.z, y = f.y }
    local pt = { x = f.x, y = f.y, z = f.z }
    pcall(trigger.action.markToAll, 7100 + i, cp.name .. " (gorge floor, " .. math.floor(f.y / FT + 0.5) .. " ft)", pt, true)
    if prev then
      pcall(trigger.action.lineToAll, coalition.side.BLUE, 7200 + i, prev, pt, { 0, 0.4, 1, 0.9 }, 2, true)
    end
    prev = pt
  end
  pcall(trigger.action.circleToAll, coalition.side.BLUE, 7300, { x = tg.x, y = tg.y, z = tg.z }, C.POP_R,
        { 1, 0.5, 0, 0.9 }, { 1, 0.5, 0, 0.05 }, 3, true)
end

------------------------------------------------------------------ HATCHET: the lasing team on the ridge
-- the highest ground 1.2-3 km from the portal that can see it; hidden and immortal, Blue, lases only on call
function T.placeTeam()
  local tg = S.tgt
  local aim = { x = tg.x, y = tg.y + 3, z = tg.z }
  local best
  for r = C.TEAM_R_MIN, C.TEAM_R_MAX, 300 do
    for a = 0, 340, 20 do
      local x, z = tg.x + r * math.cos(math.rad(a)), tg.z + r * math.sin(math.rad(a))
      local y = h(x, z)
      if (not best or y > best.y) and not wet(x, z) and land.isVisible({ x = x, y = y + 2, z = z }, aim) then
        best = { x = x, y = y, z = z }
      end
    end
  end
  best = best or T.snapHigh(tg, 1500)
  local ok = pcall(coalition.addGroup, country.id.USA, Group.Category.GROUND, {
    name = C.TEAM, task = "Ground Nothing", route = { points = {} },
    units = { { name = C.TEAM, type = "Soldier M4", x = best.x, y = best.z, heading = 0, skill = "Excellent", playerCanDrive = false } } })
  if ok then
    N.quiet(C.TEAM)
    S.team = best
  end
end

function T.laserOn()
  if not S.team or not N.liveUnit(C.TEAM) then N.msg("HATCHET: Unable, no team on the ridge.", 8) return end
  if S.kill then N.msg("HATCHET: Target's gone. Nothing to lase.", 8) return end
  N.laserStart(C.TEAM, function()
    if S.kill then return nil end
    return { x = S.tgt.x, y = S.tgt.y, z = S.tgt.z }
  end, C.LASER_CODE, "HATCHET")
  local d = N.dist(S.team, S.tgt)
  N.msg(string.format("HATCHET: Laser on the blast door, code %d. We're %.1f km %s of it, up high. Call terminate when done.",
        C.LASER_CODE, d / 1000, N.compass(N.bearing(S.tgt, S.team))), 12)
end

------------------------------------------------------------------ air defence and fighters
function T.samsLive(why)
  if S.samsLive then return end
  S.samsLive, S.samWhy = true, why
  for _, sp in ipairs(S.spawned) do
    if sp.kind == "sam" then N.setAD(sp.name, true) end
  end
  N.msg("MAGIC: Strobes at the head of the gorge. The climb-out SAMs are UP (" .. why .. ").", 15)
end

local function launch(which, why)
  local g = which == "south" and C.SOUTH_GROUP or C.NORTH_GROUP
  if S[which] then return end
  S[which] = { t = timer.getAbsTime(), why = why }
  N.activate(g)
  N.msg("MAGIC: Pop-up group, " .. (which == "south" and (C.SOUTH_KIND .. " off " .. C.SOUTH_BASE) or
        (C.NORTH_KIND .. " from the north, over the main range")) .. ", hot toward the gorge mouth. " .. why .. ".", 20)
end

function T.scramble(which, why, delay)
  timer.scheduleFunction(function() launch(which, why) return nil end, nil, timer.getTime() + (delay or 0))
end

function T.detected(name, agl)
  if S.detected then return end
  S.detected = { who = name, t = timer.getAbsTime(), agl = agl }
  N.msg(string.format("MAGIC: %s was seen above the floor at %d ft AGL. Red's radar has the package.\n" ..
        "Expect the climb-out SAMs up and fighters from the north.%s", name, math.floor(agl / FT + 0.5),
        (not S.hammer) and (" HAMMER hasn't hit " .. C.SOUTH_BASE .. " yet: expect the " .. C.SOUTH_BASE .. " alert too.") or ""), 20)
  T.samsLive("package detected")
  T.scramble("north", "Red saw the package", C.ALERT_REACT)
  if not S.hammer then T.scramble("south", "Red saw the package before HAMMER", C.ALERT_REACT) end
end

------------------------------------------------------------------ radar floor
local function playerJets()
  local out = {}
  for _, n in ipairs(C.JETS) do
    local u = N.liveUnit(n)
    if u and N.playerName(u) then out[#out + 1] = u end
  end
  return out
end

function T.floorTick(_, t)
  if S.firstImpact or S.over then return nil end
  for _, u in ipairs(playerJets()) do
    local p = u:getPoint()
    local n = u:getName()
    local d = N.dist(p, S.tgt)
    local agl = p.y - h(p.x, p.z)
    if d <= C.DET_R and d > C.POP_R and agl > C.FLOOR_FT * FT then
      S.high[n] = (S.high[n] or 0) + 1
      if S.high[n] == 1 and C.WARN and not S.warned[n] and not S.detected then
        S.warned[n] = true
        N.msg(string.format("MAGIC: %s, you're above the floor, %d ft AGL. Get down.", n, math.floor(agl / FT + 0.5)), 6)
      end
      if S.high[n] >= C.GRACE then T.detected(n, agl) end
    else
      S.high[n] = 0
    end
  end
  return t + 1
end

------------------------------------------------------------------ weapons
-- follow a bomb; on impact, extrapolate the last tracked step to the ground so a fast weapon scores where it hit
function T.trackBomb(w, shooter, id)
  local last, vel
  timer.scheduleFunction(function(_, t)
    local ok, alive = pcall(w.isExist, w)
    if ok and alive then
      local okp, p = pcall(w.getPoint, w)
      if okp and p then last = p end
      local okv, v = pcall(w.getVelocity, w)
      vel = okv and v or nil
      return t + 0.05
    end
    if last then
      local p = { x = last.x, y = last.y, z = last.z }
      if vel and vel.y and vel.y < -1 then
        local g = h(p.x, p.z)
        local dt = math.max(0, math.min(0.1, (p.y - g) / -vel.y))
        p = { x = p.x + vel.x * dt, y = g, z = p.z + vel.z * dt }
      end
      T.impact(p, timer.getAbsTime(), shooter, id)
    end
    return nil
  end, nil, timer.getTime() + 0.05)
end

local function grade(t)
  local d = t - C.TOT
  if d < -C.WINDOW then return "EARLY", d end
  if d > C.WINDOW then return "LATE", d end
  return "ON TIME", d
end

function T.impact(p, t, shooter, id)
  if not S.tgt then return end
  local miss = N.dist(p, S.tgt)
  if miss > C.AT_TARGET_R then return end
  if not S.firstImpact then
    S.firstImpact = t
    if t < C.HAMMER then
      T.scramble("south", "Bombs on the gorge before HAMMER hit the runway", 0)
    end
    timer.scheduleFunction(function() T.samsLive("bombs on the portal") return nil end, nil, timer.getTime() + C.REACT)
  end
  if not S.breach then
    if miss <= C.BREACH_R then
      local v, d = grade(t)
      S.breach = { t = t, who = shooter, id = id, verdict = v, delta = d }
      S.sealAt = t + C.KILL_WINDOW
      pcall(trigger.action.explosion, { x = S.tgt.x, y = S.tgt.y + 2, z = S.tgt.z }, 400)
      N.msg(string.format("%s: Shack! The blast door is down. Breach %s (%s vs TOT %s).\n" ..
            "Next bomb through the portal before %s or they close the inner door.",
            shooter, v, N.mmss(d), N.hms(C.TOT), N.hms(S.sealAt)), 20)
      timer.scheduleFunction(function()
        if not S.kill then
          S.sealed = true
          N.msg("MAGIC: The portal is sealed. The inner door is closed, the target survives.", 20)
        end
        return nil
      end, nil, timer.getTime() + C.KILL_WINDOW + 0.5)
    else
      S.misses[#S.misses + 1] = miss
      N.msg(string.format("%s: Miss, %d m %s of the blast door. Door still up.", shooter, math.floor(miss + 0.5),
            N.compass(N.bearing(S.tgt, p))), 12)
    end
    return
  end
  if S.kill or S.sealed then return end
  if miss <= C.KILL_R and id ~= S.breach.id and t <= S.sealAt then
    S.kill = { t = t, who = shooter }
    pcall(trigger.action.explosion, { x = S.tgt.x, y = S.tgt.y + 2, z = S.tgt.z }, 3000)
    if N.laser.on then N.laserStop(true) end
    N.msg(string.format("%s: Through the portal! Secondaries in the tunnel. TARGET DESTROYED, %d s after the breach.\n" ..
          "Get out of the gorge. Climb-out SAMs and fighters will be coming up.", shooter, math.floor(t - S.breach.t + 0.5)), 25)
  else
    S.misses[#S.misses + 1] = miss
    N.msg(string.format("%s: Miss, %d m off the portal. Door's open, %d s left.", shooter, math.floor(miss + 0.5),
          math.max(0, math.floor(S.sealAt - t + 0.5))), 12)
  end
end

------------------------------------------------------------------ score
function T.score()
  local sc = { target = 0, timing = 0, survival = 0, launched = 0, home = 0, lost = {}, lines = {} }
  if S.breach then sc.target = sc.target + C.PTS_BREACH end
  if S.kill then sc.target = sc.target + C.PTS_KILL end
  if S.breach and S.breach.verdict == "ON TIME" then sc.timing = sc.timing + C.PTS_ONTIME end
  if not S.detected and (S.breach or S.firstImpact) then sc.timing = sc.timing + C.PTS_UNSEEN end
  for pname in pairs(N.rec.airborne) do
    sc.launched = sc.launched + 1
    if N.rec.recovered[pname] and not N.rec.lost[pname] then sc.home = sc.home + 1
    else sc.lost[#sc.lost + 1] = pname .. (N.rec.lost[pname] and (" " .. N.rec.lost[pname]) or " not home") end
  end
  if sc.launched > 0 then sc.survival = math.floor(C.PTS_SURVIVAL * sc.home / sc.launched + 0.5) end
  sc.total = sc.target + sc.timing + sc.survival
  -- the grade needs the kill: without it the best you can do is PARTIAL, however many jets came home
  if S.kill and sc.total >= 90 then sc.grade = "TEXTBOOK"
  elseif S.kill and sc.total >= 70 then sc.grade = "SUCCESS"
  elseif sc.total >= 45 then sc.grade = "PARTIAL"
  else sc.grade = "FAILURE" end
  return sc
end

function T.summary()
  if S.over then return end
  S.over = true
  local sc = T.score()
  local tgt
  if S.kill then tgt = "portal breached and the tunnel destroyed"
  elseif S.breach then tgt = "portal breached, no bomb through it" .. (S.sealed and " before it was sealed" or "")
  elseif S.firstImpact then tgt = "bombs on the portal area, no breach"
  else tgt = "no bombs on the portal" end
  local tim = S.breach and (S.breach.verdict .. " (" .. N.mmss(S.breach.delta) .. ")") or "no breach"
  local alerts = {}
  if S.detected then alerts[#alerts + 1] = "seen above the floor (" .. S.detected.who .. ")" end
  if S.samsLive then alerts[#alerts + 1] = "climb-out SAMs up: " .. S.samWhy end
  if S.south then alerts[#alerts + 1] = C.SOUTH_BASE .. " alert launched" end
  if S.north then alerts[#alerts + 1] = "northern alert launched" end
  trigger.action.setUserFlag(C.OUTCOME_FLAG, ({ TEXTBOOK = 1, SUCCESS = 2, PARTIAL = 3, FAILURE = 4 })[sc.grade])
  trigger.action.setUserFlag(C.SCORE_FLAG, sc.total)
  local rescue, onLand = N.rescue(C.NEXT_ESCAPE)
  trigger.action.setUserFlag(C.RESCUE_FLAG, onLand)
  N.msg(C.NAME .. " - MISSION SUMMARY\n" ..
    string.format("Target %d/%d: %s.\n", sc.target, C.PTS_BREACH + C.PTS_KILL, tgt) ..
    string.format("Timing %d/%d: breach %s, %s.\n", sc.timing, C.PTS_ONTIME + C.PTS_UNSEEN, tim,
                  S.detected and "package detected" or "never seen above the floor") ..
    string.format("Survival %d/%d: %d of %d jets home%s.\n", sc.survival, C.PTS_SURVIVAL, sc.home, sc.launched,
                  #sc.lost > 0 and (" (" .. table.concat(sc.lost, "; ") .. ")") or "") ..
    (#alerts > 0 and ("Red: " .. table.concat(alerts, "; ") .. ".\n") or "Red never reacted.\n") ..
    string.format("\nSCORE %d/100: %s.", sc.total, sc.grade) .. rescue, 90)
end

------------------------------------------------------------------ menus
function T.timeCheck()
  local now = timer.getAbsTime()
  local d = C.TOT - now
  local state
  if S.kill then state = "Target destroyed. Egress."
  elseif S.breach then state = "Door down, " .. math.max(0, math.floor(S.sealAt - now + 0.5)) .. " s to put a bomb through."
  elseif now < C.HAMMER then state = "HAMMER hits " .. C.SOUTH_BASE .. " at " .. N.hms(C.HAMMER) .. "L. Don't arrive early."
  else state = "HAMMER is in. " .. C.SOUTH_BASE .. " alert grounded until about " .. N.hms(C.HAMMER + C.REPAIR) .. "L." end
  N.msg(string.format("Time %s\nTOT %s (%s), window +/-%d s\n%s\nRadar floor %d ft AGL: %s. Climb-out SAMs: %s.",
    N.clock(now), N.clock(C.TOT), d >= 0 and ("in " .. N.mmss(d):sub(2)) or (N.mmss(-d):sub(2) .. " ago"), C.WINDOW, state,
    C.FLOOR_FT, S.detected and "DETECTED" or "not seen", S.samsLive and "UP" or "quiet"), 15)
end

function T.targetInfo()
  if not S.tgt then return end
  local ll, mgrs, elev = N.coord({ x = S.tgt.x, y = S.tgt.y, z = S.tgt.z })
  N.msg("TARGET: blast door, tunnel portal on the gorge floor.\n" .. ll .. "\n" .. mgrs .. "\n" .. elev ..
        "\nEnter it as a waypoint or markpoint: the TGT waypoint is the planned point, this is the real one." ..
        " The F10 map shows the gorge floor from the gate to the portal.", 40)
end

------------------------------------------------------------------ events
N.on(function(e)
  if e.id == world.event.S_EVENT_SHOT and e.weapon and e.initiator and N.playerName(e.initiator) then
    if N.weaponKind(e.weapon) == "GROUND" then
      S.shots = S.shots + 1
      T.trackBomb(e.weapon, e.initiator:getName(), S.shots)
    end
  elseif e.id == world.event.S_EVENT_LAND and e.initiator and e.place and e.place.getName then
    local pname = N.playerName(e.initiator)
    if pname and e.place:getName() ~= N.rec.carrier and not N.rec.recovered[pname] and N.rec.airborne[pname] then
      N.rec.recovered[pname] = true
      S.diverted[pname] = e.place:getName()
      N.msg("MAGIC: " .. pname .. " is down safe at " .. e.place:getName() .. ".", 15)
    end
  end
end)

function N.onTrap(pname, uname)
  N.msg("MAGIC: " .. pname .. " is aboard. " .. (S.kill and "Target destroyed." or (S.breach and "Door down, no kill." or "No breach.")), 15)
end

function N.onAllDown() T.summary() end

------------------------------------------------------------------ init
function T.init()
  T.spawnAll()
  local now = timer.getAbsTime()
  local function at(abs, fn) timer.scheduleFunction(function() fn() return nil end, nil, timer.getTime() + math.max(1, abs - now)) end

  at(C.HAMMER, function()
    S.hammer = true
    N.msg("HAMMER: TLAMs impacting " .. C.SOUTH_BASE .. ". Runway cut, the alert is on the ground for about " ..
          math.floor(C.REPAIR / 60 + 0.5) .. " minutes. Window " .. N.hms(C.TOT - C.WINDOW) .. "-" .. N.hms(C.TOT + C.WINDOW) .. "L.", 20)
  end)
  at(C.HAMMER + C.REPAIR, function() launch("south", C.SOUTH_BASE .. " has a strip open again") end)
  at(C.TOT + C.WINDOW + 1, function()
    if not S.breach then N.msg("MAGIC: Window closed, no breach. Every minute in that gorge costs you now.", 15) end
  end)
  at(C.TOT + C.SAM_UP, function() T.samsLive("Red alerted by HAMMER") end)
  at(C.TOT - 600, function()
    N.msg("MAGIC: Package check, TOT " .. N.clock(C.TOT) .. " in 10 minutes. Floor is " .. C.FLOOR_FT ..
          " ft AGL from the gate at Jvari. HATCHET lases on call: F10 > Deep Cut.", 15)
  end)
  timer.scheduleFunction(T.floorTick, nil, timer.getTime() + 1)

  local root = missionCommands.addSubMenuForCoalition(N.BLUE, "Deep Cut")
  missionCommands.addCommandForCoalition(N.BLUE, "Time check", root, T.timeCheck)
  missionCommands.addCommandForCoalition(N.BLUE, "Target coordinates", root, T.targetInfo)
  missionCommands.addCommandForCoalition(N.BLUE, "Hatchet: laser on the door", root, T.laserOn)
  missionCommands.addCommandForCoalition(N.BLUE, "Hatchet: terminate (laser off)", root, function() N.laserStop(false, "HATCHET") end)
  missionCommands.addCommandForCoalition(N.BLUE, "Mission summary now", root, function() N.rec.summaryDone = false; N.recCheck(true) end)

  N.msg(C.NAME .. ". TOT " .. N.clock(C.TOT) .. ", window +/-" .. C.WINDOW .. " s. Radar floor " .. C.FLOOR_FT ..
        " ft AGL. F10 > Deep Cut for time checks, the target's exact coordinates and HATCHET's laser.", 20)
  timer.scheduleFunction(function() T.targetInfo() return nil end, nil, timer.getTime() + 5)
end

T.init()
