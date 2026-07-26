# THE GREAT ITEM EXPANSION — 2026-07-26 (overnight build)

Joel's orders, verbatim anchors:
- "bring in all 99 unused items" / on the law rows: "bring them all in, just give
  it a function if you want. or not, its your call. tuipet is its own game now"
- evo keys: "Wire fully" · capsules: "roll the existing find tool. rewire
  christmas presents to basically be holiday versions of these"
- "we gotta make sure everything is spread out too. shops, digs, cups, etc.
  i even want battle drops in adventure. make your best judgements. make sure
  everything is balanced. when you are done, audit everything."

## The count
143 authored consumables (59 foods + 84 items); 44 were shipped.
- 11 Digimentals (i:15-25) are ALREADY live through the crest shelf
  (shopscreen._icon renders them via Pet._CREST_IDS) — single door stands,
  no duplicate catalog entries.  "Brought in" by recognition, not addition.
- 1 collision: i:35 authored "Blue Crystal" (direct-evo) — its sprite is worn
  by the shipped dna_crystal.  Skipped (icon uniqueness law beats one row).
- **88 new catalog keys**: 34 foods + 54 items.  44 + 88 = 132 catalog keys.

## Builder rulings (the law rows)
- **bandage (i:80, 10b)**: comes in as a pocket med that cures injury.  H stays
  the free home cure — at 10b nothing is paywalled; the item exists so drops/
  gifts/shelves can hand out a med.  Joel explicitly overrode the shelf ban
  tonight ("bring them all in... your call").
- **elixir (f:15, 2000b)**: premium combo — cures sickness AND energy to full.
  The free pill stays; this sells convenience, not the cure.
- **vitamin_g (f:16, 2000b)**: premium combo — heals injury AND effort full +
  injury guard (the vitamin's big sibling).  H stays free.
- **meat (f:0), fruit (f:2), med (f:4), ai_supplement (f:43), ai_food_pill
  (f:44), burnt_food (f:56)**: price 0 in the source = grant-only here (price
  None): road finds / gift & capsule payouts, never sold.  med cures sickness
  when used — free path, not a shelf sale.

## Functions of note (all other stats read straight off the authored columns;
## Mood/Enthusiasm/Stress stay dormant — documented, never wired)
- **hp_chip / hp_chip_g** (1500/3000b): +5/+10 to ALL THREE powers ("HP" in
  tuipet's battle IS the power pool).  Price-per-point matches the chip curve.
- **board_game / computer_game** (2000b): attribute RESHAPERS — authored VDV
  conversion (Vaccine→Data / Virus→Data, ±15).  New lever, fully authored.
- **hedonism_101** (2000b): obedience −80, exactly as authored — the
  anti-textbook, a trap with a warning label (poison-mushroom precedent).
- **toy_oven** (500b): hunger −1 ("+Appetite" — makes room for a meal).
- **futon** (1000b): a daytime doze refills to FULL tank instead of half
  (the one live gap in the sleep system; consumed on the next doze).
- **toilet** (1000b): clean now + obedience +1 (port_potty's little brother).
- **zone_transport** (750b, road): the safe Birdramon LIFT — 10 legs ahead,
  no ambush (walking home was already free, so no "escape rope" dud; the
  middle ticket between walking and the 250b danger dash).
- **continent_transport** (1000b, road): the Whamon camp — rest to half tank
  mid-road, anywhere, once per use (lives stay life_recovery's job).
- **x_program** (grant-only; authored 100% drop from 2 enemies): the risky
  X-Antibody — empties belly, zeroes effort, drains 80% energy, then grants
  the X.  The authored drains ARE the risk; no invented death roll.
- **chocolate_egg** (300b): a snack with a toy inside — eats +1 hunger AND
  rolls a common-tier surprise.
- **capsules ×10** (100b): roll the surprise pool (the _pick_gift grammar).
  i:71/i:77 (AngrySurprise) are PRANK capsules — junk-pool payouts + jeer.
  On a HOLIDAY any capsule's roll reaches one tier higher (festival grammar).
- **evo keys, wired fully**: digitron → item_select(33); 8 direct items
  (horn_helmet, grey_claws, water_bottle, torn_tatter, white_wings,
  black_wings, metal_armor, flaming_wings) → item_direct(DigimonID);
  20 spirits → item_select(43..62).  Refusal keeps the item.

## Distribution (spread out: shops, digs, cups, drops)
- **Shops**: new priced rows join home catalog + town shelves; dormant
  shopConsumable.csv override rows come alive via key_for_icon; guest-deal
  pool triples (26 towns stay unique); tiers derive from price as ever.
- **Digs (road finds)**: biome pools grow with fitting new foods/toys;
  Human spirits seed the LAST 10 zones in PROGRESSION (one each, endgame digs).
- **Cups**: the AUTHORED prize table came alive — every cup's ItemID/FoodID
  resolves now: 36 cups award their own authored relic (incl. direct-evo
  items and specific DIGIMENTALS via the crest identity), 25 pay authored
  food hampers with amounts.  The flat energy-drink placeholder retired.
- **Beast spirits**: the Frontier chain, authentic — USING a Human spirit
  banks its Beast half in the bag (roads give Human, the Human gives Beast).
  Deterministic; no invented cup RNG.
- **Battle drops (NEW)**: fully AUTHORED — enemies.csv LootTableID →
  lootTable.csv → dropRate.csv.  Wilds drop chips at 2-7%, elites drop
  X-Antibody at 7%, the ten unique bosses drop their Digimental at 100%.
  Boss replay drops ride the road_bounty daily ration (anti-printer).
- **Christmas/holiday presents**: the festival road present now grants a
  CAPSULE (the wrapped box is an item); opened on the holiday it rolls a
  tier higher.  Home gift-call untouched.

## Balance guards (audit checklist)
- Capsule EV vs 100b price — measure resale EV, adjust pool/price if printer.
- Boss digimental drops: first-conquest guaranteed; replays rationed.
- Cup prize: bounded by the hourly cup cadence.
- Spirits/x_program: never sold, never resellable above 0? (grant-only rows
  resell at nominal 100//2 via entry() — check).
- All new effects touch LIVE meters only; test_catalog_touches must hold.
