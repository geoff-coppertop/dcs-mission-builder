<div class="kicker">Mission briefing · Enfield flight · Narrow Gate campaign, mission 1</div>

# Operation Narrow Gate

F/A-18C Hornet · 1–2 players · Caucasus · dawn precision strike · cold start and recovery aboard CVN-74

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| TOT | **{{ tot }} local** / {{ tot_z }}Z | Target | Vehicles at a fuel depot, NE of Ochamchire |
| Impact window | {{ win_on }}–{{ win_off }} | Weapons | 4× GBU-12 on PONTIAC's laser, code 1688 |
| Jamming | {{ jam_on }}–{{ jam_off }} (planned) | Threats | SA-6, 2× ZSU-23-4, SA-13; MiG-21s if late |
| Mother | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Support | FORD, PONTIAC, ARCO, CHEVY, MAGIC |

</div>

<!-- ingame -->
## Situation

Three days ago a Red mechanised brigade started south down the Black Sea coast road. Its lead battalion has stopped for the night at a fuel depot on the coastal plain just north-east of Ochamchire, two hours' drive from the Inguri bridges that Blue's ground forces are still digging in to hold.

PONTIAC, an MQ-9 working for the Blue ground commander, watched the battalion's lead elements pull in last night: two T-72s and a string of Ural fuel and ammunition trucks, parked in the open. They are refuelling through the night and will form up to move at about 09:00. The depot is defended the way a fixed site should be. An SA-6 battery sits a kilometre to the north, there is a ZSU-23-4 beside the SAM and another on the south side, and an SA-13 covers the east.

## Mission

Destroy the vehicles at the depot at {{ tot }} local. Without that fuel and armour the lead battalion stalls short of the Inguri, and Blue gets the day it needs to finish the river defence.

You are a lieutenant (junior grade), the squadron's assistant operations officer, and this is your plan. You wrote it, you briefed it to CAG, and you are leading it: ENFIELD, a section of two Hornets with laser-guided bombs, off the John C. Stennis (CVN-74), 90 km offshore. CAG signed it off with a promise. Make it work and you get more of the air wing for the follow-up.

## Why dawn

The strike goes in just after sunrise, before the column forms up. The vehicles are still parked, the crews are still refuelling, and there is enough light to launch and recover in daylight. Sunrise is about 07:41, so at TOT the sun is only 3° up, low ahead and well right of the north-east run-in. Expect glare when you look for the target. It doesn't affect PONTIAC's laser or your pod's infrared picture, and on the way out the sun is behind you.

## The narrow gate

There is no SEAD to spare for this. What you have is FORD, a pair of jamming jets crossing the area on their way to another tasking up north. Their track passes about {{ ford_cpa_nm }} nm south-west of the SA-6, and while they are within about {{ jam_r_nm }} nm their jammers blind its radar, from roughly **{{ jam_on }} to {{ jam_off }}**. That is long enough for both of you to run in, release and get back out of SA-6 range, but only if you are on time. The SA-6 reaches above your 20,000 ft ingress, so FORD's pass is the only safe way in.

Your bombs must land within **±{{ window_s }} seconds of {{ tot }}**: the lead at TOT and the wingman 30 seconds later.

FORD is real traffic, and the jamming lasts exactly as long as FORD is in range. FORD won't wait for you and won't turn back. Each jet carries two AMRAAMs for self-defence. If they are attacked they fight their way through rather than chase, but their defensive turns can take them out of range, and the SA-6 comes up until they are back on track. If FORD is shot down, the jamming stops there.

- **Early** (impact before {{ win_on }}): scored EARLY. PONTIAC won't clear an IN before {{ in_earliest }}, and before {{ jam_on }} the SA-6 is awake and waiting for you.
- **On time** ({{ win_on }}–{{ win_off }}): the SA-6 is jammed for your whole run in and out. PONTIAC clears you hot and you are scored ON TIME.
- **Late** (nothing lands in the window): scored LATE. When FORD passes out of range the SA-6 comes back up, Red knows something is coming, and the MiG-21 alert pair at Gudauta launches toward the target area.

Jamming does nothing to the guns or the SA-13. The ZSUs reach about 1.3 nm and 8,000 ft, and the heat-seeking SA-13 about 2.7 nm and 16,000 ft. Neither reaches the planned 20,000 ft attack, but a low pass, a diving pass or a pop-up attack flies straight into them. Stay above 17,000 ft near the target.

## The Gudauta patrol

Gudauta, about 50 nm up the coast, flies an irregular dawn patrol offshore. Most mornings nothing is up; some mornings it is a pair of MiG-21s or MiG-29s. Intelligence can't tell you whether it will fly today, so MAGIC will tell you about two minutes after mission start. If it is up, expect Red's controllers to send it at FORD the moment the jammers come on, because a jammer is the first thing an air defender wants dead.

## CAP and the alert

CHEVY, a pair of Hornets, holds CAP between the boat and the coast. **MAGIC commits CHEVY, not you,** against the briefed criteria:

