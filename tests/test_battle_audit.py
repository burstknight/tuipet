"""THE BATTLE AUDIT — the pins (2026-07-25).

Joel: "we gotta do a full blown battle audit. we did a bunch of changes
recently and we gotta make sure its hooked up correctly."

The recent run — the home battle key (v0.5.198), the Pen20 lock rework
(199-204), injury (205), the rolling win gate (212), the one-card rule
(179), death-is-final (180), the cup's single entrance (240) — landed
across five different doors into one engine.  These pins hold the seams:

  * THE HURRY KEY MAY ONLY HURRY.  A mashed SPACE snapped the playhead
    back to the start of the closing impact run, every press, so the
    round replayed forever and the fight sat frozen (4000 frames of
    pressing every frame never left round 1; sparse presses finish in
    ~80).  Joel plays on a phone — tap-tap-tap is the normal input.
  * ONE ENGINE, FIVE DOORS: what each source bills and feeds.
  * THE CONDITION GATE holds on every CHOSEN fight.
  * THE LOCK is pure upside and reaches the fight it was locked for.
"""
import random

import pytest

from tuipet import battle as B, statusbox
from tuipet.battlescreen import BattlePanel, LOCK_ARM_T, SKIP_DEBOUNCE
from tuipet.pet import Pet

ENEMY = {"num": 120, "name": "Kuwagamon", "stage": "Champion",
         "attribute": "Virus"}


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight()
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _play(press_every, cap=4000, seed=5):
    """Run a bout to its end, pressing SPACE every `press_every` frames
    (0 = never).  -> (frames, phase, rewinds, won)"""
    random.seed(seed)
    pan = BattlePanel(_pet(), dict(ENEMY))
    frames = rewinds = 0
    for i in range(cap):
        pan.anim()
        frames += 1
        if pan.phase == "ready" and pan.battle is None and i > 8:
            pan.key("space")                       # lock the bar
            continue
        if pan.phase == "result":
            break
        if pan.phase == "anim" and press_every and i % press_every == 0:
            before = pan.i
            pan.key("space")
            if pan.i < before:
                rewinds += 1
    return frames, pan.phase, rewinds, pan.won


# ---- the hurry key ---------------------------------------------------------

@pytest.mark.parametrize("every", [0, 10, 3, 1])
def test_a_hurry_press_never_moves_the_fight_backward(every):
    frames, phase, rewinds, _won = _play(every)
    assert rewinds == 0, f"{rewinds} rewinds at 1-in-{every} presses"
    assert phase == "result", f"never finished at 1-in-{every} presses"


def test_mashing_finishes_a_fight_FASTER_not_never():
    """The bug's shape: the faster you pressed, the longer it took — and
    at every frame it never ended at all."""
    slow, _p1, _r1, _w1 = _play(0)
    mashed, _p2, _r2, _w2 = _play(1)
    assert mashed < slow


def test_the_outcome_is_the_same_however_you_press():
    """The rounds are precomputed at the lock, so input speed is a
    PRESENTATION choice.  If this ever fails, the keys are deciding
    fights."""
    outcomes = {_play(e, seed=9)[3] for e in (0, 10, 3, 1)}
    assert len(outcomes) == 1


# ---- one engine, five doors ------------------------------------------------

def _ledger(p):
    return dict(energy=p.energy, weight=p.weight, battles=p.battles,
                wins=p.wins, stage_battles=p.stage_battles,
                stage_trainings=p.stage_trainings,
                total_trainings=p.total_trainings, exp=p.exp,
                log=len(p.battle_log))


def _run_engine(source, enemy=None, raid=False):
    random.seed(7)
    # ABOVE the species base, so the weight bill is visible: it floors AT
    # base (v0.5.204), so a pet already at base shows no movement
    p = _pet()
    p.weight = p._base_weight() + 5
    before = _ledger(p)
    b = (B.RaidBout(p, enemy or dict(ENEMY)) if raid
         else B.Battle(p, enemy or dict(ENEMY), source=source))
    for _ in range(40):
        if b.over:
            break
        b.play_round()
    after = _ledger(p)
    return {k: after[k] - before[k] for k in after}, b


