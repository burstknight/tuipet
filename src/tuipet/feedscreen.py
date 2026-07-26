"""Feed menu — the classic care picker in the SHOP layout language (redo,
Joel 2026-07-26: "make it look like all the other menus, show the sprites
when selected in a box, like shops look").  The pixel-art LCD picker (canon
decompile Rn glyph stack, then the bandage column) left with this redo —
one layout language per screen family: header, selected-item dossier box
(menu.icon_info, the icon cell every icon view shares), scrolling row list.

The classic feed stack itself is unchanged: MEAT fills a hunger heart
(+1 weight, refused at a full belly); the PILL cures an active sickness,
restores a strength heart, +7 energy, +5 weight; the BANDAGE patches a
battle injury.  All are free and infinite — the richer consumables live in
the BAG as shop items.

Dossier art holds each item's IDENTITY law: the meat shows the DVPet f:0
Meat rip (the strip the eat fx chews through); the pill shows ITS OWN
glyph (DSprite SYMBOL_PILL — the picked pill IS the eaten pill, pill-anim
fix 2026-07-20; there is no matching DVPet rip); the bandage shows the
i:80 roll (frame 0 of the strip the Bandaging show applies).
"""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM, ACCENT, POS  # noqa: F401  (theme.apply propagation)

# --- the pill's own art (DSprite SYMBOL_PILL / SYMBOL_HALF_PILL) ------------
PILL = ["00001110",
        "00010011",
        "00101111",
        "01011111",
        "10001110",
        "10000100",
        "10001000",
        "01110000"]

# the half-eaten pill: a bite taken out of the top
HALF_PILL = ["00000000",
             "00000000",
             "00000000",
             "01100000",
             "11010000",
             "10101000",
             "10011000",
             "01110000"]

# The pill is EATEN through ITS OWN glyph, the DSprite way
# (EatingAnimationScreen.setSprites(SYMBOL_PILL, SYMBOL_HALF_PILL,
# SYMBOL_EMPTY) -- main.cpp case 1): full -> half -> gone, so the picked
# pill IS the eaten pill (pill-anim fix 2026-07-20; the old DVPet f:41
# capsule never matched the picker).  The eat fx pulls this via the
# "sym:pill" icon key; the None tail is the eaten-away frame blit()
# tolerates.  DSprite's pill has ONLY these two art frames, so the strip is
# paced full -> half -> half -> gone across the eat fx's food_beats
# (2-frame rebalance, Joel 2026-07-20).
PILL_FRAMES = [PILL, HALF_PILL, HALF_PILL, None]

# R3 (2026-07-23, Joel "make them symmetric"): the BANDAGE beside the Pill
# as a free, always-available cure.  Two ailments, two care BUTTONS --
# ailments cost time, not bits.
ROWS_MENU = [("meat", "Meat"), ("pill", "Pill"), ("bandage", "Bandage")]

VIS = 6   # list rows: header 2 + dossier 4 + list 6 == the 12-row LCD


class FeedPanel:
    def __init__(self, pet):
        self.pet = pet
        # an AILING pet opens on its own cure: the HUD nag names it, and
        # meat would only be refused -- don't make the cure extra presses in
        # the most-repeated care loop (QOL sweep 2026-07-23).  Sick outranks
        # hurt when both are true: sickness is the older, louder alarm.
        self.cursor = 1 if pet.sick else (2 if pet.is_injured() else 0)
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("↑↓", "pick"), ("ENTER", "feed"), ("ESC", "out"))

    def key(self, k):
        if k in ("up", "k", "down", "j"):
            step = -1 if k in ("up", "k") else 1
            self.cursor = (self.cursor + step) % len(ROWS_MENU)
        elif k in ("enter", "space"):
            kind, label = ROWS_MENU[self.cursor]
            if kind == "meat":
                msg = self.pet.feed_meat()
                # the staple meat eats through the DVPet f:0 Meat strip
                # (art truth; the eat ACTION itself is the source's)
                if self.pet.anim == "eat":
                    return ("done", ("fed", {"key": "f:0", "name": "Meat"}, msg))
                if "full" in msg:
                    return ("done", ("full", {"key": "f:0", "name": "Meat"}, msg))
                return ("done", ("refused", {"key": "f:0", "name": "Meat"}, msg))
            if kind == "bandage":
                msg = self.pet.heal_bandage()
                from .petbase import _Refused
                if isinstance(msg, _Refused) or "patched" not in str(msg):
                    return ("done", ("refused", {"key": "i:80",
                                                 "name": "Bandage"}, str(msg)))
                # the bandage is WORN, not eaten: its own canon Bandaging
                # script plays (items.csv i:80 AnimationType)
                return ("done", ("bandaged", {"key": "i:80",
                                              "name": "Bandage"}, str(msg)))
            was_sick = self.pet.sick
            msg = self.pet.feed_pill()
            if self.pet.anim == "eat":
                out = "Cured!" if was_sick else "A tonic — strength and pep."
                return ("done", ("healed", {"key": "sym:pill", "name": "Pill"}, out))
            return ("done", ("refused", {"key": "sym:pill", "name": "Pill"}, msg))
        elif k in ("escape", "f"):
            return ("done", None)
        return None

    def _icon(self, kind):
        """The dossier cell, per the identity law in the module docstring."""
        from . import data
        if kind == "pill":
            return menu.icon_cell(PILL)
        fr = data.load_icons().get({"meat": "f:0", "bandage": "i:80"}[kind])
        return menu.icon_cell(fr[0]) if fr else [" " * menu.IC_W] * menu.IC_ROWS

    def _info(self, kind):
        """The four dossier rows -- true effects, and the refusal gate
        visible BEFORE the pick (the shop-dossier grammar; the gates are
        petcare's own: canon gates 2026-07-18)."""
        from .petcare import FULL_HUNGER
        p = self.pet
        if kind == "meat":
            gate = ""
            if p.sick:
                gate = "refused — sick: the Pill"
            elif p.poop:
                gate = "refused — clean first (C)"
            elif p.hunger >= FULL_HUNGER:
                gate = "refused — belly is full"
            return ["Meat", "free · infinite",
                    "hunger +1 · weight +1", gate or "the staple"]
        if kind == "pill":
            gate = ""
            if p.poop:
                gate = "refused — clean first (C)"
            elif (not p.sick and p.strength >= 4
                  and p.energy >= p.max_energy):
                gate = "refused — doesn't need it"
            return ["Pill", "cures sickness · effort +1",
                    "energy +7 · weight +5", gate or "free · infinite"]
        gate = "" if p.is_injured() else "refused — not injured"
        return ["Bandage", "free · infinite",
                "patches the battle injury", gate or "worn, not eaten"]

    def text(self):
        out = menu.header("FEED")
        kind, _label = ROWS_MENU[self.cursor]
        menu.icon_info(out, self._icon(kind), self._info(kind))
        fmt = lambda e, i: "%-29s %6s" % (e[1], "free")
        self.cursor = menu.list_window(out, ROWS_MENU, self.cursor, VIS, fmt)
        out.right_crop(1)          # the last row sheds its newline (the
        #                            footer convention: 12 rows, no 13th
        #                            empty split element)
        return out