- the Gudauta patrol going for FORD: CHEVY screens FORD;
- the alert MiGs launching on a late run: CHEVY covers your egress;
- anything Red within about 22 nm of Mother: fleet defence, which overrides the others.

After each commit CHEVY resets to its station, now with fewer missiles and less fuel. If a second threat appears while CHEVY is busy, it waits its turn. You can ask MAGIC for cover over your egress from the F10 menu, and MAGIC agrees only if CHEVY is free.

If CHEVY is out of missiles, short of fuel, down to one jet or shot down, Mother launches her alert-5, **UZI**, two more Hornets, to take over the CAP. A single surviving CHEVY holds until UZI arrives. Expect about {{ alert_min }} minutes with reduced or no CAP while UZI launches and climbs out. There is only one alert section.

## The plan in one line

Cold start on the Stennis, launch, hold at PUSH to burn time, push for the IP, put GBU-12s on PONTIAC's laser inside the window, egress west over the water, top off from ARCO if you need it, and bring it back aboard.

<div class="keep" markdown="1">

## What happens next

This is the first mission of a short campaign. The summary after recovery names the next file to fly.

| Result | Needs | CAG's response, and the next mission |
|---|---|---|
| Success | 4 or more of the 5 vehicles destroyed, inside the window | "Good work." The follow-up is yours to plan and lead, and COLT, an AI pair of HARM Hornets, is yours with it. **Operation_Long_Road.miz** |
| Success, late | 4 or more destroyed, outside the window | The depot is gone and the battalion is stopped, but you were late, inside a live SA-6 with MiGs up. COLT goes to a package that hits its TOT. The follow-up is still yours, with your own SEAD. **Operation_Long_Road_Own_SEAD.miz** |
| Partial | 2 or 3 destroyed | "Not what you promised." Same assets, and the battalion is at the Inguri. **Operation_Stone_Ford.miz** |
| Failure | 0 or 1 destroyed | "I can't spare more." CHEVY stays on fleet defence and the full battalion is at the Inguri. **Operation_Stone_Ford_Hard.miz** |
| A jet lost | Any result | If the pilot ejected over land, CAG releases a rescue helicopter and your section: also fly **Operation_Sandy_Lift.miz**. A pilot who ejects over the water is picked up by the Navy. |

</div>

Secondary objective, **clean recovery**: every jet that launches traps aboard Mother with at least about 2,000 lb of fuel (18% internal), and nobody is lost.

1 or 2 players, cold start on the deck. Enfield 1-1 is flyable in single player; Enfield 1-2 joins in multiplayer.
<!-- /ingame -->

<div class="pagebreak"></div>

<div class="kicker">Map 1</div>

![Theater map](map_theater.png){: .medium }

<p class="small">Coastline is approximate (about 1 km resolution). Courses are true. MOTHER is the carrier's estimated position at {{ rec_hm }}. She steams west at 27 kt, so trust TACAN 74X over the waypoint.</p>

<div class="pagebreak"></div>

<div class="kicker">Map 2</div>

![Target area](map_target.png){: .short }

<div class="keep" markdown="1">

## Close air support brief

PONTIAC reads you this 9-line at check-in. The coordinates here are computed from the mission file; enter the ones PONTIAC gives you, which come from DCS itself.

| Line | Item | PONTIAC's 9-line |
|---|---|---|
| 1 | IP | IP (waypoint 3) |
| 2 | Heading and offset | {{ ip_hdg }}° true, offset left |
| 3 | Distance | {{ ip_dist }} nm |
| 4 | Target elevation | Given at check-in (coastal plain, near sea level) |
| 5 | Description | 5 vehicles in the open: 2× T-72B, 3× Ural-375 fuel and ammunition trucks |
| 6 | Location | MGRS {{ tgt_mgrs }}<br>{{ tgt_ddm }} |
| 7 | Mark | Laser, PONTIAC, code 1688 |
| 8 | Friendlies | Blue ground forces at the Inguri, about 20 nm south-east |
| 9 | Egress | Left, west to EGRESS (waypoint 5), {{ egress_hdg }}° true |
| | Remarks | SA-6 1 km north, jammed {{ jam_on }}–{{ jam_off }} only. Two ZSU-23-4s (north and south) and an SA-13 (east), never jammed. Impact window {{ win_on_hm }}–{{ win_off_hm }}. Final attack heading 030–080. Stay above 17,000 ft. |

Read back lines 4 and 6 and the restrictions before you call IN.

</div>

<div class="pagebreak"></div>

<div class="kicker">Timing</div>

![Timeline](timeline.png)

<!-- task -->
## Times and route

TOT **{{ tot }} local / {{ tot_z }}Z**, {{ tot_offset_min }} minutes after mission start. ON TIME means impact within ±{{ window_s }} s: lead at TOT, wingman at TOT +30 s. FORD's jamming is planned {{ jam_on }}–{{ jam_off }} but follows FORD's actual position. Earliest IN {{ in_earliest }}.

Cold start on the deck. Use fast (CV) alignment and allow about 15 minutes to the catapult.

| WP | Name | Coordinates | Alt | Leg | Course | Plan time |
|---|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} | {{ r.time }} |
{% endfor %}