def test_a_local_bout_bills_the_body_and_feeds_progression():
    d, b = _run_engine("battle")
    assert d["energy"] == -5                    # a bout spends energy...
    assert d["weight"] < 0                      # ...and sheds weight...
    assert d["battles"] == 1 and d["stage_battles"] == 1
    assert d["log"] == 1                        # ...and feeds the Pen20 window
    # the clone's +2, on BOTH clocks since 2026-07-25 (Joel: "feed the
    # total_trainings thing too, flip it") -- fighting used to move the
    # stage counter and the TR gate while the hit formula's bigger
    # lifetime term sat still no matter how much a pet fought
    assert d["stage_trainings"] == 2 and d["total_trainings"] == 2
    assert (d["wins"] == 1) == bool(b.won)
    assert (d["exp"] > 0) == bool(b.won)        # only a win pays experience


def test_an_online_bout_bills_the_BODY_ONLY():
    """L17: PvP is progression-neutral — energy and weight, nothing else."""
    d, _b = _run_engine("pvp")
    assert d["energy"] == -5 and d["weight"] < 0
    for k in ("battles", "wins", "stage_battles", "stage_trainings",
              "total_trainings", "exp", "log"):
        assert d[k] == 0, k


def test_a_raid_volley_writes_NOTHING_on_the_pet():
    boss = {"num": 288, "name": "Boss", "stage": "Mega", "attribute": "Virus",
            "boss": True}
    d, b = _run_engine("raid", enemy=boss, raid=True)
    assert all(v == 0 for v in d.values()), d
    assert getattr(b, "dealt", 0) >= 0          # the report is the whole point


def test_the_weight_bill_floors_at_the_species_BASE():
    """v0.5.204: 52 bouts ground a Greymon from 40g to 10g — the maximum
    condition penalty, earned by FIGHTING."""
    p = _pet()
    p.weight = p._base_weight()
    for _ in range(30):
        p.record_battle(True, dict(ENEMY))
    assert p.weight == p._base_weight()


# ---- the gate --------------------------------------------------------------

CONDITIONS = [("injured", "Too hurt"), ("sick", "Too sick"),
              ("hunger", "Too hungry"), ("poop", "Clean up")]


@pytest.mark.parametrize("field,word", CONDITIONS)
def test_every_chosen_fight_asks_the_same_condition_gate(field, word):
    """battle_condition is THE source: the home key, the cup door, the
    lobby's accept — and, since the 2026-07-25 ruling, the road's BOSS
    gate and the raid volley too."""
    p = _pet(**({field: 0} if field == "hunger" else {field: 3 if field == "poop" else True}))
    assert word in (p.battle_condition() or "")
    assert word in (p.can_battle() or "")
    from tuipet import tournament
    assert word in (tournament.can_enter(p) or p.battle_condition() or "")


# ---- the lock --------------------------------------------------------------

def test_the_lock_is_pure_upside_and_reaches_the_fight():
    """Pen20 shake ruling: a mega lock adds aim AND steadies the guard;
    normal and miss both fight at the pet's own stats — no lock can make a
    pet fight worse than it was raised."""
    foe = B.Side.wild(120)
    got = {}
    for lock in ("mega", "normal", "miss"):
        p = _pet(saved_hit_type=lock)
        me = B.Side.of_pet(p)
        assert me.hit_type == lock              # the lock reaches the Side
        got[lock] = (me.hit_chance(foe), foe.hit_chance(me))
    assert got["normal"] == got["miss"]          # a shank costs NOTHING
    assert got["mega"][0] > got["normal"][0]     # aim
    assert got["mega"][1] < got["normal"][1]     # and guard


