# THE ITEM REFACTOR — executed ledger (planned 2026-07-27, shipped 2026-07-28)

Joel's order, verbatim: *"all items need to be completely refactored and
catagorized... make the items for TUIPET. a game built 100% by claude code"*,
then: *"lets start from the beginning. refactor the item system. do not half
ass this... make a plan, audit it, ship it. make sure shops are balancee.
daily items. not all at once like the home shop. basic items sure but cmon...
drop the mood shit if its dead, its supposed to be. we have manners. jist plan
it, audit, proofread, polish, execute, audit and ship."*

## THE ONE RULE

> An item earns its slot only if it does something **no free action and no
> cheaper item already does.**  A shop earns a row only if that row is a
> **choice**.

## WHAT SHIPPED

### 1. The catalog: 131 → 114, every survivor distinct

**18 keys retired, each with a named heir** (`shop.RETIRED`):

| retired | why | heir |
|---|---|---|
| balloon | moves NOTHING (`_toy()` all-zero) | ball |
| bubble_bath | strictly less than the free C key | ball |
| toy_car, stuffed_animal | 500/1000b for `obedience -1`, no upside | ball |
| cold_shower | Music Player's niche, done worse (+ a care mistake) | cold_compress |
| toilet | between a free key and the Port Potty | port_potty |
| bitter_herbs | duplicate of Book | book |
| nuts, oats, egg, guava, milk, chicken_soup | six copies of `hunger+1 · weight+1` | bread |
| rice, salmon | copies of `hunger+1 · weight+2` | cheese |
| beans | dominated by Broccoli | broccoli |
| ice_cream, banana | dominated by Cake | cake |

**Nobody loses anything:** owned copies convert 1:1 in the bag heal
(`persistence._heal_bag`, the 07-18 LEGACY_KEYS precedent), and every authored
channel still speaking an old icon — loot rows, cup prizes, town stock lines —
resolves to the heir through `key_for_icon`'s `_RETIRED_ICONS` fallback.  A
champion whose cup paid Bubble Bath gets a Ball, never nothing.

**One item ADDED — the CURE hole:** `cold_compress` (2000b, wears the shower's
freed art).  `care_mistakes` is the game's deadliest meter (21 reads, gates
evolutions, kills) and exactly one item touched it, at 7777b.  The compress
wipes one slip for a quarter of the price and **charges 8 energy** instead of
granting 12 — relief you have to sleep off, a ladder instead of a lone luxury.

### 2. The categories: eight ACTS

Every key now answers *"what do I want to happen?"*:

**Feed** (hunger·weight·overeat) · **Rest** (energy, the rules of night and
filth) · **Cure** (sick·injured·care_mistakes; Revive Floppy lives here — the
ultimate cure) · **Drill** (effort, weight down) · **Manners** (obedience,
both directions) · **Power** (Va/D/Vi/dp — the chip ladder finally named for
what it moves) · **Treasure** (the capsules) · **Evolve** (the doors: spirits,
relics, X, growth, inheritance) · **Road** (spent on the march).

The tab BAR stays four wide (the P4 width law); the acts ride the Items tab
as its sub-headers.  Armor-Spirit (the crest shelf) is untouched.

### 3. The home shop: a store, not a wall

`home_stock` was the whole catalog, every day (96 rows).  Now:

- **STAPLES, always** (11): fish, bread, cheese, vegetable, sleeping_pill,
  music_player, energy_drink, dumbbell, slim_drink, supplement, capsule_a.
- **THE DAILY BAND** (10): the rest of the sellable pool dealt as a
  **shuffled cycle** — seeded per epoch, so every device deals the same week
  and *every key is guaranteed a shelf day each ~6-day cycle*.
- **TWO DOOR SHELVES bypass the band**: the Digimentals (crest door) and the
  Road gear (map-clear gated — a tamer who just earned the warp doesn't wait
  three days to buy it).
- ~23 rows a day.  Deal + capsule rations unchanged; staples/band sell
  unlimited at catalog price (a flip at catalog is always a loss).

Towns are untouched — they were already the curated half.  The duplicated
ration arithmetic now lives once (`_ration_left`), and successor resolution
dedups a town that stocked both an item and its heir.

### 4. Mood: BURIED

Joel: *"there shoukdnt be a mood system at all... we have manners."*
The meter had ONE read (its own initializer).  Gone: the field, `_set_mood`
(19 write-sites), `mood_pct`, the `last_mood` snapshot.  Old saves load
clean — `pet_from_save` drops unknown fields.  `current_mood()` (the DERIVED
word driving poses/personality) and `daily_mood` (its tally) are live systems
and stay.

### 5. The capsules: named, not collapsed  *(audit deviation)*

The plan said collapse 10 → 2.  The audit killed that: the tier keys are HOW
an earned tier persists in a bag — a collapse would erase which capsule you
were given.  The real complaint was ten identical labels, so the display was
fixed instead: Capsule / Blue / Green / Red / Silver / Gold / Prism / Royal,
and the pranks now *Rattling* and *Hissing*.  Keys, grants, festival pools
unchanged.

### 6. Other audit deviations (each argued, not slipped)

- **Glutton's Platter (planned) was CUT before shipping**: feeding a stuffed
  pet already bills `overeat+1` + a care mistake (petcare's overfeed door) —
  the platter would have been a *paid bypass of an authored penalty*.
- **orange stays** despite duplicating fruit: it IS the Citramon door
  (evol_food 42).  **fruit / ai_food_pill / meat stay**: grant-system goods,
  not shelf noise.
- **FEED holds ~17 priced rows, not the plan's 8**: the cap was for the
  always-visible staples; the survivors are each distinct (the ladder, the
  peppers, the traps, the door, the feast).

## VERIFICATION (all green before ship)

2687 tests (new pins: cycle coverage, staples-always, RETIRED-heir liveness,
bag-heal conservation, category laws) · ruff ratcheted 258 → 237 · mypy at
its 24-error star-import baseline · full cross-wiring audit probe: **0
findings** (every key through use_item awake+asleep, fx replay, 462 enemies'
drops, every trophy prize, town dedup, cycle coverage, mood burial) · sim
soak ×4 policies: 0 findings · menu + adventure sheets render.

## OPEN (named, not snuck)

- The full policy-object merge of `home_stock`/`town_stock` (they now share
  the ration math and the row grammar; their row *sources* remain separate
  loops by design — towns walk authored data, home walks the catalog).
- Anything touching the FEED survivor list is Joel's taste call.
