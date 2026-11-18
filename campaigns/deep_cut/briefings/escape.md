<div class="kicker">Player reference · not an operations order · Deep Cut follow-up when a pilot is down over land</div>

# Operation Deep Cut: Escape

F-14A Tomcat · 1 player, or 2 with a RIO · Caucasus · escape and evasion in a stolen jet · cold start at Senaki-Kolkhi, recovery aboard CVN-74

<p class="small">Nobody briefs an escape. In the story, all you have is what HATCHET whispered to you on the ramp and what you remember. This sheet is for you, the player.</p>

<div class="glance" markdown="1">

| | | | |
|---|---|---|---|
| Start | **{{ start }} local**, cold on the ramp | Seen by | about **{{ discover }}**, or {{ notice }} s after you take off |
| Jet | Red's F-14A, readied for a ferry flight: full fuel, two tanks, **gun only** | Chasing | Two MiG-29s off Kutaisi, about {{ react_min }} min after you're seen |
| Home | CVN-74 · 127.5 · TACAN 74X · ICLS 11 | Help | CHEVY CAP at the coast, ARCO, MAGIC |
| Code word | **{{ code }}**: check in with MAGIC once airborne | ID zone | {{ id_nm }} nm from Mother: unknown jets get intercepted; the fleet fires inside {{ fleet_nm }} nm |

</div>

<!-- ingame -->
## On the ramp

*HATCHET, low, crouched by the nose gear, {{ start }}:*

"That's your ride. It's theirs: one of the second-hand Tomcats they bought from an export customer. They can barely keep them flying, and this one's being ferried to a depot for overhaul this morning. So it's fuelled for the trip, two bags on, and the only weapon on it is the gun. Don't go looking for a fight.

"Their crew aligned it during engine runs yesterday and nobody's moved it since, so use the stored heading. A full alignment and you'll still be sitting here when the guards come round. The start cart's still hooked up for them. Good thing: no APU on these.

"Guards are doubled after what you lot did to the gorge. Someone checks this end at about **{{ discover }}**, so be rolling well before that. The moment you take off they'll know, and the guns on this field will open up: ZU-23s, a Shilka, an SA-13. Kutaisi's alert crews are sitting in their jets since yesterday, but the word still has to get from here to the sector and back down to them. Figure two MiG-29s off the ground five or six minutes after you're seen. Use the head start.

"Go west, low and fast, to the coast. The Navy knows someone's coming out in a Red Tomcat. It doesn't know when, or which blip is you. Once you're airborne, call MAGIC and give them **{{ code }}**, straight away. An unknown jet heading for a carrier from this side of the coast is a threat until somebody proves otherwise. Their fighters will be busy with you instead of the MiGs, and get too close and the ships will shoot. Mother's TACAN is 74X. Their radios are set up for their flight, not yours.

"You're heavy. Burn it or dump it before you try to land that thing on a carrier.

"Twenty years since you flew one of these, they tell me. Go."

## Mission

Start the Tomcat, get airborne and get home to Mother.

## How the game plays it

- **Get moving.** The stored-heading alignment takes about 3 minutes and runs while the engines spin up; a full alignment (about 8) won't finish before the guards arrive. The jet is noticed {{ notice }} seconds after you take off, when the guards arrive, or at once if you fire the gun on the field.
- **The chase.** {{ react_min }} minutes after you're seen (relaying the report, then a scramble from cockpit readiness), two MiG-29s launch from Kutaisi, about 25 nm east. Get feet wet before they're up and they have to chase you into CHEVY, two Hornets on CAP off the coast, which MAGIC commits onto them. Slow on the ramp, or a long time over land, and they catch you.
- **Identification.** Once you're airborne, F10 > Escape > Check in with MAGIC declares you friendly. Stay silent and it costs you:
    - In the ID zone ({{ id_nm }} nm from Mother), CHEVY is committed to intercept you, **ahead of the MiGs**. It can't cover you from them until you're identified, by checking in or by CHEVY getting close enough to see you.
    - Inside {{ warn_nm }} nm, Mother warns you off. Inside **{{ fleet_nm }} nm**, still unidentified, the fleet fires. Checking in while the missiles are in the air aborts them.

## What happens next

| Result | What it means |
|---|---|
| Success | You land aboard Mother, identified. The pilot is home |
| Partial | You eject over the water: the Navy picks you up, but the jet is lost. Or you trap without being identified |
| Failure | You go down over land again, or the fleet shoots you down |

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

F10 > Escape: **Status** (seen or not, identified or not, fighters, CAP), **Check in with MAGIC ({{ code }})** (airborne only), **Mission summary now**.
<!-- /task -->

<div class="pagebreak"></div>

<div class="kicker">Map</div>

![The way home](Operation_Deep_Cut_Escape_theater.png){: .medium }

<div class="keep" markdown="1">

## Route card

| WP | Name | Coordinates | Altitude | Leg | Course |
|---|---|---|---|---|---|
{% for r in route %}
| {{ r.wp }} | {{ r.name if r.wp else "Senaki-Kolkhi (ramp)" }} | {{ r.coords }} | {{ r.alt if r.wp else "ramp" }} | {{ r.leg }} | {{ r.course }} |
{% endfor %}

<p class="small">In the story you'd carry this route in your head; the game loads it into the jet's navigation system anyway. Loadout: {{ load | reject("equalto", "—") | join(", ") }}, gun. MOTHER is the carrier's estimated position; trust TACAN 74X.</p>

</div>
