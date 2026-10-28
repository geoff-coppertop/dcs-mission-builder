"""Pull positions and route data out of the built .miz into geom.json (lat/lon)."""
import json, math, sys, zipfile
import lupa
import dcs
from dcs import mapping

miz = sys.argv[1]
terrain = dcs.terrain.Caucasus()
L = lupa.LuaRuntime(unpack_returned_tuples=True)
with zipfile.ZipFile(miz) as z:
    L.execute(z.read("mission").decode("utf-8"))
    L.execute(z.read("l10n/DEFAULT/dictionary").decode("utf-8"))
mis = L.globals().mission
dic = L.globals().dictionary


def ll(x, y):
    p = mapping.Point(x, y, terrain).latlng()
    return [p.lat, p.lng]


out = {"groups": {}, "start_time": mis.start_time}
for side in ("blue", "red"):
    for _, c in mis.coalition[side].country.items():
        for cat in ("plane", "ship", "vehicle"):
            if not c[cat]:
                continue
            for _, g in c[cat].group.items():
                pts = g.route.points
                route = []
                for i in range(1, len(pts) + 1):
                    p = pts[i]
                    route.append({"name": p.name or "", "type": p.type, "ll": ll(p.x, p.y),
                                  "x": p.x, "y": p.y, "alt": p.alt, "speed": p.speed})
                units = [{"name": u.name, "type": u.type, "ll": ll(u.x, u.y), "x": u.x, "y": u.y}
                         for _, u in g.units.items()]
                out["groups"][g.name] = {"side": side, "cat": cat, "route": route, "units": units,
                                         "late": bool(g.lateActivation),
                                         "freq": g.frequency}
zones = mis.triggers.zones
for i in range(1, len(zones) + 1):
    if zones[i].name == "BRIDGE":
        out["bridge"] = ll(zones[i].x, zones[i].y)
        out["bridge_r"] = zones[i].radius
out["briefing"] = {"situation": dic[mis.descriptionText], "task": dic[mis.descriptionBlueTask]}
json.dump(out, open("geom.json", "w"), indent=1)
e = out["groups"]["Enfield"]["route"]
for w in e:
    print(w["name"] or w["type"], [round(v, 4) for v in w["ll"]], round(w["alt"] / 0.3048), "ft")
print("groups:", list(out["groups"]))
