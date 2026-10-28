# Operation Narrow Gate

A short branching campaign for the F/A-18C on the Caucasus map, for one or two players. Every mission starts
cold on the deck of the John C. Stennis and ends with a trap. The outcome of each mission picks the next one.

You are a lieutenant (junior grade), your squadron's assistant operations officer. A Red mechanised brigade is
driving south down the Black Sea coast toward the Inguri bridges, and Narrow Gate, the dawn strike on its lead
battalion's fuel depot, is your plan. CAG has promised you more of the air wing if it works.

## Missions

| File | When you fly it | What it is |
|---|---|---|
| `Operation_Narrow_Gate.miz` | First | Dawn time-on-target strike on the depot, inside the window a transiting jamming package opens on the SA-6. Laser-guided bombs under JTAC control |
| `Operation_Long_Road.miz` | Narrow Gate succeeded on time | Interdiction of the brigade's stalled column before it reaches cover, with COLT (AI HARM pair) assigned to you |
| `Operation_Long_Road_Own_SEAD.miz` | The depot was destroyed, but late | The same interdiction without COLT: your section brings its own HARMs |
| `Operation_Stone_Ford.miz` | Narrow Gate partly worked | Close air support for the bridgehead at Ganmukhuri against a weakened battalion, ground JTAC (Type 1) |
| `Operation_Stone_Ford_Hard.miz` | Narrow Gate failed | The same fight against the full battalion, with MiG-29s early and the CAP held back for fleet defence |
| `Operation_Sandy_Lift.miz` | A jet went down over land in Narrow Gate | Rescue escort: clear the area, bring in the helicopter, keep it alive |
| `Operation_Sandy_Lift_Long_Road.miz` | A jet went down over land in Long Road | The same rescue, by the coast road |
| `Operation_Sandy_Lift_Inguri.miz` | A jet went down over land in Stone Ford | The same rescue, behind Red's line at the Inguri |

The mission summary at the end of each mission names the next file. It also sets flag 90 (1 success,
2 partial, 3 failure, 4 success but late in Narrow Gate) and flag 91 (a jet was lost), for anyone wiring this into
a DCS campaign file.

```
                         ┌─ success, on time ──── Long Road (COLT)
                         ├─ success, late ─────── Long Road (own SEAD)
Narrow Gate ─────────────┼─ partial ───────────── Stone Ford
                         └─ failure ───────────── Stone Ford (hard)

any mission, pilot ejects over land ──── the matching Sandy Lift
```

## What carries through the campaign

- **The story's assets are real aircraft.** FORD, the jamming package in Narrow Gate, is a pair of AI Hornets on a
  transit track: the SA-6 is jammed only while they are in range, and if they are shot down the jamming ends.
- **MAGIC runs the CAP.** CHEVY is committed against briefed criteria (a threat to the boat first, then threats to
  your package), resets to its station afterwards, and is relieved by the carrier's alert-5, UZI, if it runs out
  of missiles or fuel or loses a jet. You can only request cover.
- **CAG keeps score.** Success on time earns COLT; success but late doesn't. Failure keeps CHEVY on fleet defence.
- **Downed pilots matter.** An ejection over land leads to a rescue mission; over the water the Navy picks them up.
- **Random elements.** In Narrow Gate, the Gudauta dawn patrol is up on about one morning in five, and when it is,
  it is MiG-21s or MiG-29s at even odds.

## Building

From the repository root: `python build.py narrow_gate`. See the [main README](../../README.md).

| Source | What it builds |
|---|---|
| `build_narrow_gate.py`, `lua/narrow_gate.lua`, `mission_times.py` | Narrow Gate. All its timing comes from `mission_times.py` |
| `build_long_road.py`, `lua/long_road.lua` | Both Long Road variants |
| `build_stone_ford.py`, `lua/stone_ford.lua` | Both Stone Ford variants |
| `build_sandy_lift.py`, `lua/sandy_lift.lua` | All three Sandy Lift variants |
| `briefings/*.md`, `context.py` | Briefings |
| `maps_narrow_gate.py`, `maps_followon.py` | Maps |
| `tests/` | Scenario tests, run against the built `.miz` files |
