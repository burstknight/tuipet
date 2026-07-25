# CARE AUDIT — the loop the whole game is made of (2026-07-25)

Joel: "lets do a full blown care audit next."

Scope: the body tick — hunger, calories, weight, effort, filth, sleep,
sickness, injury, the care-mistake economy and the deaths it feeds.  Method
as before: **live the days.**  Real ticks, three regimes, every meter held
against its rails on every tick.

---

## 1. F1 — THE STARVATION DEATH COULD NEVER FIRE  ✅ FIXED

```python
self._starve_t += dt                      # dt is GAME-MINUTES
if self._starve_t >= 12 * 3600:           # ...compared to a real-seconds shape
    self._die("starvation")
```

43,200 game-minutes is **thirty game-days of unbroken starvation**.
Measured: after three game-days held at an empty belly the clock stood at
2,940 while the 20-mistake ladder was already at 13 — so the death it
guards could not happen, ever.

Two things make it a bug rather than a dormant idea: the comment says
"empty hunger 12h → death", and round 41 (F8) deliberately **persisted**
`_starve_t` so quit-cycling couldn't dodge it.  Nobody persists a clock
that cannot fire.

It is **the unit law's fourth instance** (after the vitamin guard, the
fidget cadence and the Grow Capsule) — and the warning for it sits twelve
lines below the bug in the same function.  The number is now
`STARVE_DEATH_MIN = 12 * 60`, on the body's own clock, the same rescale
`FILTH_SICK_BOUND` took ("12000 real-min → /60 game scale").

Measured after the fix: a pet **held** at an empty belly dies at exactly 12
game-hours, cause `starvation`, with 1 care mistake.  A fed belly resets
the clock; a sleeping pet does not starve in its sleep (awake-only, like
the hunger call).  **An attentive player is untouched** — 0 mistakes over
three game-days, no breaches.

## 2. F2 — HUNGER WAS TOO SLOW TO MATTER  ✅ RULED + RETUNED

While measuring F1 I had to answer "how long until a belly is empty?", and
the answer is the bigger finding:

| the hunger clock | game-min | game-days | real play |
|---|---|---|---|
| one calorie lapse | 225 | 0.16 | 4 min |
| one hunger heart (8 lapses) | 1,800 | 1.2 | 30 min |
| **a full belly (4 hearts)** | **7,200** | **5.0** | **2.0 hours** |

Against that, measured deaths by neglect:

- pure neglect (never fed, never cleaned): dies at **3.5 game-days**
- tidy but never fed: dies at **4.6 game-days**

**The pet dies two to three game-days before its belly can empty.**  So in
a natural life, hunger never reaches zero — and everything downstream of an
empty belly is unreachable:

- the **hunger call** (the `!`, the alarm, the care mistake),
- **"Too hungry to fight"** and **"Too hungry to train"**,
- the **starvation death**, even after F1.

Which means: **feeding is optional.**  A pet you never feed once dies of
filth and lights, not of hunger, with hearts still on the meter.

For a game whose whole point is a Bandai V-Pet — where you feed the thing
several times a device-day — that reads wrong.  But the constants are
labelled *"tuipet's tuned pace"* and *"keep ~1800s per hunger heart"*, so
this is a **balance ruling, not a unit slip**, and it is yours.

> ### ✅ RULED — Joel, same day: "yeah retune the hunger, do it"
>
> `CALORIE_DECAY_SEC` is now **tied to the day itself** rather than to a
> loose number: `DAY_MINUTES / (FULL_HUNGER × 2 × CALORIE_LIMIT)` = 45, so
> four hearts × eight lapses is exactly one game-day and the scale can
> never drift out of the day again.
>
> | | before | after |
> |---|---|---|
> | one hunger heart | 1.2 game-days (30 real min) | **0.25 game-days (6 real min)** |
> | a full belly | 5.0 game-days (2 real hours) | **1.0 game-day (24 real min)** |
> | a pet nobody feeds | died at 3.5 days of *neglect*, hearts left | **belly empties at 1.4, starves at 1.9** |
> | an attentive player | 0 mistakes | **0 mistakes, ~3 meals a game-day, never sees an empty belly** |
>
> So the whole chain downstream of an empty belly is live for the first
> time: the hunger call and its `!`, both "too hungry" refusals, and F1's
> starvation death — which is now what actually kills a neglected pet,
> rather than a clock that could never run.
>
> **The sibling clocks were NOT touched** — poop still comes every 1.9
> game-days and an effort heart every 2.1.  They are tuned to the same
> old scale and now look slow beside hunger; that is the next ruling, not
> this one.  (Worth knowing for it: the effort gauge has its own call, so
> a pet nobody drills books slips exactly like a pet nobody feeds.)

## 3. HELD UNDER LOAD

- **The meters never leave their rails** across every regime and day: hunger
  and effort 0..4, energy never over max, weight never under 1, mistakes
  never negative, and the poop pile count always equal to its size list.
- **All four mistake sources fire, exactly once each**: an ignored hunger
  call, filth left standing, lights burning at bedtime, and stuffing a full
  belly.
- **The death ladder holds at both ends**: 19 mistakes lives, 20 dies of
  `neglect`; a late-window Ultimate at 5 dies of `frailty` (the Pen20
  contract).
- **An attentive player keeps a spotless pet** — two game-days of real
  feeding, cleaning, lights and cures leave zero mistakes.

## 4. SHIPPED

- **v0.5.256** — F1, the starvation clock, plus `tests/test_care_audit.py`
  (11 pins).  Suite 2115 → 2126.
- **v0.5.257** — F2 ruled and retuned: a full belly is one game-day.  The
  pins that recorded the broken numbers were superseded in place, which is
  exactly what they were written for.  Suite 2126 → 2127.
