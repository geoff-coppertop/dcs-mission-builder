# Operation Deep Cut

A low-level strike on the Caucasus map for up to four players, two pairs of F/A-18C strike Hornets cold on the
deck of the John C. Stennis, with a follow-up if a pilot goes down over land. One Hornet can fly it alone: HATCHET,
a special forces team on the ridge, lases the target on call so a solo pilot only has to fly and drop.

Red has dug a hardened missile store into the wall of the upper Enguri gorge near Khaishi. The only way in is the
tunnel portal on the gorge floor. The strike coasts in at the Enguri mouth, follows the river to Jvari and flies up
the gorge under a radar floor. The first laser-guided bomb has to bring down the portal's blast door, and a second
has to go through it before Red closes the inner door. Then everyone has to get out past SAMs that wake up
behind them and fighters heading for the gorge mouth.

## Missions

| File | What it is |
|---|---|
| `Operation_Deep_Cut.miz` | Standard: 500 ft floor with a warning, ±45 s window, 90 s to make the kill, SA-6 and SA-8 at the climb-out, MiG-29s and MiG-21s |
| `Operation_Deep_Cut_Hard.miz` | Hard: 300 ft floor, no warning, ±30 s window, 60 s for the kill, SA-11 and SA-15/SA-8, a ZSU-23-4 in the gorge, MiG-29s and Su-27s, Kutaisi back up sooner |
| `Operation_Deep_Cut_Escape.miz` | Follow-up, flown when a pilot ejects over land in either variant: steal Red's F-14A (an F-14A-135-GR in ex-export paint), readied for a ferry flight: full fuel and tanks, gun only, start cart hooked up. The base is on alert after the raid (guards at +9 min, enough for a stored-heading INS start and the taxi; if they come before you're airborne, infantry spawn and a late-activated BRDM-2 drives at the jet; still parked, you're captured, already taxiing, you get 60 s to be airborne; MiG-29s about 6 min after you're seen: the report relayed through the sector, then a cockpit-readiness scramble). The pilot is the air wing commander, who flew F-14Ds before the type retired in 2006. Outrun the MiGs to the coast, where CHEVY holds CAP. 1 player, or 2 with a RIO. Check in with MAGIC (code word KESTREL). Silent, you're an unknown: in the ID zone (80 nm from Mother) CHEVY intercepts you ahead of the MiGs (`cap.lua` kind `ident`); Mother warns at 20 nm and the fleet shoots inside 10 nm unless you authenticate before the missiles arrive |

## What drives it

- **Radar floor.** From the gorge mouth to 3.8 nm from the portal, any player jet more than the floor height above
  the ground for a few seconds is seen: the climb-out SAMs come up, the northern alert launches, and before HAMMER the
  Kutaisi alert does too. Escorts count, so they hold west of the gorge until the first bomb.
- **Timing.** HAMMER, a scripted TLAM strike, destroys the sector air defence command post and Kutaisi's
  fighter-control radar three minutes before TOT; Kutaisi's alert waits for the backup (10 minutes, 7 hard). Bombs
  before HAMMER launch it at once; a late breach finds the SAMs already up. The briefing explains why this is a
  manned strike rather than a Tomahawk one.
- **Breach, then kill.** The first bomb within 15 m (12 m hard) of the blast door breaches it. A different bomb within
  the same distance inside the kill window destroys the store. One bomb can't do both.
- **Survival is scored.** The summary scores 100 points: 40 target, 20 timing (on time, unseen), 40 shared across every
  player jet that launches and lands (aboard or a divert). The store must be destroyed for SUCCESS or TEXTBOOK.
- **HATCHET.** Spawned at start on the highest ground 1.2–3 km from the portal that has line of sight to it, hidden and
  immortal. F10 > Deep Cut > Hatchet: laser on the door (code 1688); off on terminate or when the store is destroyed.
- **Egress cover.** CHEVY, an AI Hornet CAP over the water (`lua/cap.lua`), is committed when Red fighters launch.
  The strike Hornets carry two AIM-9X and an AMRAAM each. Enfield 1-2 trails its lead by 30 s to stay out of the
  fragments; Springfield attacks 45 s after TOT off a different heading.
- **A pilot down over land** is sent to `Operation_Deep_Cut_Escape.miz` in the summary; over the water, the Navy picks them up.

Flags at the end: 90 = 1 textbook, 2 success, 3 partial, 4 failure; 91 = a pilot is down over land; 92 = the score.
Escape sets 90 = 1 home, 2 down over the water, 3 down over land.

## The carrier

Mother starts about 75 nm off the coast in Deep Cut (85 nm in Escape) and steams west, so it is around 100 nm out
by recovery, a stand-off from Red's coastal anti-ship missiles. Plan on ARCO.

## Placement on DCS terrain

pydcs has no terrain elevation, and the gorge above the Enguri dam is only known here to a kilometre or two. So the
target and all Red ground sites are not in the `.miz`: the mission script spawns them at start, using DCS's own
`land.getHeight` to find the gorge floor nearest each planned point (guns, MANPADS, the portal) or the highest ground
(the climb-out SAMs), and avoids water. It marks the floor it found on the F10 map from Jvari to the portal and
sends the portal's exact coordinates, because the TGT waypoint is only the planned point. The radar floor is measured
above the real terrain under each jet.

Jvari and the dam use published coordinates. Everything above the dam is estimated, so check it in the Mission
Editor or on the F10 map before you rely on the waypoints.

## Building

From the repository root: `python build.py deep_cut`. See the [main README](../../README.md).

| Source | What it builds |
|---|---|
| `build_deep_cut.py`, `lua/deep_cut.lua` | Both strike variants (uses the shared `lua/common.lua`) |
| `build_escape.py`, `lua/escape.lua` | The escape follow-up (uses `lua/common.lua` and `lua/cap.lua`) |
| `briefings/*.md`, `context.py` | Briefings |
| `maps_deep_cut.py` | Theater, gorge and escape maps |
| `tests/` | Scenario tests against the built `.miz` files, including placement on a synthetic gorge |
