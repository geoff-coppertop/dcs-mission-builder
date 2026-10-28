<div class="kicker">Mission briefing · Enfield flight · Narrow Gate campaign, {% if colt %}success branch{% else %}success branch (late){% endif %}</div>

# Operation Long Road{% if not colt %} (own SEAD){% endif %}

F/A-18C Hornet · 1–2 players · Caucasus · midday interdiction, SEAD leads · cold start and recovery aboard CVN-74

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| Column moves | **{{ restart_hms }} local** / {{ restart_z }}Z | Target | Stalled column, 10 vehicles, coast road |
| SEAD | {% if colt %}COLT on your call{% else %}Your own HARMs{% endif %} · a HARM hit = {{ suppress_s }} s window | Weapons | HARM, GBU-12, Mk-20 Rockeye |
| Control | PONTIAC (MQ-9), Type 3 | Threats | SA-6, SA-8, 2× ZSU-23-4, MiG-29s |
| Mother | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Support | {% if colt %}COLT (yours), {% endif %}PONTIAC, ARCO, CHEVY, MAGIC |

</div>

<!-- ingame -->
## Situation

{% if colt %}
Narrow Gate worked, and CAG kept his word. You planned it, and now you plan and lead the follow-up, with COLT, a pair of HARM-armed Hornets, assigned to your package.
{% else %}
The depot is gone and CAG gives you that much. But your bombs landed outside the window, with the section inside a live SA-6 and MiGs in the air, and that is not the plan he signed. COLT has gone to a package that hits its TOT. You still plan and lead the follow-up, and your section brings its own SEAD.
{% endif %}

The lead battalion's tanks, fuel and ammunition are burning at the Ochamchire depot, and the brigade's main body is stuck behind it on the coast road, nose to tail, waiting for fuel that isn't coming. PONTIAC is watching the column: two T-72s, three BMP-2s, three fuel trucks and two ammunition trucks, with an SA-8 and two ZSU-23-4s riding along. The brigade has set up its own SA-6 battery {{ sa6_nm }} nm {{ sa6_dir }} of the column to cover it.

They won't wait forever. At about **{{ restart }}** the brigade gives up on the fuel and turns inland for the wooded hills {{ cover_nm }} nm away. Anything that reaches the trees is gone.

## Mission

Destroy the column on the coast road before it reaches cover.

## SEAD leads

The SA-6 covers the column, and PONTIAC won't clear an attack on the column while the SA-6 can shoot. Each HARM that hits the Straight Flush radar puts it off the air for {{ suppress_s }} seconds, and that is your window to get bombs on the column. Kill the radar outright, with a HARM or a GBU-12 on PONTIAC's laser, and the SA-6 is finished for good.

{% if colt %}
COLT holds over the water, outside SA-6 reach, until you push it from the F10 menu. From its hold it is about 3 minutes to its HARM shots, so time the push to arrive as the HARMs land. Enfield 1-1 carries two backup HARMs. Enfield 1-2 carries cluster bombs for the column.
{% else %}
Nobody leads you in this time. Both jets carry two HARMs, two GBU-12s and two Rockeye. One jet shoots while the other uses the window to bomb the column. With only {{ harms }} HARMs in the section, killing the radar outright is the surer plan.
{% endif %}

Rockeye needs a lower release than the GBU-12s, and below about 10,000 ft you are inside the reach of the ZSUs and the SA-8.

## Threats

- **SA-6** (Straight Flush and four launchers) reaches above 20,000 ft.
- **SA-8** with the column reaches about 5.5 nm in DCS. It is radar guided, so HARMs work on it too.
- **Two ZSU-23-4s** ride in the column.
- **Two MiG-29s** launch from Gudauta at about {{ mig }}. MAGIC will commit CHEVY when they do, and you can ask for cover over the column from the F10 menu. If CHEVY is out of missiles, short of fuel, down to one jet or lost, Mother launches her alert-5, UZI, two more Hornets: about 12 minutes to station, and only one section.

<div class="keep" markdown="1">

## What happens next

This is the last mission on this branch of the campaign.

| Result | Needs | What it means |
|---|---|---|
| Success | 7 or more of the 10 vehicles destroyed | The brigade's main body is wrecked on the coast road. The advance on the Inguri is over |
| Partial | 4 to 6 destroyed | The survivors reach the hills. The advance is delayed, not stopped |
| Failure | 3 or fewer | Most of the column reaches cover, and the brigade will try again |
| Bonus | SA-6 radar destroyed | Reported in the summary |
| A jet lost | Any result | If the pilot ejected over land, also fly **Operation_Sandy_Lift_Long_Road.miz** |

</div>

Secondary objective, **clean recovery**: every jet that launches traps aboard Mother with at least about 2,000 lb of fuel, and nobody is lost.

1 or 2 players, cold start on the deck. Enfield 1-1 is flyable in single player.
<!-- /ingame -->

<div class="keep" markdown="1">

## Key times

| Event | Local |
|---|---|
| Mission start, cold on the deck | {{ start }} |
| Red MiG-29 pair launches | {{ mig }} |
| PONTIAC: column crews mounting up | {{ mounting }} |
| Column moves for the hills | **{{ restart }}** |
| Last vehicle in cover, if untouched (estimate) | {{ last_cover }} |

