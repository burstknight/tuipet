"""THE ADVENTURE AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown adventure audit next."

Two findings and the invariants a run must hold, measured by RUNNING the
road rather than reading it:

  * F1 (hotfixed v0.5.250, pinned in test_battle_audit) — the boss gate
    inherited the HOME energy clause and refused every honest arrival.
  * F2 — the Town Transport past the last town: every zone has exactly
    ONE town span, so once you walk past it the 500b ticket bought a rest
    in place while announcing "Warped to a town" — no hub, no shop, no
    visit-or-walk-on choice.  Late, drained and past the town is exactly
    when a tamer reaches for that ticket.
  * the run invariants: lives, progress, the weight floor, the effort
    cap, the streak, and loot that the bag can actually use.
"""
import random

import pytest

from tuipet import adventure as A, shop
from tuipet.adventurescreen import AdventurePanel
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight() + 6
    p.bits, p.adv_progress = 0, 3
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _zone_with_town():
    return next(z for z in A.ZONES if z.get("town_legs"))


# ---- F2: the Town Transport --------------------------------------------

def test_a_town_warp_lands_in_the_town_it_promises():
    z = _zone_with_town()
    a, b, _t = z["town_legs"][0]
    for start in (0, a, b):
        p = _pet()
        p.add_item("town_transport")
        adv = A.Adventure(p, zone=z)
        adv.loc = start
        assert "town_transport" in adv.held_transports()
        assert adv.use_transport("town_transport") == "town-warp"
        assert adv._in_town(adv.loc), f"warp from {start} landed outside the town"
        assert p.inventory.get("town_transport", 0) == 0     # the ticket is spent


def test_past_the_last_town_the_ticket_is_not_offered_or_spent():
    z = _zone_with_town()
    _a, b, _t = z["town_legs"][0]
    p = _pet()
    p.add_item("town_transport")
    adv = A.Adventure(p, zone=z)
    adv.loc = b + 1
    assert "town_transport" not in adv.held_transports()      # hidden, like the
    #                                                           full-hearts life warp
    assert adv.use_transport("town_transport") is None        # and refused if forced
    assert p.inventory.get("town_transport", 0) == 1          # ticket KEPT
    assert adv.loc == b + 1                                   # and no silent rest


def test_the_planted_feet_strip_only_offers_a_warp_that_exists():
    """The honest-outs rule (energy audit 2026-07-23) meets F2: a spent pet
    past the town must not be told to warp."""
    z = _zone_with_town()
    _a, b, _t = z["town_legs"][0]

    def strip_at(loc):
        p = _pet(energy=-1)
        p.add_item("town_transport")
        pan = AdventurePanel(p, zone=z)
        pan._trans = pan._pulse = None
        pan.travelling, pan._landed, pan._refused = True, True, True
        pan.adv.loc = loc
        return pan.strip()

    assert "T warp" in strip_at(0)
    assert "T warp" not in strip_at(b + 1)
    assert "ESC home" in strip_at(b + 1)


# ---- the run's invariants ----------------------------------------------

@pytest.mark.parametrize("seed", [11, 12, 13])
def test_a_whole_run_holds_its_invariants(seed):
    random.seed(seed)
    p = _pet()
    adv = A.Adventure(p, zone=A.ZONES[A.PROGRESSION[seed % len(A.PROGRESSION)]])
    base = p._base_weight()
    for _ in range(4000):
        r = adv.travel()
        if r is None:
            break
        tag = r[0] if isinstance(r, tuple) else r
        if tag == "encounter":
            won = random.random() < 0.7
            p.record_battle(won, r[1])
            adv.chain(won)
            if won:
                adv.award_bits(r[1])
            if adv.resolve(won) == "failed":
                break
        elif tag == "boss":
            p.record_battle(True, r[1])
            adv.resolve_boss(True)
            break
        elif tag == "find":
            assert r[1] in shop.CATALOG or r[2], "found loot the bag can't use"
            adv.finds += 1
        elif tag == "hazard":
            adv.hazard_hit()
        elif tag == "refused":
            break
        assert 0 <= adv.lives <= A.MAX_LIVES
        assert 0 <= adv.loc <= adv.total
        assert p.weight >= base, "the march ground the pet under its base weight"
        assert p.strength <= A.TRAVEL_EFFORT_CAP
        assert adv.streak <= adv.best_streak
    assert adv.bits_earned >= 0


