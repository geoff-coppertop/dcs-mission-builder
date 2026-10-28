"""Operation Narrow Gate campaign: build stages, called by build.py in order.

Missions and how they connect are described in README.md in this folder.
"""
import json
from pathlib import Path

from missionbuilder import briefing

# (mission file, briefing template, context function in context.py, footer title)
MISSIONS = [
    ("Operation_Narrow_Gate.miz", "narrow_gate.md", "narrow_gate", "Operation Narrow Gate"),
    ("Operation_Long_Road.miz", "long_road.md", "long_road", "Operation Long Road"),
    ("Operation_Long_Road_Own_SEAD.miz", "long_road.md", "long_road", "Operation Long Road (own SEAD)"),
    ("Operation_Stone_Ford.miz", "stone_ford.md", "stone_ford", "Operation Stone Ford"),
    ("Operation_Stone_Ford_Hard.miz", "stone_ford.md", "stone_ford", "Operation Stone Ford (hard)"),
    ("Operation_Sandy_Lift.miz", "sandy_lift.md", "sandy_lift", "Operation Sandy Lift"),
    ("Operation_Sandy_Lift_Long_Road.miz", "sandy_lift.md", "sandy_lift", "Operation Sandy Lift (Long Road)"),
    ("Operation_Sandy_Lift_Inguri.miz", "sandy_lift.md", "sandy_lift", "Operation Sandy Lift (Inguri)"),
]
FOLLOW_ONS = [m[0] for m in MISSIONS[1:]]


def missions(c):
    for s in ("build_narrow_gate.py", "build_long_road.py", "build_stone_ford.py", "build_sandy_lift.py"):
        c.run(s, quiet=True)
    for m in MISSIONS:
        assert (c.out / m[0]).exists(), m[0]
    print(f"   {len(MISSIONS)} missions in {c.out.relative_to(c.out.parents[1])}")


def maps(c):
    c.run(Path(__file__).resolve().parents[2] / "missionbuilder" / "geom.py", c.out / "Operation_Narrow_Gate.miz", quiet=True)
    c.run("maps_narrow_gate.py", quiet=True)
    c.run("maps_followon.py", *[c.out / f for f in FOLLOW_ONS], quiet=True)
    print(f"   maps in {c.work}")


def briefings(c):
    import context
    for miz, tpl, fn, title in MISSIONS:
        ctx = getattr(context, fn)(c.out / miz, c.work)
        md = briefing.render(c.dir / "briefings" / tpl, ctx)
        stem = Path(miz).stem
        (c.work / f"{stem}.md").write_text(md, encoding="utf-8")            # the filled-in Markdown, for review
        (c.work / f"{stem}.context.json").write_text(json.dumps(ctx, indent=1, default=str), encoding="utf-8")
        desc, task = briefing.ingame(md)
        briefing.inject(c.out / miz, desc, task)
        briefing.to_pdf(md, c.out / f"{stem}_Briefing.pdf", c.work, title, f"{title} · fictional training scenario · DCS World")
        print(f"   {stem}: in-game text {len(desc) + len(task):,} chars, PDF written")


def checks(c):
    log = c.run(Path(__file__).resolve().parents[2] / "missionbuilder" / "landcheck.py",
                *sorted(c.out.glob("*.miz")), quiet=True)
    bad = [l for l in log.splitlines() if "IN SEA" in l]
    if bad:
        raise SystemExit("ground units in the sea:\n" + "\n".join(bad))
    print(f"   all ground units on land ({len(log.splitlines())} missions)")


def tests(c):
    for lua in ("lua51", "lua55"):
        c.env["NG_LUA"] = lua
        runs = [("tests/test_narrow_gate.py", "Operation_Narrow_Gate.miz"),
                ("tests/test_long_road.py", "Operation_Long_Road.miz"),
                ("tests/test_long_road.py", "Operation_Long_Road_Own_SEAD.miz"),
                ("tests/test_stone_ford.py", "Operation_Stone_Ford.miz"),
                ("tests/test_stone_ford.py", "Operation_Stone_Ford_Hard.miz"),
                ("tests/test_sandy_lift.py", "Operation_Sandy_Lift.miz"),
                ("tests/test_sandy_lift.py", "Operation_Sandy_Lift_Long_Road.miz"),
                ("tests/test_sandy_lift.py", "Operation_Sandy_Lift_Inguri.miz")]
        for script, miz in runs:
            log = c.run(script, c.out / miz, quiet=True)
            print(f"   [{lua}] {miz}: {log.strip().splitlines()[-1]}")
