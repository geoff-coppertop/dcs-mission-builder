#!/usr/bin/env python3
"""Build campaigns: missions (.miz), maps, briefings (PDF + in-game text), checks and tests.

    python build.py                      every campaign under campaigns/
    python build.py narrow_gate          one campaign
    python build.py narrow_gate --no-tests
    python build.py narrow_gate --only briefings     re-render briefings from the existing .miz files

Outputs go to dist/<campaign>/ (committed); intermediates to build/<campaign>/ (ignored).
"""
import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ("missions", "maps", "briefings", "checks", "tests")


class Campaign:
    def __init__(self, name):
        self.name = name
        self.dir = ROOT / "campaigns" / name
        self.out = ROOT / "dist" / name
        self.work = ROOT / "build" / name
        self.out.mkdir(parents=True, exist_ok=True)
        self.work.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ, MB_CAMPAIGN_DIR=str(self.dir), MB_OUT_DIR=str(self.out), MB_WORK_DIR=str(self.work),
                        PYTHONPATH=os.pathsep.join([str(ROOT), str(self.dir), os.environ.get("PYTHONPATH", "")]))

    def run(self, script, *args, quiet=False):
        """Run a Python script from the campaign folder with the work dir as cwd. Raises on failure."""
        script = self.dir / script if not Path(script).is_absolute() else Path(script)
        r = subprocess.run([sys.executable, str(script), *map(str, args)], cwd=self.work, env=self.env,
                           capture_output=True, text=True)
        noise = ("Cannot read registry keys", "Couldn't detect any installed DCS World")
        log = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if not l.startswith(noise))
        if r.returncode != 0:
            print(log)
            raise SystemExit(f"FAILED: {script.name} {' '.join(map(str, args))}")
        if not quiet and log.strip():
            print("   " + log.strip().replace("\n", "\n   "))
        return log


def load_campaign_module(c):
    spec = importlib.util.spec_from_file_location(f"campaign_{c.name}", c.dir / "campaign.py")
    mod = importlib.util.module_from_spec(spec)
    os.environ.update({k: v for k, v in c.env.items() if k.startswith("MB_")})
    sys.path[:0] = [str(ROOT), str(c.dir)]
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("campaigns", nargs="*", help="campaign folder names (default: all)")
    ap.add_argument("--no-tests", action="store_true", help="skip the scripted mission tests")
    ap.add_argument("--only", choices=STAGES, action="append", help="run only these stages (repeatable)")
    a = ap.parse_args()
    names = a.campaigns or sorted(p.name for p in (ROOT / "campaigns").iterdir() if (p / "campaign.py").exists())
    stages = a.only or [s for s in STAGES if not (s == "tests" and a.no_tests)]
    for name in names:
        c = Campaign(name)
        mod = load_campaign_module(c)
        print(f"== {name}")
        for st in stages:
            print(f"-- {st}")
            getattr(mod, st)(c)
    print("done")


if __name__ == "__main__":
    main()
