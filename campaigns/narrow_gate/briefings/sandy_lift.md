{% set after = {"narrow_gate": "Narrow Gate", "long_road": "Long Road", "inguri": "Stone Ford"}[variant] %}
<div class="kicker">Mission briefing · Sandy flight · Narrow Gate campaign, rescue after {{ after }}</div>

# Operation Sandy Lift{% if variant == "long_road" %} (Long Road){% elif variant == "inguri" %} (Inguri){% endif %}

F/A-18C Hornet · 1–2 players · Caucasus · rescue escort (Sandy) · cold start and recovery aboard CVN-74

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| Search party | moves **{{ search }}**, reaches the pilot about {{ capture }} | Survivor | {% if variant == "narrow_gate" %}Fields north-west of Ochamchire{% elif variant == "long_road" %}Fields south of the coast road{% else %}Red side of the line, NW of Ganmukhuri{% endif %} |
| Rescue helo | DODGE 1-1 (SH-60B), called in from F10 | Weapons | Maverick F, Mk-20 Rockeye, GBU-12 |
| Overhead | PONTIAC (MQ-9), laser 1688 | Threats | {% if variant == "narrow_gate" %}SA-13, 2× ZSU-23-4{% elif variant == "long_road" %}SA-13, ZSU-23-4{% else %}SA-9, ZSU-23-4{% endif %}, ZU-23, Igla; {{ mig_kind }} |
| Mother | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Support | ARCO, CHEVY CAP, MAGIC |

</div>

<!-- ingame -->
## Situation

CAG's orders are short: "We don't leave people." He has released DODGE, a rescue helicopter, and your section to bring the pilot home.{% if variant == "inguri" %} He has also released CHEVY from whatever it was doing to cover the rescue.{% endif %} If the pilot on the ground is from your own section, the squadron has a spare jet and a spare pilot on the schedule; in multiplayer, Enfield 1-2 flies that seat.

{% if variant == "narrow_gate" %}
A Hornet went down near Ochamchire during Narrow Gate. The pilot is on the ground, uninjured and hiding in the fields north-west of town, about 2 nm from the fuel depot. A Red search party is {{ search_km }} km away at the edge of town: a BTR-80, a ZU-23 on a truck, and riflemen with an Igla. It starts toward the pilot at about **{{ search }}**, and at its pace it reaches them around **{{ capture }}**.

The depot's short-range defences are still there: two ZSU-23-4s and an SA-13, and the SA-13 can reach the pickup site. The SA-6 is not. PONTIAC watched what was left of the battery pack up and drive off north-east within an hour of the strike. Mobile SAMs move once they have been seen.
{% elif variant == "long_road" %}
A Hornet went down during Long Road. The pilot is on the ground, uninjured and hiding in the fields south of the coast road, about 1.5 nm south-east of where the column was hit. A Red search party is {{ search_km }} km away at the road junction where the column turned inland: a BTR-80, a ZU-23 on a truck, and riflemen with an Igla. It starts toward the pilot at about **{{ search }}**, and at its pace it reaches them around **{{ capture }}**.

What is left of the brigade has pulled into the hills with its SA-6, out of reach of the pickup site. It left a rear guard on the road, a ZSU-23-4 and an SA-13, and both can reach the pickup site.
{% else %}
A Hornet went down during Stone Ford. The pilot is on the ground on the Red side of the line, about 2.6 nm north-west of the Ganmukhuri bridgehead, and the infantry in the village can't get to them. A Red search party is {{ search_km }} km away, setting out from Red's assembly area further north-west: a BTR-80, a ZU-23 on a truck, and riflemen with an Igla. It starts toward the pilot at about **{{ search }}**, and at its pace it reaches them around **{{ capture }}**.

Red's attack left air defence behind on its line, a ZSU-23-4 and an SA-9, and both can reach the pickup site.
{% endif %}

## Mission

You are SANDY. Clear the area around the pilot, bring DODGE in, and keep the helicopter alive until it is back aboard Mother.

DODGE 1-1, an SH-60B, is holding over the water {{ hold_nm }} nm {{ hold_dir }} of the survivor, about {{ transit_min }} minutes away. Call it in from the F10 menu when the area is clear. DODGE lands next to the survivor, needs {{ board_s }} seconds on the ground, then flies home. Keep the search party off the pilot and the guns off the helicopter.

DODGE goes when you call, clean LZ or not, and warns you if threats are still close. Call too late and the search party gets there first: the last call that still beats them is about **{{ latest_call }}**.

## Air threat

