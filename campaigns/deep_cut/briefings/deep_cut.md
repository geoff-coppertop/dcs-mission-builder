<div class="kicker">Mission briefing · Enfield, Springfield and Dodge · standalone mission{% if hard %}, hard{% endif %}</div>

# Operation Deep Cut{% if hard %} (hard){% endif %}

F/A-18C strike and F-14B escort · 1–6 players · Caucasus · low-level gorge strike · cold start and recovery aboard CVN-74

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| TOT | **{{ tot }} local** / {{ tot_z }}Z | Target | Tunnel portal on the Enguri gorge floor, near Khaishi |
| Window | {{ win_on }}–{{ win_off }} (±{{ window }} s) | Attack | Breach the blast door, then a second bomb through it within {{ kill_window }} s |
| Radar floor | {{ floor_ft }} ft AGL from Jvari to {{ pop_nm }} nm out | Threats | Guns and MANPADS in the gorge; {{ sam_names | join(" and ") }} at the climb-out; fighters |
| Mother | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Support | HAMMER (TLAMs), DODGE escort, ARCO, MAGIC |

</div>

<!-- ingame -->
## Situation

Red has dug a hardened store into the wall of the upper Enguri gorge, near Khaishi, and is moving its long-range missiles into it. Once they are inside, nothing we carry can reach them. The only way in is the tunnel portal on the gorge floor: a blast door, and behind it a straight tunnel into the rock.

The gorge is the only approach. Red's radars on the ridges watch everything above the rim, and the high ground either side of the portal holds {{ sam_names | join(" and ") }} batteries, sitting quiet with their radars off until Red's air defence commander wakes them. Guns and MANPADS teams line the floor of the upper gorge. Two fighter alerts cover the area: {{ south_kind }} at Kutaisi to the south-east, and {{ north_kind }} north of the main range.

## Mission

Destroy the store by putting two laser-guided bombs into the tunnel portal: the first to bring the blast door down, the second through the open portal within **{{ kill_window }} seconds**, before Red closes the inner door. Then get every jet home.

## The run

Coast in at the Enguri mouth below {{ floor_ft }} ft, follow the river {{ coast_gate_nm }} nm to the gorge mouth at **Jvari (GATE)**, and fly up the gorge past the dam and along the reservoir, about {{ canyon_nm }} nm, to the portal. That is about {{ run_min }} minutes from the coast at 470 kt, and from the GATE on you are inside Red's radar coverage.

**The radar floor.** From the GATE until you are {{ pop_nm }} nm from the portal, any jet more than **{{ floor_ft }} ft above the ground** for {{ grace }} second{{ "s" if grace > 1 }} is seen. {% if warn %}MAGIC warns you the first time you go above it. {% endif %}If anyone is seen, Red knows the package is coming: the climb-out SAMs come up at once, the northern alert launches, and if HAMMER hasn't hit yet, so does Kutaisi. Inside {{ pop_nm }} nm of the portal you may climb for the attack: Red will know where you are when the first bomb lands anyway.

This applies to every Blue jet, escorts included. **DODGE stays west of the GATE until the first bomb lands.**

## Timing: HAMMER and the window

At **{{ hammer }}**, {{ hammer_lead }} minutes before TOT, HAMMER, a salvo of Tomahawks, cuts the runway at Kutaisi. Red needs about {{ repair_min }} minutes to open a strip, so the Kutaisi alert is airborne at about **{{ south_up }}** whatever you do. The window is built around that:

- **On time** ({{ win_on }}–{{ win_off }}): the breaching bomb lands while Kutaisi is cratered and before Red's air defence has worked out what HAMMER was for. The climb-out SAMs come up {{ react }} seconds after the first bomb lands on the portal. That is your time to get back down into the gorge.
- **Early** (before {{ win_on }}): if a bomb lands before HAMMER, Kutaisi's runway is still open and its alert launches straight away.
- **Late** (after {{ win_off }}): Red's air defence is fully alerted by HAMMER. The climb-out SAMs are up at **{{ sam_up }}** ({{ sam_up_s }} s after TOT) whether or not you have attacked, and every minute you spend in the gorge brings the Kutaisi fighters closer.

## The attack

The blast door is a small target: a bomb counts only if it lands within **{{ hit_r }} m** of it. The first bomb that does brings the door down. A second bomb (another bomb, not the same one) within {{ hit_r }} m of the portal inside {{ kill_window }} seconds goes through and destroys the store. After that the inner door closes and the store survives.

Each Hornet carries two GBU-12s and a LITENING pod, so one jet can do both, one bomb after the other or as a pair on the same laser spot. The plan: Enfield 1-1 breaches at TOT, Enfield 1-2 follows ten seconds behind to put the second bomb through, and Springfield arrives 30 seconds after TOT to finish anything that's left. Players shoot when they have the shot.

The TGT waypoint is the planned point. The mission places the portal on the actual gorge floor at mission start. The exact coordinates are sent at start and in **F10 > Deep Cut > Target coordinates**, and the F10 map draws the gorge floor from the GATE to the portal. Enter the coordinates as a waypoint or markpoint before you push.

## Getting out

After the attack the {{ sam_names | join(" and ") }} come up on the high ground around the portal, and their envelopes cover the climb out of the gorge. Get back on the floor and fly the gorge out the way you came, or use the HARMs on the radars before you climb. Expect {{ gun2 }} fire and MANPADS on the way down the gorge.