<!-- pdf-only -->
<p class="small">Plan times assume 420 kt ground speed from PUSH. The TGT waypoint carries the TOT in the Mission Editor, but enter it yourself on the HSI DATA page. DCS forum users report that the Hornet's TOT cue works in Zulu: {{ tot_z }}Z.</p>
<!-- /pdf-only -->
<!-- /task -->

<div class="pagebreak"></div>

<div class="kicker">Kneeboard</div>

<!-- task -->
## Comms and navigation

| Callsign | Role | Frequency | Notes |
|---|---|---|---|
| MOTHER | CVN-74 John C. Stennis | 127.5 AM | TACAN 74X STN · ICLS 11 |
| ENFIELD 1-1, 1-2 | You | 251.0 AM | Flight frequency, shared with ARCO |
| ARCO | S-3B tanker, 15,000 ft on the egress track | 251.0 AM | TACAN 60Y |
| MAGIC | E-2C, controls CHEVY and UZI | 255.0 AM | |
| PONTIAC | MQ-9 over the target: passes the Blue ground commander's 9-line and clearances, and lases | F10 menu | Laser 1688 |
| FORD | 2× F/A-18C jamming package, transiting north at 25,000 ft | Text calls | Jamming {{ jam_on }}–{{ jam_off }} |
| CHEVY | 2× F/A-18C CAP, 20,000 ft | MAGIC commits | Station about 23 nm SW of EGRESS |
| UZI | 2× F/A-18C alert-5 on Mother | Via MAGIC | About {{ alert_min }} min to the CAP station |

## Loadout

Both jets: 4× GBU-12 (two BRU-33s), LITENING, 2× AIM-9X, 3× AIM-120C, centreline tank. The GBU-12s and the LITENING laser spot tracker default to code 1688; check the stores page before launch.

## F10 radio menu: Strike

| Item | What it does |
|---|---|
| Time check | Time, TOT and time remaining, jamming and impact windows, check-in, 9-line and readback status |
| Request CAP cover | Asks MAGIC for the CAP over EGRESS, about 3–4 minutes away. Approved only if the CAP is free |
| Pontiac (CAS) > 1. Check in | Your check-in; PONTIAC answers with the situation and game plan |
| Pontiac (CAS) > 2. Ready to copy 9-line | The 9-line with live coordinates and elevation, plus remarks |
| Pontiac (CAS) > 3. Read back | Lines 4 and 6 and restrictions. Required before any clearance |
| Pontiac (CAS) > Request mark | Red smoke 30 m north of the current target |
| Pontiac (CAS) > Enfield 1-x > IN | Sends your heading: CLEARED HOT, or ABORT with the reason |
| Pontiac (CAS) > Enfield 1-x > Ten seconds | PONTIAC turns the laser on |
| Pontiac (CAS) > Enfield 1-x > Spot | You confirm the spot |
| Pontiac (CAS) > Enfield 1-x > OFF | Off target; BDA once your weapons land |
| Pontiac (CAS) > Enfield 1-x > Terminate | Laser off |
| Mission summary now | Outcome on demand (automatic once every jet is down) |
<!-- /task -->

<div class="keep" markdown="1">

## CAS flow (Type 2, bomb on target)

| Step | You (F10) | PONTIAC |
|---|---|---|
| 1 | Check in | Situation update and game plan |
| 2 | Ready to copy 9-line | 9-line and remarks |
| 3 | Read back 4, 6 and restrictions | Readback correct |
| 4 | IN from the IP, heading 030–080, not before {{ in_earliest }} | CLEARED HOT, or ABORT ABORT ABORT with the reason |
| 5 | Ten seconds, then Spot | Laser on, code 1688, then "copy spot" |
| 6 | OFF | BDA once your weapons land (automatic if you forget) |
| 7 | Terminate when done | Laser off |

A clearance stays valid for 2 minutes. PONTIAC aborts an IN without a readback, outside the final attack heading, from more than 25 nm out, or before {{ in_earliest }}, when your bombs would land ahead of the window. Releases without a valid CLEARED HOT are flagged in your debrief.

</div>

PONTIAC lases when either jet calls Ten seconds. The spot stays on, moving to the next vehicle as each one dies, until someone calls Terminate or the last vehicle is destroyed. Your own LITENING on 1688 is the backup.

## Scoring, debrief and summary

Each pilot is scored on their first bomb to land within 2.5 km of the depot: EARLY, ON TIME or LATE, to the second. Air-to-air shots don't count. After you trap, you get a debrief with your grade, how you flew the CAS procedure, the vehicles left, and whether the window was used.

When every jet that launched has trapped or been lost, MAGIC posts the mission summary: vehicles destroyed, whether the window was met, the clean recovery, what happened to FORD, the Gudauta patrol and the CAP, the outcome, and the next mission to fly. Flag 90 is set to 1 for success, 2 partial, 3 failure and 4 success but late; flag 91 is set if a jet was lost.

## Recovery

Mother steams west at 27 kt into the wind, so she will be well west of where you launched. Use TACAN 74X and ICLS 11. ARCO's track is on the way home if you need fuel.
