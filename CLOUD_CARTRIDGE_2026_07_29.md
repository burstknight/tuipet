# THE CARTRIDGE — cloud saves, one device at a time (SHIPPED v0.5.313, 2026-07-29)

> STATUS: **LIVE** — client v0.5.313 on PyPI, server deployed to
> `/opt/tuipet-lobby/` (pm2 `tuipet-lobby`), smoke-verified against production.
> This file is the design record and the incident history behind it. The code
> is the single source; where they disagree, the code wins.

## Why this exists

Cloud saves resolved conflicts by wall clock — newest push wins. That is
correct only if every copy of the save descends from the same pet. Twice it
didn't:

- **2026-07-27, the gen-10 loss.** A desktop holding a gen-3 fork relaunched
  and legitimately out-stamped the phone's gen-10 pet.
- **2026-07-29, the GPD fork war.** joelgpd held a stale gen-1 Greymon save;
  every launch re-stamped it over the real BlitzGreymon Mega. Twice in one
  night, including after the cloud record was cleaned by hand.

A guard stack (`PULL_REACHED`, divergence detection, rescue copies, a
Rescued-pets page) shipped in **v0.5.290-293** and was **removed by v0.5.294**
(commit `77a7d54`, "CLOUD SAVE IS BACK TO PLAIN AND SIMPLE") — undocumented at
the time, which is why the second incident looked impossible. **Never trust a
"guards shipped" note without grepping the current tree.**

No timestamp heuristic can answer the actual question — *which copy did you
mean?* — so the cartridge asks the player, once, at the only moment it matters.

## The model

The pet is a cartridge, checked out to exactly **one device** per account.

- The **holder** device plays with zero new friction: no prompts, no changes.
- A **non-holder** gets one terminal question at launch:
  `Your pet is on phone. Take it onto this device? [y/N]`
  - **y** → the server moves holdership here, this device pulls the real save.
  - **n** → prints where the pet lives and exits 0. Nothing local is touched.
- The server **drops any save push from a non-holder**, however fresh its
  timestamp. Enforcement is server-side; a stale or hostile client cannot
  argue its way past it.

## Wire protocol

| direction | message | meaning |
|-----------|---------|---------|
| client → | `login` + `device`, `dlabel` | every sync login names its device (uuid4 hex16 minted into settings; label = `phone` on Termux, `iPhone` on iOS, else hostname) |
| → client | `welcome` + `holder` | `{"device","label","ts"}` or `null` when unheld |
| client → | `take` | the player's explicit yes |
| → client | `holder` + `ok`, `save` | `ok:false` for legacy clients (no device id) |
| → client | `save_ack` + `why` | `holder` (non-holder push), `lease` (stale session), `invalid` (failed validation) |

Server state: `HOLDERS` (`holders.json`, path via `TUIPET_HOLDERS`), keyed by
lowercased account → `{device, label, ts}`. Like `SAVES`/`RAID`/`LADDER`, it is
loaded **in memory at module load**, so editing the file on the box requires a
stop / edit / start, not a live edit + restart.

Order in the `save` handler matters: **the holder check runs before the lease
check.** The lease decides which of the holder's own sessions writes; the
holder decides whether this device may write at all.

## Client flow (v0.5.313)

- `cloudsync.gate()` → `('ok'|'badpw'|'offline', save, holder|None)`;
  `probe()` stays a 2-tuple for the account switcher; `take()` sends `take`
  and waits for `holder`.
- `app.main()` runs the boot gate before any sim starts. `EOFError`/`OSError`
  on the prompt is treated as no answer, so headless runs never hang.
- `persistence.holder_cache()` caches the last known verdict in settings.
  `_push_cloud` and `_flush_cloud_on_quit` return early when it is `False` —
  the quit flush was the GPD war's second wound.
- Offline **and** cached non-holder = spectator exit: a device that knows the
  pet is elsewhere and can't ask to take it must not play a fork forward.
- `persistence.rescue_copy()` snapshots the local save (`save.rescue.<stamp>.json`,
  newest 5 kept) before any pull replaces it. A wrong answer is undoable.
- `push_save()` **must** probe before pushing: an unreachable cloud writes
  nothing; an empty cloud returns `('ok', None)` so first uploads still flow.
- `net.SyncClient._login_msg` carries `device`/`dlabel` too — the in-session
  autosave pusher has to pass the same holder check the boot path does.

## Migration

The first device that syncs an **unheld** account auto-claims it
(`login`, `sync_only`). Existing players therefore never see the question on
the device they already play; other devices meet it on their next launch.
Legacy clients (older versions, no device id) can still pull, but can neither
claim nor push to a held account.

## Follow-up: the silent drop (v0.5.315, 2026-07-30)

The guard worked; the *telling* didn't. Joel opened tuipet on his PC, the pet
didn't come over, and nothing on screen explained why. Diagnosis from the
server log: the PC pushed every 10s for five minutes and every push was
dropped `why=holder` — the real pet (13,145 bits) was never at risk.

Two defects behind the silence:

1. **`net.py` `_handle` matched only `("lease", "invalid")`.** The new `holder`
   verdict fell through, set no flag, and the app's warn pass had nothing to
   read. A protection nobody surfaces is indistinguishable from a broken
   feature. Fixed: `SyncClient.not_holder` + `app._warn_if_not_holder()`, which
   flips `set_holder_cache(False)` (the thing that actually stops the pushes),
   beeps, and names the holder device once per session.
2. **The boot gate used the 3s `_TIMEOUT`.** The one call that decides whether
   the take-question is asked was the least patient in the app, and a
   just-logged-in machine's cold DNS + TLS lost that race — while the session
   client's retry loop connected fine seconds later. The log proves it: a
   `sync_only` session login with no gate login before it. Fixed:
   `BOOT_TIMEOUT = 12.0` plus one retry on `offline`.

The server also now includes `holder` in a `why=holder` ack, so the client can
say *where* the pet is rather than only that something failed.

**Rule this produced:** a new reason code on the wire is unshipped until a
client branch matches it *and* the player is told. Grep every consumer of the
field, then trace the flag to something the player actually sees.

Taking the pet remains a **relaunch** door on purpose — the boot gate exists so
the app never has to reload a pet mid-session.

## Known limits (flagged, not bugs)

- Declining the question **exits**; there is no pet-less spectator lobby yet.
- Account-switching *onto* a held account from a non-holding device refuses —
  parking would push a fork. Honest, but blunt.

## Tests

`tests/test_sync.py`, against a real `server.py` subprocess
(`TUIPET_HOLDERS` in the fixture env), with `_as_device()` monkeypatching
`persistence.device_id`/`device_label`: first-claim, non-holder drop **with a
fresher stamp**, take moves holdership + locks out the zombie, legacy raw-wire
client (`why == "holder"`), blind-push refusal against a dead port, and
rescue-before-replace.

Production smoke (throwaway account, 2026-07-29): claim → push `True` →
non-holder push with fresher stamp `False` → take `True` → push after take
`True`.

## Files

`src/tuipet/cloudsync.py` (rewritten), `src/tuipet/persistence.py` (device id,
label, holder cache, rescue copies), `src/tuipet/app.py` (boot gate + push
gates), `src/tuipet/net.py` (device on the session login),
`server/server.py` (holders ledger, `take`, holder-first save check),
`tests/test_sync.py`.
