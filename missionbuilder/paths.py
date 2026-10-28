"""Where things live. build.py sets the MB_* environment variables for each campaign it builds.

  MB_CAMPAIGN_DIR  campaigns/<name>          sources: build scripts, lua/, briefings/
  MB_OUT_DIR       dist/<name>               what players get: .miz and briefing PDFs (committed)
  MB_WORK_DIR      build/<name>              intermediates: maps, built scripts, contexts (not committed)
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LUA_DIR = ROOT / "lua"


def _dir(var, default):
    p = Path(os.environ.get(var) or default).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def campaign_dir():
    return _dir("MB_CAMPAIGN_DIR", Path.cwd())


def out_dir():
    return _dir("MB_OUT_DIR", campaign_dir() / "out")


def work_dir():
    return _dir("MB_WORK_DIR", campaign_dir() / "work")


def read_lua(name):
    """A Lua script by file name: the campaign's lua/ folder first, then the shared lua/ library."""
    for d in (campaign_dir() / "lua", LUA_DIR):
        if (d / name).exists():
            return (d / name).read_text(encoding="utf-8")
    raise FileNotFoundError(name)