</div>

<div class="keep" markdown="1">

<div class="kicker">Map 1</div>

![Theater map](Operation_Long_Road{% if not colt %}_Own_SEAD{% endif %}_theater.png){: .medium }

<p class="small">Coastline is approximate (about 1 km resolution). Courses are true. MOTHER is the carrier's estimated position at recovery. She steams west at 27 kt, so trust TACAN 74X over the waypoint.</p>

</div>

<div class="pagebreak"></div>

<div class="kicker">Map 2</div>

![Objective area](Operation_Long_Road{% if not colt %}_Own_SEAD{% endif %}_area.png){: .short }

<div class="keep" markdown="1">

## Control: SEAD leads (Type 3, PONTIAC)

| Step | You (F10) | Response |
|---|---|---|
| 1 | Pontiac: target update | Column status, the lead vehicle and the Straight Flush coordinates |
{% if colt %}
| 2 | PUSH COLT; the lead's own HARMs from MAGNUM as backup | COLT reaches its Magnum point about 3 minutes after the push. A hit puts the SA-6 off the air for {{ suppress_s }} s |
{% else %}
| 2 | HARMs from MAGNUM (waypoint 2) | A hit puts the SA-6 off the air for {{ suppress_s }} s |
{% endif %}
| 3 | IN on SA-6 radar (DEAD), laser on the Straight Flush | Always cleared. Radar destroyed means the SA-6 is out for good |
| 4 | IN on column | CLEARED HOT only while the SA-6 is suppressed or dead, otherwise ABORT |
| 5 | Laser on column, or terminate | The spot works along the column; once it is moving, the vehicle nearest cover |
| 6 | OFF | BDA: impacts, closest miss, column destroyed or escaped, SA-6 status |

A clearance lasts 2 minutes. Releases without clearance, and attacks on the column while the SA-6 is live, are flagged in the summary.

</div>

<div class="pagebreak"></div>

<div class="kicker">Kneeboard</div>

<!-- task -->
## Times and route

The column moves at **{{ restart_hms }} local / {{ restart_z }}Z**, {{ restart_min }} minutes after mission start. The MiG-29s launch at about {{ mig }}.

| WP | Name | Coordinates | Alt | Leg | Course |
|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} |
{% endfor %}

MAGNUM (waypoint 2) is the HARM launch point, about 20 nm from the SA-6.

## Loadout

{% if colt %}
Enfield 1-1 (lead, backup SEAD and DEAD): 2× AGM-88C HARM, 2× GBU-12, 2× Mk-20 Rockeye, LITENING, 2× AIM-9X, AIM-120C, tank. Enfield 1-2 (strike): 4× Mk-20 Rockeye, 2× GBU-12, LITENING, 2× AIM-9X, AIM-120C, tank.
{% else %}
Both jets (own SEAD): 2× AGM-88C HARM, 2× GBU-12, 2× Mk-20 Rockeye, LITENING, 2× AIM-9X, AIM-120C, tank.
{% endif %}

<!-- pdf-only -->
| Station | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
{% for j in loadout %}
| {{ j.jet }} | {{ j.stations | join(" | ") }} |
{% endfor %}
<!-- /pdf-only -->

## Comms and navigation

| Callsign | Role | Frequency | Notes |
|---|---|---|---|
| MOTHER | CVN-74 John C. Stennis | 127.5 AM | TACAN 74X STN · ICLS 11 |
| ENFIELD 1-1, 1-2 | You | 251.0 AM | Flight frequency, shared with ARCO |
| ARCO | S-3B tanker, 15,000 ft | 251.0 AM | TACAN 60Y |
| MAGIC | E-2C, controls CHEVY and UZI | 255.0 AM | |
| PONTIAC | MQ-9 over the column, laser | F10 menu | Laser 1688 |
{% if colt %}
| COLT | 2× F/A-18C, 4 HARMs each (AI) | F10 push | Holds west of MAGNUM |
{% endif %}
| CHEVY | 2× F/A-18C CAP, 20,000 ft | MAGIC commits | Fleet defence comes first |
| UZI | 2× F/A-18C alert-5 on Mother | Via MAGIC | About 12 min to the CAP station |

## F10 radio menu: Long Road

| Item | What it does |
|---|---|
| Pontiac: target update | Column and SA-6 status and coordinates; when the column moves |
{% if colt %}
| PUSH COLT (SEAD) | Sends COLT at the Straight Flush. Once only |
{% endif %}
| Request CAP cover | Asks MAGIC for CHEVY over the column. Approved only if CHEVY is free |
| Pontiac laser > Straight Flush, column, terminate | PONTIAC's laser, code 1688 |
| Enfield 1-x > IN on SA-6 radar (DEAD) | Always cleared hot |
| Enfield 1-x > IN on column | Cleared only inside a suppression window or after DEAD |
| Enfield 1-x > OFF (request BDA) | BDA for your last pass |
| Mission summary now | Outcome on demand (automatic once every jet is down) |
<!-- /task -->
