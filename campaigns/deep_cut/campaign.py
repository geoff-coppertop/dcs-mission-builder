"""Operation Deep Cut: build stages, called by build.py in order. See README.md in this folder."""
import json
from pathlib import Path

from missionbuilder import briefing

# (mission file, briefing template, context function in context.py, footer title)
MISSIONS = [
    ("Operation_Deep_Cut.miz", "deep_cut.md", "deep_cut", "Operation Deep Cut"),
    ("Operation_Deep_Cut_Hard.miz", "deep_cut.md", "deep_cut", "Operation Deep Cut (hard)"),
    ("Operation_Deep_Cut_Escape.miz", "escape.md", "escape", "Operation Deep Cut: Escape"),
]
TESTS = {"Operation_Deep_Cut_Escape.miz": "tests/test_escape.py"}
ROOT = Path(__file__).resolve().parents[2]


def missions(c):
    c.run("build_deep_cut.py", quiet=True)
    c.run("build_escape.py", quiet=True)
    for m in MISSIONS:
        assert (c.out / m[0]).exists(), m[0]
    print(f"   {len(MISSIONS)} missions in {c.out.relative_to(c.out.parents[1])}")


def maps(c):
    c.run("maps_deep_cut.py", *[c.out / m[0] for m in MISSIONS], quiet=True)
    print(f"   maps in {c.work}")


def briefings(c):
    import context
    for miz, tpl, fn, title in MISSIONS:
        ctx = getattr(context, fn)(c.out / miz, c.work)
        md = briefing.render(c.dir / "briefings" / tpl, ctx)
        stem = Path(miz).stem
        (c.work / f"{stem}.md").write_text(md, encoding="utf-8")
        (c.work / f"{stem}.context.json").write_text(json.dumps(ctx, indent=1, default=str), encoding="utf-8")
        desc, task = briefing.ingame(md)
        briefing.inject(c.out / miz, desc, task)
        briefing.to_pdf(md, c.out / f"{stem}_Briefing.pdf", c.work, title, f"{title} · fictional training scenario · DCS World")
        print(f"   {stem}: in-game text {len(desc) + len(task):,} chars, PDF written")


def checks(c):
    # Red ground is spawned by the script at mission start (placed on DCS terrain), so the .miz has none to check;
    # this still catches any ground unit added to the mission file later.
    log = c.run(ROOT / "missionbuilder" / "landcheck.py", *[c.out / m[0] for m in MISSIONS], quiet=True)
    bad = [l for l in log.splitlines() if "IN SEA" in l]
    if bad:
        raise SystemExit("ground units in the sea:\n" + "\n".join(bad))
    print(f"   all ground units on land ({len(log.splitlines())} missions)")


def tests(c):
    for lua in ("lua51", "lua55"):
        c.env["NG_LUA"] = lua
        for m in MISSIONS:
            log = c.run(TESTS.get(m[0], "tests/test_deep_cut.py"), c.out / m[0], quiet=True)
            print(f"   [{lua}] {m[0]}: {log.strip().splitlines()[-1]}")