The Kutaisi alert launches at about {{ south_up }} (earlier if you are early or seen) and heads for the gorge mouth and the coast, which is your way home. DODGE, the F-14 escort, owns that fight. If no human is flying DODGE by {{ escort_check }}, MAGIC puts FORD, two AI Tomcats, on the escort station.

## Scoring

The summary after the last jet is down gives you a score out of 100.

<div class="keep" markdown="1">

| | Points | For |
|---|---|---|
| Target | {{ pts.breach }} | The blast door down |
| | {{ pts.kill }} | A second bomb through the portal within {{ kill_window }} s |
| Timing | {{ pts.ontime }} | The breaching bomb inside the window |
| | {{ pts.unseen }} | Nobody seen above the floor before the first bomb |
| Survival | {{ pts.survival }} | Shared by every player jet that launches; each one that lands (aboard, or a safe divert) keeps its share |

</div>

**TEXTBOOK** is 90 or more with the store destroyed. **SUCCESS** is 70 or more with the store destroyed. Anything else is **PARTIAL** at 45 or more, or **FAILURE**. A destroyed store that cost the package its jets is not a success.

## Players

Enfield 1-1 is flyable in single player; one Hornet can win this on its own. In multiplayer, Enfield and Springfield are two pairs of strike Hornets and Dodge is a pair of F-14Bs. All six start cold on the deck.
<!-- /ingame -->

<!-- task -->
<div class="keep" markdown="1">

## Key times

| Event | Local |
|---|---|
| Mission start, cold on the deck | {{ start }} |
| Escort check: FORD launches if no DODGE is airborne | {{ escort_check }} |
| HAMMER: TLAMs cut the Kutaisi runway | {{ hammer }} |
| Window opens | {{ win_on }} |
| **TOT: blast door** | **{{ tot }}** |
| Window closes | {{ win_off }} |
| Climb-out SAMs up if nothing has woken them | {{ sam_up }} |
| Kutaisi alert airborne (no earlier trigger) | {{ south_up }} |

</div>

<div class="keep" markdown="1">

## Comms and menus

| Callsign | Who | |
|---|---|---|
| ENFIELD, SPRINGFIELD | Strike Hornets, two pairs | 251.0 AM |
| DODGE | Escort F-14Bs (FORD if AI) | 251.0 AM |
| MAGIC | E-2C, calls the floor, the SAMs and the fighters | 255.0 AM |
| ARCO | S-3B tanker | 251.0 AM, TACAN 60Y |
| MOTHER | CVN-74 Stennis | 127.5, TACAN 74X, ICLS 11 |

F10 > Deep Cut: **Time check** (TOT, HAMMER, floor and SAM state), **Target coordinates** (the portal's exact position), **Mission summary now**.

</div>
<!-- /task -->

<div class="pagebreak"></div>

<div class="kicker">Map 1</div>

![Theater map](Operation_Deep_Cut{% if hard %}_Hard{% endif %}_theater.png){: .medium }

<p class="small">Coastline is approximate (about 1 km resolution). Courses are true. Red's sites are drawn at their planned points.</p>

<div class="pagebreak"></div>

<div class="kicker">Map 2</div>

![The gorge](Operation_Deep_Cut{% if hard %}_Hard{% endif %}_gorge.png){: .medium }

<p class="small">The checkpoints follow the river from Jvari and the dam; above the dam they are estimates. At mission start the script finds the real gorge floor within each dotted ring with DCS's own terrain and places the portal, guns and MANPADS there, and the SAMs on the highest ground in theirs. Fly the gorge you see, not the line.</p>

<div class="pagebreak"></div>

<div class="keep" markdown="1">

## Route card: Enfield and Springfield

| WP | Name | Coordinates | Altitude | Leg | Course | Time |
|---|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} | {{ r.time }} |
{% endfor %}

<p class="small">Springfield's TGT time is locked 30 seconds after Enfield's. The TGT coordinates are the planned point: use the exact ones the mission gives you. Planned target: MGRS {{ tgt_mgrs }}, {{ tgt_ddm }}.</p>

</div>

<div class="keep" markdown="1">

## Route card: Dodge

| WP | Name | Coordinates | Altitude | Leg | Course |
|---|---|---|---|---|---|
{% for r in escort_route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} |
{% endfor %}

</div>

<div class="keep" markdown="1">

## Loadouts

| Station | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| F/A-18C | {{ strike_load[:9] | join(" | ") }} | |
| F-14B | {{ escort_load | join(" | ") }} |

<p class="small">Laser code 1688 on every Hornet. Fuel full internal plus tanks. Chaff 60, flares 30: the gorge is MANPADS country.</p>

</div>

{% if hard %}
## Hard variant

The floor is {{ floor_ft }} ft with no warning and {{ grace }} second{{ "s" if grace > 1 }} of grace, the window is ±{{ window }} s, the door has to be hit within {{ hit_r }} m and the kill made within {{ kill_window }} s. The climb-out SAMs are {{ sam_names | join(" and ") }}, the gorge guns include a ZSU-23-4, Kutaisi reopens after {{ repair_min }} minutes, and the northern alert is {{ north_kind }}.
{% endif %}
