<div class="kicker">Mission briefing · Enfield flight · Narrow Gate campaign, {% if hard %}failure branch{% else %}partial branch{% endif %}</div>

# Operation Stone Ford{% if hard %} (hard){% endif %}

F/A-18C Hornet · 1–2 players · Caucasus · close air support, troops in contact · cold start and recovery aboard CVN-74

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| First wave | **{{ waves[0].time }} local** | Defend | Blue's bridgehead at Ganmukhuri, on the Inguri |
| Attack | {{ n_waves }} waves, {{ n_veh }} vehicles, from the north-west | Weapons | Maverick F, GBU-12, Mk-20 Rockeye |
| Control | AXEMAN, ground JTAC, Type 1 | Lost if | {{ lost_at }} vehicles reach the village |
| Mother | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Support | ARCO, MAGIC, {% if hard %}CHEVY on fleet defence only{% else %}CHEVY CAP{% endif %} |

</div>

<!-- ingame -->
## Situation

{% if hard %}
CAG's verdict on Narrow Gate was short: "Your plan didn't stop them, and I can't spare more for it." The lead battalion reached the Inguri at full strength. CHEVY stays on fleet defence. MAGIC will commit it only against threats to the boat, never to the Inguri. You have your section and ARCO. Win this and the plan's failure is forgiven. Lose it and the bridges are gone.
{% else %}
CAG's verdict on Narrow Gate: not what you promised. Some of the depot burned, but the lead battalion kept enough fuel to move, and it reached the Inguri anyway. The Army needs help now. You keep what you had: your section, CHEVY on CAP, and ARCO.
{% endif %}

What is left of the {% if not hard %}weakened {% endif %}battalion is attacking Blue's bridgehead at Ganmukhuri, on the north bank of the Inguri, which covers the bridges. Blue is holding the village with light infantry who are almost out of anti-armour weapons. If the bridgehead falls, the bridges go with it.

The attack comes from the north-west in {{ n_waves }} waves, {{ n_veh }} vehicles in all:

{% for w in waves %}
- {{ w.name }} moves at {{ w.time }}: {{ w.mix }}.
{% endfor %}

{% if hard %}
Two MiG-29s are expected over the Inguri at about {{ mig }}, before the first wave moves, and nobody is coming to deal with them for you. Bring the AIM-9Xs and the AMRAAM into the fight if you have to.
{% else %}
Two MiG-21s will come down from Gudauta at about {{ mig }}. MAGIC will commit CHEVY when they launch, and you can ask for cover over the Inguri from the F10 menu. If CHEVY is out of missiles, short of fuel, down to one jet or lost, Mother launches her alert-5, UZI, two more Hornets: about 12 minutes to station, and only one section.
{% endif %}

## Mission

Break the attack before it reaches the village. The bridges are lost if {{ lost_at }} vehicles get through.

## Control

AXEMAN is a ground JTAC with the infantry, and this is **Type 1** control: he has to see you on every pass. Call IN from inside {{ vis_nm }} nm, with a line of sight to the village, or he will tell you to CONTINUE without a clearance. You get a new 9-line for every target group, and each one has to be read back.

Final attack headings are **020–070 or 200–250**: along the front, never toward the village. Targets within {{ danger_r }} m of friendlies are danger close, and AXEMAN gives his initials in the 9-line and the readback. Any impact within {{ frat_r }} m of friendlies is fratricide. A vehicle that reaches the village edge, {{ bridge_r }} m from the bridges, is through. Red opens fire once it is inside about {{ contact_km | round(0) | int }} km.

<div class="keep" markdown="1">

## What happens next

This is the last mission on this branch of the campaign.

| Result | Needs | What it means |
|---|---|---|
| Success | No more than {{ held_max }} vehicle through, and no fratricide | The bridgehead holds. The Red advance dies at the Inguri |
| Partial | {{ held_max + 1 }} to {{ lost_at - 1 }} through, or any fratricide | The bridgehead holds, at a cost |
| Failure | {{ lost_at }} or more through | The bridges at Ganmukhuri are lost. Blue falls back behind the Inguri |
| A jet lost | Any result | If the pilot ejected over land, also fly **Operation_Sandy_Lift_Inguri.miz** |

