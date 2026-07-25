"""THE CARE AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown care audit next."

F1 (FIXED) — THE STARVATION CLOCK COULD NEVER FIRE.  `_starve_t`
accumulates dt, which is GAME-MINUTES, and was compared against
`12 * 3600` — a real-seconds shape asking for 43,200 of them, i.e. THIRTY
GAME-DAYS of unbroken starvation.  Measured, it reached 2,940 after three
game-days while the 20-mistake ladder was already at 13, so the death it
guards could not happen — on a field round 41 deliberately PERSISTED so
that quit-cycling couldn't dodge it.  The unit law's fourth instance, and
the warning for it sits twelve lines below the bug.

F2 (RULING, not fixed here) — the numbers behind it are pinned below so
the ruling starts from measurement: a full belly lasts ~5 GAME-DAYS, and
ordinary neglect kills at 3.5, so hunger cannot reach zero in a natural
life.  See CARE_AUDIT_2026_07_25.md §2.
"""
import pytest

from tuipet.pet import DAY_LENGTH, Pet
from tuipet.petbase import STARVE_DEATH_MIN


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    p.world_seconds = 8 * 60.0
    p.evo_blocked = True                  # isolate the body from the charts
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# ---- F1: the starvation clock ------------------------------------------

def test_the_starvation_clock_is_counted_in_the_bodys_own_minutes():
    """12 GAME-hours, the number its comment always claimed.  The old
    `12 * 3600` was 30 game-days: unreachable."""
    assert STARVE_DEATH_MIN == 12 * 60
    assert STARVE_DEATH_MIN < DAY_LENGTH          # inside a single game-day


def test_a_pet_held_at_an_empty_belly_actually_starves():
    p = _pet(hunger=0)
    died_at = None
    for i in range(int(DAY_LENGTH * 2)):
        p.tick(1.0)
        p.hunger = 0                              # hold it starving
        if p.dead:
            died_at = i
            break
    assert died_at is not None, "the starvation death still cannot fire"
    assert p.death_cause == "starvation"
    assert abs(died_at - STARVE_DEATH_MIN) <= 60  # ~12 game-hours


def test_a_belly_that_is_fed_resets_the_clock():
    p = _pet(hunger=0)
    for _ in range(300):
        p.tick(1.0)
        p.hunger = 0
    assert p._starve_t > 0
    p.hunger = 3                                  # a meal
    p.tick(1.0)
    assert p._starve_t == 0.0


def test_a_sleeping_pet_does_not_starve_in_its_sleep():
    """Awake-only, like the hunger call itself."""
    p = _pet(hunger=0)
    p.world_seconds = 23 * 60.0
    p._fall_asleep()
    before = getattr(p, "_starve_t", 0.0)
    for _ in range(200):
        p.tick(1.0)
        p.hunger = 0
        if not p.asleep:
            break
    assert getattr(p, "_starve_t", 0.0) == before


# ---- F2: the measurement the ruling needs ------------------------------

def test_the_hunger_clock_is_what_the_board_says_it_is():
    """These are the numbers CARE_AUDIT §2 asks Joel to rule on.  If they
    move, the board's argument moved with them and needs rereading."""
    p = _pet()
    lapse = p._hunger_interval
    full_belly = 32 * lapse                       # 4 hearts x 8 lapses
    assert lapse == pytest.approx(225, abs=1)
    assert full_belly / DAY_LENGTH == pytest.approx(5.0, abs=0.2)


def test_ordinary_neglect_still_kills_before_the_belly_empties():
    """The consequence, measured end to end: a pet nobody feeds dies of the
    mistake ladder while it still has hearts left.  This is the pin that
    fails the day the hunger pace is retuned -- which is the point."""
    p = _pet()
    for _ in range(int(DAY_LENGTH * 8)):
        p.tick(1.0)
        if p.dead:
            break
    assert p.dead
    assert p.death_cause != "starvation"
    assert p.hunger > 0, "the belly emptied after all -- retune the board"


# ---- the care loop's own invariants ------------------------------------

def test_an_attentive_player_keeps_a_spotless_pet():
    p = _pet()
    for _ in range(int(DAY_LENGTH * 2)):
        p.tick(1.0)
        if p.hunger <= 1 and not p.asleep:
            p.feed_meat()
        if p.poop:
            p.clean()
        if p.sick:
            p.feed_pill()
        if p.injured:
            p.heal_bandage()
        if p.asleep and p.lights:
            p.toggle_lights()
        elif not p.asleep and not p.lights:
            p.toggle_lights()
    assert not p.dead and p.care_mistakes == 0


@pytest.mark.parametrize("days", [1, 3])
def test_the_meters_never_leave_their_rails(days):
    p = _pet()
    for _ in range(int(DAY_LENGTH * days)):
        p.tick(1.0)
        assert 0 <= p.hunger <= 4
        assert 0 <= p.strength <= 4
        assert p.energy <= p.max_energy
        assert p.weight >= 1
        assert p.care_mistakes >= 0
        assert len(p.poop_sizes) == p.poop
        if p.dead:
            break


def test_every_care_mistake_has_exactly_one_source():
    """The four doors that book a slip, each fired in isolation."""
    # an ignored hunger call
    p = _pet(hunger=0)
    for _ in range(int(DAY_LENGTH)):
        p.tick(1.0)
        p.hunger = 0
        if p.care_mistakes:
            break
    assert p.care_mistakes == 1
    # filth left standing
    q = _pet(poop=4, poop_sizes=[1, 1, 1, 1])
    for _ in range(int(DAY_LENGTH)):
        q.tick(1.0)
        if q.care_mistakes:
            break
    assert q.care_mistakes >= 1
    # stuffing a full belly
    r = _pet(hunger=4)
    before = r.care_mistakes
    r.feed_meat()
    assert r.care_mistakes == before + 1


def test_the_death_ladder_holds_at_both_ends():
    p = _pet(care_mistakes=19)
    p.tick(1.0)
    assert not p.dead
    p.care_mistakes = 20
    p.tick(1.0)
    assert p.dead and p.death_cause == "neglect"
    q = _pet(stage="Ultimate", care_mistakes=5)
    q.stage_seconds = q.LATE_STAGE_WINDOW + 1
    q.tick(1.0)
    assert q.dead and q.death_cause == "frailty"
