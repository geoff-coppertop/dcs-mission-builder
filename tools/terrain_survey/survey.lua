-- Terrain survey: samples land height and surface type on a regular grid and writes it to dcs.log.
-- Grid is in DCS local coordinates (x north, z east). Rows go north, columns east.
local S = { LAT0 = 42.20, LAT1 = 43.20, LON0 = 41.50, LON1 = 42.55, STEP = 250, PER_LINE = 100, ROWS_PER_TICK = 10 }

local function log(s) env.info("SURVEY " .. s) end

local xs, zs = {}, {}
for _, c in ipairs({ { S.LAT0, S.LON0 }, { S.LAT0, S.LON1 }, { S.LAT1, S.LON0 }, { S.LAT1, S.LON1 } }) do
  local p = coord.LLtoLO(c[1], c[2], 0)
  xs[#xs + 1], zs[#zs + 1] = p.x, p.z
end
local x0, x1 = math.floor(math.min(unpack(xs))), math.ceil(math.max(unpack(xs)))
local z0, z1 = math.floor(math.min(unpack(zs))), math.ceil(math.max(unpack(zs)))
local nx, nz = math.floor((x1 - x0) / S.STEP) + 1, math.floor((z1 - z0) / S.STEP) + 1
log(string.format("GRID %d %d %d %d %d", x0, z0, S.STEP, nx, nz))
-- projection anchors, so the grid can be checked against pydcs
for _, c in ipairs({ { 42.5, 41.6 }, { 42.5, 42.4 }, { 43.1, 41.6 }, { 43.1, 42.4 }, { 42.95, 42.19 } }) do
  local p = coord.LLtoLO(c[1], c[2], 0)
  log(string.format("LL %.4f %.4f %.1f %.1f", c[1], c[2], p.x, p.z))
end

local row = 0
local function tick()
  for _ = 1, S.ROWS_PER_TICK do
    if row >= nx then
      log("DONE")
      trigger.action.outText("Terrain survey done. Quit and send Saved Games\\DCS\\Logs\\dcs.log", 60)
      return nil
    end
    local x = x0 + row * S.STEP
    for c0 = 0, nz - 1, S.PER_LINE do
      local h, t = {}, {}
      for c = c0, math.min(c0 + S.PER_LINE, nz) - 1 do
        local p = { x = x, y = z0 + c * S.STEP }
        h[#h + 1] = string.format("%d", math.floor(land.getHeight(p) + 0.5))
        t[#t + 1] = tostring(land.getSurfaceType(p))
      end
      log(string.format("H %d %d %s", row, c0, table.concat(h, ",")))
      log(string.format("T %d %d %s", row, c0, table.concat(t)))
    end
    row = row + 1
  end
  if row % 40 == 0 then trigger.action.outText(string.format("Terrain survey: %d / %d rows", row, nx), 5, true) end
  return timer.getTime() + 0.05
end
trigger.action.outText("Terrain survey running, about a minute. Leave the mission running until it says done.", 15)
timer.scheduleFunction(tick, nil, timer.getTime() + 1)