</div>

Vehicles still advancing when your last jet lands count as through. Secondary objective, **clean recovery**: every jet that launches traps aboard Mother with at least about 2,000 lb of fuel, and nobody is lost.

1 or 2 players, cold start on the deck. Enfield 1-1 is flyable in single player.
<!-- /ingame -->

<div class="keep" markdown="1">

## Key times

| Event | Local |
|---|---|
| Mission start, cold on the deck | {{ start }} |
{% if hard %}
| Red MiG-29 pair over the Inguri | {{ mig }} |
{% endif %}
{% for w in waves %}
| {{ w.name }} moves ({{ w.n }} vehicles) | {{ w.time }} |
{% endfor %}
{% if not hard %}
| Red MiG-21 pair launches | {{ mig }} |
{% endif %}

</div>

<div class="keep" markdown="1">

<div class="kicker">Map 1</div>

![Theater map](Operation_Stone_Ford{% if hard %}_Hard{% endif %}_theater.png){: .medium }

<p class="small">Coastline is approximate (about 1 km resolution). Courses are true. MOTHER is the carrier's estimated position at recovery. She steams west at 27 kt, so trust TACAN 74X over the waypoint.</p>

</div>

<div class="pagebreak"></div>

<div class="kicker">Map 2</div>

![Objective area](Operation_Stone_Ford{% if hard %}_Hard{% endif %}_area.png){: .short }

<div class="keep" markdown="1">

## Control: Type 1, AXEMAN

| Step | You (F10) | AXEMAN |
|---|---|---|
| 1 | Check in | Situation, threats and game plan |
| 2 | Ready to copy 9-line | A 9-line on the group closest to the village, with live coordinates |
| 3 | Read back 4, 6 and restrictions | Readback correct. A new 9-line needs a new readback |
| 4 | IN, heading 020–070 or 200–250, inside {{ vis_nm }} nm | CLEARED HOT, CONTINUE (he can't see you), or ABORT with the reason |
| 5 | Ten seconds, then Spot | Laser on from AXEMAN's position, code 1688 |
| 6 | OFF | BDA: impacts, closest miss, destroyed, through, still coming |

</div>

<div class="pagebreak"></div>

<div class="kicker">Kneeboard</div>

<!-- task -->
## Times and route

{% for w in waves %}
- {{ w.name }} moves at {{ w.time }} local ({{ w.n }} vehicles).
{% endfor %}
- Red fighters: {{ mig }} local.

| WP | Name | Coordinates | Alt | Leg | Course |
|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} |
{% endfor %}

The IP is over the water: hold there until AXEMAN has a target for you. TGT marks the attack axis north-west of the bridgehead.

## Loadout

Both jets: 2× AGM-65F Maverick, 2× GBU-12, 2× Mk-20 Rockeye, LITENING, 2× AIM-9X, AIM-120C, tank.

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
| AXEMAN | Ground JTAC with the infantry | F10 menu | Laser 1688 |
{% if hard %}
| CHEVY | 2× F/A-18C, fleet defence only | MAGIC commits | Threats to the boat only |
{% else %}
| CHEVY | 2× F/A-18C CAP, 20,000 ft | MAGIC commits | Fleet defence comes first |
{% endif %}
| UZI | 2× F/A-18C alert-5 on Mother | Via MAGIC | About 12 min to the CAP station |

## F10 radio menu: Stone Ford

| Item | What it does |
|---|---|
| Axeman: battle status | Destroyed, through, the closest group, the next wave |
| Request CAP cover | {% if hard %}Refused: CAG has CHEVY on fleet defence{% else %}Asks MAGIC for CHEVY over the Inguri. Approved only if CHEVY is free{% endif %} |
| JTAC Axeman > 1, 2, 3 | Check in, 9-line, read back |
| JTAC Axeman > Enfield 1-x > IN | Type 1 clearance request with your current heading |
| JTAC Axeman > Enfield 1-x > Ten seconds, Spot | Laser on, confirm the spot |
| JTAC Axeman > Enfield 1-x > OFF | BDA for your last pass |
| JTAC Axeman > Terminate | Laser off |
| Mission summary now | Outcome on demand |
<!-- /task -->