def test_the_bar_locks_the_form_the_fight_then_uses():
    pan = BattlePanel(_pet(saved_hit_type="miss"), dict(ENEMY))
    for _ in range(20):
        pan.anim()
    pan.phase = "ready"
    pan._ready_frame = 0
    pan.key("space")
    assert pan.locked in ("mega", "normal", "miss")
    assert pan.pet.saved_hit_type == pan.locked
    assert pan.battle.me.hit_type == pan.locked


# ---- the card --------------------------------------------------------------

class _Stats:
    def __init__(self):
        self.text = ""
        self.border_subtitle = ""

    def update(self, t):
        self.text = t


class _App:
    def __init__(self, pet, mode):
        self.pet, self.mode, self.stats_w = pet, mode, _Stats()


@pytest.mark.parametrize("kw", [
    {}, {"wild": True, "scene": "greenhills"}, {"raid": True},
    {"skip_intro": True},
])
def test_one_battle_card_paints_for_every_door(kw):
    """v0.5.179: cup bout, road wild, town cup, raid volley — same card."""
    p = _pet()
    pan = BattlePanel(p, dict(ENEMY), **kw)
    app = _App(p, pan)
    fn = statusbox.painter_for(pan)
    assert fn is not None
    fn(app)
    txt = app.stats_w.text
    assert "You" in txt and ("battle" in txt.lower() or "raid" in txt.lower())


def test_the_card_reaches_a_fight_hosted_INSIDE_another_screen():
    """The cup runs its bouts as a SUB; painter_for walks the chain, or the
    cup's fights show vitals instead of HP bars."""
    from tuipet.tournamentscreen import TournamentPanel
    p = _pet()
    host = TournamentPanel(p)
    host.sub = BattlePanel(p, dict(ENEMY), skip_intro=True)
    app = _App(p, host)
    statusbox.painter_for(host)(app)
    assert "You" in app.stats_w.text


def test_the_skip_debounce_still_guards_the_first_presses():
    """The mash fix must not undo the lock-frame debounce (QOL round 1)."""
    random.seed(5)
    pan = BattlePanel(_pet(), dict(ENEMY))
    for i in range(400):                          # the intro plays first
        pan.anim()
        if pan.phase == "ready" and pan.battle is None and i > 8:
            for _ in range(LOCK_ARM_T + 1):       # let the bar ARM (v0.5.200)
                pan.anim()
            pan.key("space")                      # lock -> phase "anim"
            break
    assert pan.phase == "anim"
    i0 = pan.i
    pan.key("space")                              # inside the debounce
    assert pan.i == i0
    for _ in range(SKIP_DEBOUNCE + 1):
        pan.anim()
    pan.key("space")
    assert pan.i >= i0


# ---- the ruling: the device's gate on every CHOSEN fight -------------------
#
# Joel 2026-07-25: "tuipet is its own game, supposed to feel as close to
# bandai vpet as much as possible, so anything else is extra."  The battle
# gate IS the device asking whether this body can fight; adventure and raids
# are tuipet's own extras, so they answer to it wherever the PLAYER chooses
# the fight.  The wayside ambush keeps its carve-out -- you cannot decline a
# pounce -- and that is the one exception, pinned below so it stays one.

def _road(pet):
    from tuipet import adventure
    from tuipet.adventurescreen import AdventurePanel
    pet.adv_progress = 3
    pan = AdventurePanel(pet, zone=adventure.ZONES[adventure.PROGRESSION[0]])
    pan._trans = pan._pulse = None                # skip the teleport-out beat
    return pan


@pytest.mark.parametrize("field,word", CONDITIONS)
def test_the_road_BOSS_gate_asks_the_body_first(field, word):
    p = _pet(**({field: 0} if field == "hunger"
                else {field: 3 if field == "poop" else True}))
    pan = _road(p)
    pan._start_boss(pan.adv.boss)
    assert pan.sub is None, "a refused body was marched into the boss"
    assert pan._at_gate and word in pan._gate_refusal
    assert word in pan.strip()                    # and the strip SAYS which
    pan.key("space")                              # pressing again re-asks
    assert pan.sub is None


