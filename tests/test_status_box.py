"""The STATUS box budget: #stats is physically 26x16 content (CSS 30x18
border-box).  Every painter must fit -- the status-box audit 2026-07-04 found
the DNA card 28 wide (its hint line wrapped mid-box) and raw-minutes ages
('4325m40s').  Same lesson as the LCD box-clip: pixels aren't the box."""
import re

from tuipet.pet import Pet

CARD_W, CARD_H = 26, 16


def _vis(line):
    return len(re.sub(r"\[/?[^\[\]]*\]", "", line))


from tuipet.app import Stats


class _FakeStats(Stats):
    """A Stats with the Textual plumbing stubbed out (never mounted)."""
    def __init__(self): self.txt = ""
    def update(self, t): self.txt = str(t)
    @property
    def border_subtitle(self): return ""
    @border_subtitle.setter
    def border_subtitle(self, v): pass


def _fits(fake, tag):
    lines = fake.txt.split("\n")
    assert len(lines) <= CARD_H, f"{tag}: {len(lines)} lines overflow the card"
    w = max(_vis(l) for l in lines)
    assert w <= CARD_W, f"{tag}: {w} cols overflow the card"


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.age_seconds = 3 * 86400 + 7000       # an older pet: worst-case widths
    p.bits = 99999
    p.dp = 3
    p.poop = 2
    p.sick = True
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_main_egg_and_grave_cards_fit_and_read_compact_ages():
    fake = _FakeStats()
    p = _pet()
    Stats.paint(fake, p)
    _fits(fake, "main")
    assert "3d01h" in fake.txt                  # compact age, not 4436m40s
    assert "◆◆◆" in fake.txt                    # the DP meter: pips on its own row
    assert "Care" in fake.txt                   # the evolution driver, no longer buried
    assert "Power" not in fake.txt              # the ledger lives on the DigiCore now
    assert "HP " not in fake.txt                # the classic trained-HP left with it
    Stats.paint(fake, Pet.new_egg(egg_type=1))
    _fits(fake, "egg")
    dead = _pet(dead=True)
    Stats.paint(fake, dead)
    _fits(fake, "grave")
    assert "Lived    3d01h" in fake.txt


# ---- card audit 2026-07-24: word-wrap, not char-slice --------------------

def test_wrap_never_splits_a_word_and_caps_with_ellipsis():
    """The helper the Options card now uses: word boundaries only, a lone
    over-wide token still breaks (never overruns the card), and past the cap
    the last line ends in an ellipsis rather than dropping the tail silently."""
    from tuipet import statusbox as sb
    out = sb.wrap("A flips launch auto-install", 3)
    assert all(len(l) <= CARD_W for l in out)
    assert "auto-install" in out                 # kept whole, not "auto-instal"
    out = sb.wrap(" ".join(["word"] * 15), 2)      # 15 words -> 3 lines, capped
    assert len(out) == 2 and out[-1].endswith("…")
    assert all(len(l) <= CARD_W for l in sb.wrap("x" * 40, 3))  # lone giant token


def test_options_card_wraps_every_desc_and_the_update_msg():
    """Joel "words are getting cut off": the Options card sliced desc[:26] /
    [26:52] and msg[:26] -- cutting 'auto-install' mid-glyph and dropping the
    restart prompt's tail.  Now every option's desc and the longest update
    message fit the card with NO word lost."""
    import re
    from tuipet import statusbox, optionsscreen as _opts

    class _Mode:
        def __init__(self, cursor, msg): self.cursor, self.msg = cursor, msg

    class _App:
        def __init__(self, mode): self.mode, self.stats_w = mode, _FakeStats()

    longest = "Updated! Restart now?  ENTER restarts · ESC later"
    for i, row in enumerate(_opts._ROWS):
        app = _App(_Mode(i, longest))
        statusbox.options(app)
        _fits(app.stats_w, f"options[{row}]")
        shown = re.sub(r"\[/?[^\[\]]*\]", "", app.stats_w.txt)
        for word in re.findall(r"[A-Za-z]+", _opts._DESC.get(row, "") + " " + longest):
            assert word in shown, f"{row}: lost the word {word!r}"
