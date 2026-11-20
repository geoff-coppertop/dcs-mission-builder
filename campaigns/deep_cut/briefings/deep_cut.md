<div class="kicker">Mission briefing · Enfield · Deep Cut, mission 1{% if hard %}, hard{% endif %}</div>

# Operation Deep Cut{% if hard %} (hard){% endif %}

F/A-18C · 1–2 players · Caucasus · low-level gorge strike · cold start and recovery aboard {{ carrier_short }}{% if supercarrier %} (Supercarrier){% endif %}

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| TOT | **{{ tot }} local** / {{ tot_z }}Z | Target | Tunnel portal on the Enguri gorge floor, near Khaishi |
| Window | {{ win_on }}–{{ win_off }} (±{{ window }} s) | Attack | Breach the blast door, then a second bomb through it within {{ kill_window }} s |
| Radar floor | {{ floor_ft }} ft AGL from Jvari to {{ pop_nm }} nm out | Threats | Guns and MANPADS in the gorge; {{ sam_names | join(" and ") }} at the climb-out; fighters |
| Mother | {{ carrier_short }} · 127.5 · TACAN 74X · ICLS 11 | Support | HAMMER (TLAMs), HATCHET (laser), CHEVY (CAP), ARCO, MAGIC |

</div>

<!-- ingame -->
## Situation

Red has dug a hardened store into the wall of the upper Enguri gorge, near Khaishi, and is moving its long-range missiles into it over the next day. Once they are inside, nothing we carry can reach them. The only way in is the tunnel portal on the gorge floor: a blast door, and behind it a straight tunnel into the rock.

**Why not Tomahawks.** The portal faces down a near-vertical wall into a gorge that bends twice below it; a cruise missile can't make the last turn and dive without hitting the rock. The door also needs two bombs seconds apart, the second guided only after someone has seen the first land. That takes aircrew and a laser.

The gorge is the only approach. Red's radars on the ridges watch everything above the rim, and the high ground either side of the portal holds {{ sam_names | join(" and ") }} batteries, sitting quiet with their radars off until Red's air defence commander wakes them. Guns and MANPADS teams line the floor of the upper gorge. Two fighter alerts cover the area: {{ south_kind }} at Kutaisi to the south-east, and {{ north_kind }} north of the main range.

## Mission

Destroy the store by putting two laser-guided bombs into the tunnel portal: the first to bring the blast door down, the second through the open portal within **{{ kill_window }} seconds**, before Red closes the inner door. Then get every jet home.

## The run

Coast in at the Enguri mouth below {{ floor_ft }} ft, follow the river {{ coast_gate_nm }} nm to the gorge mouth at **Jvari (GATE)**, and fly up the gorge past the dam and along the reservoir, about {{ canyon_nm }} nm, to the portal. That is about {{ run_min }} minutes from the coast at 470 kt, and from the GATE on you are inside Red's radar coverage.

**The radar floor.** From the GATE until you are {{ pop_nm }} nm from the portal, any jet more than **{{ floor_ft }} ft above the ground** for {{ grace }} second{{ "s" if grace > 1 }} is seen. {% if warn %}MAGIC warns you the first time you go above it. {% endif %}If anyone is seen, Red knows the package is coming: the climb-out SAMs come up at once, the northern alert launches, and if HAMMER hasn't hit yet, so does Kutaisi. Inside {{ pop_nm }} nm of the portal you may climb for the attack: Red will know where you are when the first bomb lands anyway.

This applies to every Blue jet in the package.

## Timing: HAMMER and the window

At **{{ hammer }}**, {{ hammer_lead }} minutes before TOT, HAMMER, a salvo of Tomahawks, destroys the sector air defence command post and the radar that controls Kutaisi's fighters. Fixed targets like those are what Tomahawks are for. Kutaisi won't launch its alert without control, and the backup takes about {{ repair_min }} minutes to come up, so the Kutaisi alert is airborne at about **{{ south_up }}** whatever you do. The window is built around that:

- **On time** ({{ win_on }}–{{ win_off }}): the breaching bomb lands while Kutaisi has no fighter control and before Red's air defence has worked out what HAMMER was for. The climb-out SAMs come up {{ react }} seconds after the first bomb lands on the portal. That is your time to get back down into the gorge.
- **Early** (before {{ win_on }}): if a bomb lands before HAMMER, Kutaisi's fighter control is still working and its alert launches straight away.
- **Late** (after {{ win_off }}): Red's air defence is fully alerted by HAMMER. The climb-out SAMs are up at **{{ sam_up }}** ({{ sam_up_s }} s after TOT) whether or not you have attacked, and every minute you spend in the gorge brings the Kutaisi fighters closer.

## Getting there on time

**Hold at PUSH** (waypoint {{ push_wp }}), over the water short of the coast: a left-hand racetrack with {{ hold_leg }} nm legs, the inbound leg on **{{ hold_course }}°** ending at PUSH. That's the course to FEET DRY, so the push is straight ahead. **{{ hold_ft }} ft.** Be established by {{ hold_by }}, and time your last lap to cross PUSH inbound on the call.

MAGIC calls the push. You'll hear "five minutes to push" with the hold, then "one minute to push", then **PUSH PUSH** at **{{ push }}**. Leave PUSH (waypoint {{ push_wp }}) on the call and fly the planned speeds on the route card; it gives the planned time at every waypoint to the target.

To let the jet do the sums, set the Hornet's TOT function: on the HSI DATA page, on the waypoint sequence (SEQUFC) page, enter TOT **{{ tot_z }}** Zulu (local time minus 4 hours on this map) and set TGT to **waypoint {{ tgt_wp }}**. Leave the ground speed entry blank. The HSI then shows the ground speed you need to make the TOT. Fly that, and step through the waypoints in order: set the HSI to auto-sequence, or step it by hand at each one. radio menu > F10. Other > Deep Cut > Time check gives the push time, the TOT and how long is left.

## The attack

The blast door is a small target: a bomb counts only if it lands within **{{ hit_r }} m** of it. The first bomb that does brings the door down. A second bomb (another bomb, not the same one) within {{ hit_r }} m of the portal inside {{ kill_window }} seconds goes through and destroys the store. After that the inner door closes and the store survives.

Each Hornet carries two GBU-12s and a LITENING pod, so one jet can do both: release both bombs in one pass, on the same laser spot, a fraction of a second apart. The plan for the two-ship, both on the same line up the gorge:

- **Enfield 1-1** breaches at TOT.
- **Enfield 1-2** puts the second bomb through 30 seconds later. Any closer and it flies through its lead's fragments and debris at 300 ft.

Players shoot when they have the shot.

**HATCHET**, a special forces team, is dug in on the ridge {{ team_km }} km from the portal, on the highest ground there that can see the blast door. On your call (**radio menu > F10. Other > Deep Cut > Hatchet: laser on the door**) they lase it on code 1688 until you call terminate or the store is destroyed. With HATCHET lasing, you can fly the pop-up and drop without working the pod; flying alone, that's the easier way to do it. Self-lasing works too.

The TGT waypoint is the planned point. The mission places the portal on the actual gorge floor at mission start. The exact coordinates are sent at start and in **radio menu > F10. Other > Deep Cut > Target coordinates**, and the F10 map draws the gorge floor from the GATE to the portal. Enter the coordinates as a waypoint or markpoint before you push.

## Getting out

After the attack the {{ sam_names | join(" and ") }} come up on the high ground around the portal, and their envelopes cover the climb out of the gorge. Get back on the floor and fly the gorge out the way you came, or use the HARMs on the radars before you climb. Expect {{ gun2 }} fire and MANPADS on the way down the gorge.

The Kutaisi alert launches at about {{ south_up }} (earlier if you are early or seen) and heads for the gorge mouth and the coast, which is your way home. CHEVY, two Hornets on CAP over the water off the Enguri mouth, is committed by MAGIC as soon as Red fighters launch. Each strike Hornet has two AIM-9Xs and an AMRAAM for the fight CHEVY doesn't reach. The quicker you are out of the gorge, the less of that fight there is.

**A pilot down.** A pilot who ejects over land is hidden by HATCHET overnight. The summary then tells you to fly **Operation_Deep_Cut_Escape.miz** to bring them home. A pilot who ejects over the water is picked up by the Navy.

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