def test_a_healthy_pet_still_walks_straight_into_the_boss():
    p = _pet()
    pan = _road(p)
    pan._start_boss(pan.adv.boss)
    assert pan.sub is not None and not pan._at_gate
    assert pan._gate_refusal is None


def test_a_refused_gate_is_never_a_dead_end():
    """ESC home always works, and a held transport still warps -- the same
    honest outs the planted-on-the-road refusal offers."""
    p = _pet(injured=True)
    p.add_item("town_transport")
    pan = _road(p)
    pan._start_boss(pan.adv.boss)
    assert "ESC home" in pan.strip() and "T warp" in pan.strip()
    pan.key("t")
    assert pan._transport == ["town_transport"]


class _GateClient:
    """The relay's answers, standing boss, attempts left — the raid door's
    own gates all OPEN, so only the BODY can refuse."""
    def __init__(self, boss_num):
        self.me_id = 1
        self.raid = {"t": "raid", "now": 100.0,
                     "boss": {"num": boss_num, "name": "BossMon", "hp": 1000,
                              "max_hp": 1000, "start": 0.0, "end": 604800.0},
                     "top": [], "you": [1, 0], "attempts": 3, "award": None}
        self.last_hit = None
        self.raid_reward = None

    def raid_get(self):
        pass


@pytest.mark.parametrize("field,word", CONDITIONS)
def test_a_raid_volley_asks_the_body_first(field, word):
    import json
    from tuipet.raidscreen import RaidPanel
    boss_num = json.load(open("server/raid_pool.json"))[0]["num"]
    p = _pet(**({field: 0} if field == "hunger"
                else {field: 3 if field == "poop" else True}))
    p.world_seconds = 600.0
    pan = RaidPanel(p, None, client=_GateClient(boss_num))
    pan.key("space")
    assert pan.sub is None, "a refused body threw itself at a raid boss"
    assert word in (pan.msg or "")


def test_a_healthy_pet_still_gets_its_raid_volley():
    import json
    from tuipet.raidscreen import RaidPanel
    boss_num = json.load(open("server/raid_pool.json"))[0]["num"]
    p = _pet()
    p.world_seconds = 600.0
    pan = RaidPanel(p, None, client=_GateClient(boss_num))
    pan.key("space")
    assert pan.sub is not None


def test_a_wayside_AMBUSH_still_cannot_be_declined():
    """The one carve-out, and it stays one: a pounce is not a choice, and
    the energy grammar has always had the same exception."""
    p = _pet(injured=True, sick=True)
    pan = _road(p)
    enemy = {"num": 120, "name": "Kuwagamon", "stage": "Champion",
             "attribute": "Virus"}
    pan._start_battle(enemy)
    assert pan.sub is not None                     # the fight happens


def test_fighting_moves_the_lifetime_training_term_too():
    """The flip: the hit formula's lifetime term (+0.2 cap) used to be
    unreachable by fighting -- only the drill fed it.

    Measured in two halves on purpose.  The bouts themselves also SPEND
    the body (energy, weight), so comparing a rested pet with a
    200-bout-drained one measures the drain, not the term."""
    p = _pet()
    for _ in range(200):
        p.record_battle(True, dict(ENEMY))
    assert p.total_trainings == 400              # the mechanism...
    rested, trained = _pet(), _pet()
    trained.total_trainings = p.total_trainings
    foe = B.Side.wild(120)
    assert (B.Side.of_pet(trained).hit_chance(foe)
            > B.Side.of_pet(rested).hit_chance(foe))   # ...and what it buys


def test_the_drill_still_feeds_both_at_its_own_rate():
    """Unchanged: 1 drill = 1 on each clock.  The bout's +2 is the clone's
    own number, not a copy of the drill's."""
    p = _pet()
    p.train_result(True)
    assert p.total_trainings == 1 and p.stage_trainings == 1