Two {{ mig_kind }} come looking from Gudauta at about {{ mig }}. MAGIC will commit CHEVY when they launch, and you can ask for cover over the survivor's area from the F10 menu. If CHEVY is out of missiles, short of fuel, down to one jet or lost, Mother launches her alert-5, UZI, two more Hornets: about 12 minutes to station, and only one section.

<div class="keep" markdown="1">

## What happens next

| Result | Needs |
|---|---|
| Success | DODGE lands aboard Mother with the survivor |
| Failure | The survivor is captured, or DODGE is lost |

</div>

Secondary objective, **clean recovery**: every Sandy jet traps aboard Mother with at least about 2,000 lb of fuel, and nobody is lost. The summary comes once DODGE and both jets are down.

1 or 2 players, cold start on the deck. Enfield 1-1 is flyable in single player.
<!-- /ingame -->

<div class="keep" markdown="1">

## Key times

| Event | Local |
|---|---|
| Mission start, cold on the deck | {{ start }} |
| Search party starts moving | {{ search }} |
| Red {{ mig_kind[:-1] }} pair launches | {{ mig }} |
| Latest DODGE call ({{ transit_min }} min transit and {{ board_s }} s on the ground, estimate) | **{{ latest_call }}** |
| Search party reaches the survivor, if untouched (estimate) | {{ capture }} |

</div>

<div class="keep" markdown="1">

<div class="kicker">Map 1</div>

![Theater map]({{ miz[:-4] }}_theater.png){: .medium }

<p class="small">Coastline is approximate (about 1 km resolution). Courses are true. MOTHER is the carrier's estimated position at recovery. She steams west at 27 kt, so trust TACAN 74X over the waypoint.</p>

</div>

<div class="pagebreak"></div>

<div class="kicker">Map 2</div>

![Objective area]({{ miz[:-4] }}_area.png){: .short }

<div class="keep" markdown="1">

## Rescue sequence

| Step | You | What happens |
|---|---|---|
| 1 | Pontiac: LZ report | Survivor coordinates, how far off the search party is, threats within {{ threat_km }} km |
| 2 | Kill what threatens the helicopter | The air defence near the pickup site, then the ZU-23 and Igla with the search party |
| 3 | Stop the search party | If it gets within {{ capture_r }} m of the survivor, the pilot is captured |
| 4 | CALL IN DODGE | DODGE pushes, about {{ transit_min }} min, and warns you if threats remain |
| 5 | Cover the pickup | {{ board_s }} s on the ground next to the survivor's green smoke |
| 6 | Escort DODGE home | DODGE lands on Mother; the summary follows when DODGE and both jets are down |

</div>

<div class="pagebreak"></div>

<div class="kicker">Kneeboard</div>

<!-- task -->
## Times and route

The search party moves at {{ search }} local and reaches the survivor at about {{ capture }} if nothing stops it. Latest DODGE call about {{ latest_call }}. {{ mig_kind }} at {{ mig }}.

| WP | Name | Coordinates | Alt | Leg | Course |
|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name }} | {{ r.coords }} | {{ r.alt }} | {{ r.leg }} | {{ r.course }} |
{% endfor %}

## Loadout

Both jets: 2× AGM-65F Maverick, 2× Mk-20 Rockeye, 2× GBU-12, LITENING, 2× AIM-9X, AIM-120C, tank.

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
| ENFIELD 1-1, 1-2 | You, flying Sandy | 251.0 AM | Flight frequency, shared with ARCO |
| ARCO | S-3B tanker, 15,000 ft | 251.0 AM | TACAN 60Y |
| MAGIC | E-2C, controls CHEVY and UZI | 255.0 AM | |
| PONTIAC | MQ-9 over the survivor | F10 menu | Laser 1688 |
| DODGE | SH-60B rescue helicopter | F10 call-in | Holds {{ hold_nm }} nm {{ hold_dir }} of the survivor |
| CHEVY | 2× F/A-18C CAP, 20,000 ft | MAGIC commits | Fleet defence comes first |
| UZI | 2× F/A-18C alert-5 on Mother | Via MAGIC | About 12 min to the CAP station |

## F10 radio menu: Sandy Lift

| Item | What it does |
|---|---|
| Pontiac: LZ report | Survivor position, search party, threats within {{ threat_km }} km, DODGE status |
| Survivor: pop green smoke | Marks the survivor |
| CALL IN DODGE (rescue helo) | Sends the helicopter in |
| Request CAP cover | Asks MAGIC for CHEVY over the survivor's area. Approved only if CHEVY is free |
| Pontiac laser > nearest threat, terminate | Laser on the closest ground threat to the pickup site, code 1688 |
| Mission summary now | Outcome on demand |
<!-- /task -->