Every slot is a client slot: in single player pick one (Enfield 1-1 is the lead), and one Hornet can win this on its own. In multiplayer, Enfield is a pair of strike Hornets. Both start cold on the deck.{% if supercarrier %} This version uses the Supercarrier ({{ carrier }}): everyone flying needs the Supercarrier module to start on the deck or catch a wire. Without it, fly the Stennis version, {{ miz | replace("_SC", "") }}.{% endif %}
<!-- /ingame -->

<!-- task -->
<div class="keep" markdown="1">

## Key times

| Event | Local |
|---|---|
| Mission start, cold on the deck | {{ start }} |
| Established in the hold at PUSH ({{ hold_ft }} ft) | {{ hold_by }} |
| **Push** | **{{ push }}** |
| HAMMER: TLAMs hit Red's air defence command post and fighter control | {{ hammer }} |
| Window opens | {{ win_on }} |
| **TOT: blast door** ({{ tot_z }}Z) | **{{ tot }}** |
| Window closes | {{ win_off }} |
| Climb-out SAMs up if nothing has woken them | {{ sam_up }} |
| Kutaisi alert airborne on the backup control (no earlier trigger) | {{ south_up }} |

</div>

<div class="keep" markdown="1">

## Comms and menus

| Callsign | Who | |
|---|---|---|
| ENFIELD | Strike Hornets, a pair | 251.0 AM |
| HATCHET | Special forces team on the ridge, lases the door on your radio call | Radio menu, F10. Other |
| CHEVY | Hornet CAP over the water, committed by MAGIC | 251.0 AM |
| MAGIC | E-2C, calls the floor, the SAMs and the fighters | 255.0 AM |
| ARCO | S-3B tanker | 251.0 AM, TACAN 60Y |
| MOTHER | {{ carrier }} | 127.5, TACAN 74X, ICLS 11 |

radio menu > F10. Other > Deep Cut: **Time check** (TOT, HAMMER, floor and SAM state), **Target coordinates** (the portal's exact position), **Hatchet: laser on the door**, **Hatchet: terminate**, **Mission summary now**.

The mission's commands are in the radio menu, under **F10. Other** (not the F10 map key). In flight, open the radio menu with the Hornet's COMM switch: **COMM 1** (default Right Alt + backslash) or **COMM 2** (Right Ctrl + backslash). The generic backslash key only opens it on the deck.

</div>
<!-- /task -->

<div class="pagebreak"></div>

<div class="kicker">Map 1</div>

![Theater map]({{ stem }}_theater.png){: .medium }

<p class="small">Coastline is approximate (about 1 km resolution). Courses are true. Red's sites are drawn at their planned points.</p>

<div class="pagebreak"></div>

<div class="kicker">Map 2</div>

![The gorge]({{ stem }}_gorge.png){: .medium }

<p class="small">The checkpoints follow the river from Jvari and the dam; above the dam they are estimates. At mission start the script finds the real gorge floor within each dotted ring with DCS's own terrain and places the portal, guns and MANPADS there, and the SAMs on the highest ground in theirs. Fly the gorge you see, not the line.</p>

<div class="pagebreak"></div>

<div class="keep" markdown="1">

## Route card: Enfield

| WP | Name | Coordinates | Altitude | Leg | Course | Time |
|---|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} | {{ r.time }} |
{% endfor %}

<p class="small">Times are the lead's; Enfield 1-2 is 30 seconds behind. The TGT coordinates are the planned point: use the exact ones the mission gives you. Planned target: MGRS {{ tgt_mgrs }}, {{ tgt_ddm }}.</p>

</div>

<div class="keep" markdown="1">

## Loadouts

| Station | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| F/A-18C | {{ strike_load[:9] | join(" | ") }} |

<p class="small">Laser code 1688 on every Hornet. Fuel full internal plus tanks. Chaff 60, flares 30: the gorge is MANPADS country.</p>

</div>

{% if hard %}
## Hard variant

The floor is {{ floor_ft }} ft with no warning and {{ grace }} second{{ "s" if grace > 1 }} of grace, the window is ±{{ window }} s, the door has to be hit within {{ hit_r }} m and the kill made within {{ kill_window }} s. The climb-out SAMs are {{ sam_names | join(" and ") }}, the gorge guns include a ZSU-23-4, Kutaisi's backup fighter control is up after {{ repair_min }} minutes, and the northern alert is {{ north_kind }}.
{% endif %}
