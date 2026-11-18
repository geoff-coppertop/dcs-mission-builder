<div class="kicker">Mission briefing · Enfield 1-1 · Deep Cut, follow-up when a pilot is down over land</div>

# Operation Deep Cut: Escape

F-14B Tomcat · 1 player, or 2 with a RIO · Caucasus · escape and evasion in a captured jet · cold start at Senaki-Kolkhi, recovery aboard CVN-74

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| Start | **{{ start }} local**, cold on the ramp | Seen by | about **{{ discover }}**, or {{ notice }} s after you take off |
| Jet | Captured F-14B, 2× AIM-9M, gun, under half fuel | Chasing | Two MiG-29s off Kutaisi, {{ react }} s after you're seen |
| Home | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Help | CHEVY CAP at the coast, ARCO, MAGIC |

</div>

<!-- ingame -->
## Situation

You ejected over the gorge yesterday. HATCHET, the team on the ridge, reached you before Red did and moved you down the valley overnight. There's no helicopter coming this deep. Instead HATCHET has brought you to Senaki-Kolkhi, where Red has been keeping a Blue F-14B it captured after a divert last month. It is fuelled for engine runs, two Sidewinders are still on the rails, and nobody is guarding it closely.

Nobody is watching this end of the ramp right now. HATCHET reckons the guards reach it about {{ discover_min }} minutes after you climb in, at **{{ discover }}**. If you're still on the ground then, the guns on the field open up.

## Mission

Start the Tomcat, get airborne and get home to Mother.

## How it goes

- **Get moving.** It's a cold start. The jet is noticed {{ notice }} seconds after you take off, or when the guards arrive, whichever comes first, or at once if you fire the gun on the field. Once it is noticed, the field's ZU-23s, a ZSU-23-4 and an SA-13 open up.
- **The chase.** {{ react }} seconds after you're seen, Kutaisi's alert launches two MiG-29s at you. Kutaisi is about 25 nm east of the field, so they start close behind you.
- **The run.** Head west, low and fast, to FEET WET on the coast. MAGIC commits CHEVY, two Hornets on CAP off the coast, onto the MiGs once they launch. Your two AIM-9Ms and the gun are for the moment it goes wrong.
- **Fuel.** Under half internal, no tanks. ARCO is on its track if you need it before the trap.

## What happens next

| Result | What it means |
|---|---|
| Success | You land aboard Mother. The pilot is home |
| Partial | You eject over the water. The Navy picks you up, but the jet is lost |
| Failure | You go down over land again |

1 player, cold start. In multiplayer a second player can take the RIO seat; in single player Jester is your RIO.
<!-- /ingame -->

<!-- task -->
## Key times and comms

| Event | Local |
|---|---|
| Mission start, cold on the ramp | {{ start }} |
| Guards reach the jet | {{ discover }} |

| Callsign | Who | |
|---|---|---|
| MAGIC | E-2C | 255.0 AM |
| CHEVY | Hornet CAP at the coast | MAGIC commits it |
| ARCO | S-3B tanker | 251.0 AM, TACAN 60Y |
| MOTHER | CVN-74 Stennis | 127.5, TACAN 74X, ICLS 11 |

F10 > Escape: **Status** (seen or not, fighters, CAP), **Mission summary now**.
<!-- /task -->

<div class="kicker">Map</div>

![The way home](Operation_Deep_Cut_Escape_theater.png){: .medium }

<div class="keep" markdown="1">

## Route card

| WP | Name | Coordinates | Altitude | Leg | Course |
|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name if r.wp else "Senaki-Kolkhi (ramp)" }} | {{ r.coords }} | {{ r.alt if r.wp else "ramp" }} | {{ r.leg }} | {{ r.course }} |
{% endfor %}

<p class="small">Loadout: {{ load | reject("equalto", "—") | join(", ") }}, gun. MOTHER is the carrier's estimated position; trust TACAN 74X.</p>

</div>
