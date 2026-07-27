"""THE RESCUE PAGE (2026-07-27).

A cloud pull writes save.rescue.<stamp>.json before it replaces the pet, so
a wrong pull is undoable -- but the copies were only reachable from a shell,
which on a phone is no recovery at all.  Joel lost a pet that way and could
not run a single command to get it back ("not an option").  Options ->
Rescued pets is the door; these are its pins.
"""
import json
import os
import time

from tuipet import persistence
from tuipet.optionsscreen import OptionsPanel, RescuePanel
from tuipet.pet import Pet


def _pet(num=297, gen=1, name="BlitzGreymon"):
    p = Pet(num=num, stage="Mega", attribute="Vaccine", obedience=500)
    p.name, p.generation, p.world_seconds = name, gen, 600.0
    return p


def _panel(pet):
    return OptionsPanel(pet, sound_get=lambda: True, sound_toggle=lambda: None)


def test_a_pull_leaves_a_rescue_the_page_can_list():
    persistence.save(_pet())                       # the pet this device played
    persistence.rescue_copy()                      # ...as a pull would rescue it
    rows = persistence.rescue_list()
    assert len(rows) == 1
    fn, blob = rows[0]
    assert fn.startswith("save.rescue.") and blob["num"] == 297
    pan = RescuePanel()
    assert "BlitzGreymon" in pan.text().plain
    assert "gen 1" in pan.text().plain


def test_restoring_puts_the_pet_back_and_outranks_the_cloud():
    persistence.save(_pet())                       # the Mega...
    persistence.rescue_copy()
    replaced = persistence.to_save_dict(_pet(num=283, gen=3, name="Plesiomon"))
    replaced["_saved_at"] = time.time() + 600      # ...and the pull that beat it
    persistence.write_save_dict(replaced)
    assert json.load(open(persistence.SAVE_PATH))["num"] == 283

    fn = persistence.rescue_list()[0][0]
    before = time.time()
    back = persistence.rescue_restore(fn)
    assert back["num"] == 297, "the rescued pet is not the one restored"
    live = json.load(open(persistence.SAVE_PATH))
    assert live["num"] == 297 and live["name"] == "BlitzGreymon"
    # stamped NOW: otherwise the cloud copy that replaced it is still newer
    # and the very next launch pulls it straight back over the top
    assert live["_saved_at"] >= before
    assert live["_saved_at"] > replaced["_saved_at"] - 600


def test_restoring_is_itself_undoable():
    """The pet you were playing is rescued before it is replaced."""
    persistence.save(_pet())
    persistence.rescue_copy()
    persistence.write_save_dict(
        persistence.to_save_dict(_pet(num=283, gen=3, name="Plesiomon")))
    persistence.rescue_restore(persistence.rescue_list()[0][0])
    pets = {b["num"] for _f, b in persistence.rescue_list()}
    assert 283 in pets, "the replaced pet left no way back"


def test_enter_on_a_rescue_restarts_so_the_pet_actually_loads():
    """The pet is read once at boot -- a restore that doesn't restart leaves
    the old pet on screen, autosaving straight back over the restored file."""
    persistence.save(_pet())
    persistence.rescue_copy()
    pan = _panel(_pet(num=283, gen=3, name="Plesiomon"))
    pan.cursor = _row_index("rescue")
    assert pan.key("enter") is None                 # opens the sub-page
    assert isinstance(pan.sub, RescuePanel)
    out = pan.key("enter")                          # ...restore the top row
    assert out == ("done", ("restart",)), out
    assert json.load(open(persistence.SAVE_PATH))["num"] == 297


def test_the_page_is_honest_when_there_is_nothing_to_restore():
    pan = RescuePanel()
    assert pan.rows == []
    assert "No rescued pets" in pan.text().plain
    assert pan.key("enter") is None                 # ...and ENTER can't misfire
    assert pan.key("escape") == ("done", None)
    pan2 = _panel(_pet())
    assert pan2._value("rescue") == "none"


def _row_index(name):
    from tuipet.optionsscreen import _ROWS
    return _ROWS.index(name)


def test_the_row_counts_what_is_waiting():
    persistence.save(_pet())
    persistence.rescue_copy()
    assert _panel(_pet())._value("rescue") == "1 saved"
    assert os.path.basename(persistence.rescue_list()[0][0]).endswith(".json")
