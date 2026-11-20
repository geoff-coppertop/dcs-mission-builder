"""Build Terrain_Survey_Caucasus.miz: run it once in DCS, then parse dcs.log with parse_survey.py."""
import datetime
import pathlib
import sys

import dcs
from dcs.action import DoScript
from dcs.planes import FA_18C_hornet
from dcs.triggers import TriggerStart
from dcs.unit import Skill

HERE = pathlib.Path(__file__).parent
OUT = HERE.parents[1] / "dist" / "tools" / "Terrain_Survey_Caucasus.miz"


def main():
    m = dcs.Mission(dcs.terrain.Caucasus())
    m.start_time = datetime.datetime(2026, 6, 1, 10, 0)
    usa = m.country("USA")
    m.terrain.airports["Senaki-Kolkhi"].set_blue()
    fg = m.flight_group_from_airport(usa, "Survey", FA_18C_hornet, m.terrain.airports["Senaki-Kolkhi"],
                                     start_type=dcs.mission.StartType.Warm, group_size=1)
    fg.units[0].skill = Skill.Client
    trig = TriggerStart(comment="terrain survey")
    trig.add_action(DoScript(m.string((HERE / "survey.lua").read_text())))
    m.triggerrules.triggers.append(trig)
    m.set_sortie_text("Terrain survey")
    m.set_description_text("Samples terrain heights around the Enguri gorge and writes them to dcs.log. "
                           "Fly nothing: take the slot, wait for 'Terrain survey done', then quit.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT))
    print("saved", OUT)


if __name__ == "__main__":
    sys.exit(main())