def test_a_town_rest_fills_the_tank_breaks_the_chain_and_fires_ONCE(monkeypatch):
    # a quiet road: this pin is about the REST, not about what jumps out
    for knob in ("ENCOUNTER_CHANCE", "HAZARD_CHANCE", "FIND_CHANCE"):
        monkeypatch.setattr(A, knob, 0.0)
    z = _zone_with_town()
    a, _b, _t = z["town_legs"][0]
    p = _pet(energy=1)
    adv = A.Adventure(p, zone=z)
    adv.loc, adv.lives, adv.streak = a - 1, 1, 4
    adv.best_streak = 4
    assert adv.travel() == "town"                       # stepped in: rested
    assert adv.lives == A.MAX_LIVES
    assert p.energy >= p.max_energy // 2                 # at least half a tank (D1)
    assert adv.streak == 0 and adv.best_streak == 4      # the chain pays the price
    p.energy = 1
    adv.travel()                                         # the NEXT leg in town
    assert p.energy == 1, "the rest re-fired inside the same town span"


# ---- progression --------------------------------------------------------

def test_only_the_frontier_advances_the_road():
    p = _pet()
    p.adv_progress = 3
    assert A.record_win(p, A.ZONES[A.PROGRESSION[3]]) and p.adv_progress == 4
    assert not A.record_win(p, A.ZONES[A.PROGRESSION[3]])      # a replay
    assert not A.record_win(p, A.ZONES[A.PROGRESSION[10]])     # out of order
    assert p.adv_progress == 4
    p.adv_progress = len(A.PROGRESSION)
    assert not A.record_win(p, A.ZONES[A.PROGRESSION[-1]])     # the end holds
    assert len(A.unlocked_indices(p)) == len(A.PROGRESSION)


# ---- every road state renders (the panel smoke law) ---------------------

def _panel(**kw):
    p = _pet(**kw)
    pan = AdventurePanel(p, zone=A.ZONES[A.PROGRESSION[2]])
    pan._trans = pan._pulse = None
    pan.travelling = pan._landed = True
    return p, pan


ROAD_STATES = {
    "march": lambda pan: None,
    "glint": lambda pan: setattr(pan, "_find", "fish"),
    "ambush": lambda pan: setattr(pan, "_hazard",
                                  {"t": 1, "enemy": {"num": 120, "name": "K"},
                                   "dodged": False, "hit": False}),
    "town prompt": lambda pan: setattr(pan, "_town_prompt", True),
    "town rest": lambda pan: setattr(pan, "_rest_t", 3),
    "life recovery": lambda pan: setattr(pan, "_heal_t", 3),
    "at the gate": lambda pan: setattr(pan, "_at_gate", True),
    "summary": lambda pan: setattr(pan, "_summary", True),
    "parade": lambda pan: setattr(pan, "_parade",
                                  {"t": 1, "nums": [120], "msg": "The gate falls!"}),
    "pulse": lambda pan: setattr(pan, "_pulse", {"t": 1, "parade": [], "msg": None}),
}


@pytest.mark.parametrize("state", sorted(ROAD_STATES))
def test_every_road_state_renders_inside_the_arena(state):
    _p, pan = _panel()
    ROAD_STATES[state](pan)
    txt = pan.text()
    plain = txt.plain if hasattr(txt, "plain") else str(txt)
    rows = plain.split("\n")
    assert len(rows) <= 12, f"{state}: {len(rows)} rows"
    assert max(len(r) for r in rows) <= 40, f"{state}: too wide"
    pan.strip()                                   # the hint line renders too
