"""List any ground unit or ground waypoint that falls in the sea (1 km coastline resolution)."""
import sys, zipfile, lupa, dcs
from dcs import mapping
from global_land_mask import globe
terrain = dcs.terrain.Caucasus()
for path in sys.argv[1:]:
    L = lupa.LuaRuntime(unpack_returned_tuples=True)
    with zipfile.ZipFile(path) as z: L.execute(z.read("mission").decode("utf-8"))
    mis = L.globals().mission; bad = []; n = 0
    for side in ("blue", "red"):
        for _, c in mis.coalition[side].country.items():
            if not c.vehicle: continue
            for _, g in c.vehicle.group.items():
                pts = [(u.name, u.x, u.y) for _, u in g.units.items()] + [(f"{g.name} wp{i}", p.x, p.y) for i, p in g.route.points.items()]
                for nm, x, y in pts:
                    ll = mapping.Point(x, y, terrain).latlng(); n += 1
                    if not globe.is_land(ll.lat, ll.lng): bad.append((nm, round(ll.lat, 4), round(ll.lng, 4)))
    print(path, f"{n} ground points checked,", "ALL ON LAND" if not bad else f"IN SEA: {bad}")
