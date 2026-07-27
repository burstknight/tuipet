"""Blocking cloud-save helpers for the launch/quit edges.

The pet save lives on the lobby server keyed by account (see server.py). To make
a pet follow you across devices we:
  * pull synchronously at startup, BEFORE the pet is loaded, and mirror a newer
    cloud save down to the local file — so the normal load path just picks it up
    (no mid-session pet swapping);
  * push synchronously on quit so the final state is captured.
During the session the app pushes incrementally via net.SyncClient (autosave).

Everything here is fail-soft: offline / bad password / timeout simply returns
without syncing, so the game always runs.
"""
from __future__ import annotations
import json
import time

from . import persistence

_TIMEOUT = 3.0

# The app-launch stamp: every sync login carries it, and the server grants the
# save lease only to the NEWEST launch — so a backgrounded device's reconnect
# can't steal save ownership back from the session the player actually opened.
BOOT = time.time()

# Did the startup pull actually reach the cloud and read what it holds?
#
# push_save (the quit flush) has always compared timestamps first, on the
# stated rule that "a device that missed its startup pull must not stomp a
# newer cloud save".  The SESSION pusher (net.SyncClient, every autosave)
# never learned that rule: it sends unconditionally and the server is
# last-write-wins, so a launch whose pull timed out spent the whole session
# overwriting the account's real save with this device's stale pet.  That is
# how a desktop's gen-3 replaced a phone's gen-10 (2026-07-27).  False here
# holds the session pusher back; the quit flush still runs, guarded by its
# own timestamp compare, so a genuinely newer pet still reaches the cloud.
PULL_REACHED = True
# ...and if it was held back because the cloud holds a DIFFERENT pet rather
# than because the cloud was unreachable, so the warning can say which.
DIVERGED = False


def _connect(uri, timeout):
    # imported lazily so a missing optional dep never blocks startup
    from websockets.sync.client import connect
    return connect(uri, open_timeout=timeout, close_timeout=1)


def pull_save(uri, name, pw, timeout=_TIMEOUT):
    """Return the account's stored cloud save dict, or None. Never raises."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps({"t": "login", "name": name, "pw": pw,
                                "sync_only": True, "boot": BOOT}))
            for _ in range(5):                       # welcome is the first/early frame
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "welcome":
                    return m.get("save")
                if m.get("t") == "login_failed":
                    return None
    except Exception:
        return None
    return None


def probe(uri, name, pw, timeout=_TIMEOUT):
    """Login check for the account switcher: ('ok', save_or_None) on a welcome
    (an unknown name is CREATED by the server, like the first-launch flow),
    ('badpw', None) when the server rejects the login — pull_save can't tell
    that apart from no-save, and switching onto a typo'd password would
    silently strand the player on a fresh start — ('offline', None) when the
    lobby can't be reached. Never raises."""
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps({"t": "login", "name": name, "pw": pw,
                                "sync_only": True, "boot": BOOT}))
            for _ in range(5):                       # welcome is the first/early frame
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "welcome":
                    return ("ok", m.get("save"))
                if m.get("t") == "login_failed":
                    return ("badpw", None)
    except Exception:
        return ("offline", None)
    return ("offline", None)


def push_save(uri, name, pw, save, timeout=_TIMEOUT):
    """Upload one save dict, blocking. Returns True on a clean send. Never raises.
    Compares timestamps first: a device that missed its startup pull (offline
    at launch) must not stomp a newer cloud save on quit."""
    try:
        from .net import SAVE_WIRE_MAX
        if len(json.dumps(save)) > SAVE_WIRE_MAX:
            return False       # the server would silently drop the frame (64KB cap)
    except Exception:
        return False
    try:
        cloud = pull_save(uri, name, pw, timeout)
        if cloud and float(cloud.get("_saved_at") or 0) > float(save.get("_saved_at") or 0):
            return False                             # the cloud moved on without us
    except Exception:
        pass                                         # compare is best-effort; the send decides
    try:
        with _connect(uri, timeout) as ws:
            ws.send(json.dumps({"t": "login", "name": name, "pw": pw,
                                "sync_only": True, "boot": BOOT}))
            ws.send(json.dumps({"t": "save", "save": save}))
            for _ in range(5):                   # wait for the server's verdict --
                m = json.loads(ws.recv(timeout=timeout))
                if m.get("t") == "saved":        # fire-and-forget used to report
                    return bool(m.get("ok"))     # True on drops (stale lease etc.)
                if m.get("t") == "login_failed":
                    return False
            return False
    except Exception:
        return False


def _other_pet(cloud):
    """Is the cloud holding a DIFFERENT pet from the local save?

    Different species or different generation = a different life, not a
    later state of this one.  Unreadable local save -> False: an empty or
    torn save has nothing to protect, and the ordinary rules apply.
    """
    import json as _json
    try:
        with open(persistence.SAVE_PATH) as fh:
            local = _json.load(fh)
    except (ValueError, OSError):
        return False
    return (local.get("num"), local.get("generation")) != \
           (cloud.get("num"), cloud.get("generation"))


def sync_down_at_startup(uri, name, pw, timeout=_TIMEOUT):
    """Pull the cloud save and, if it's newer than the local one, write it to the
    local save file so the app loads the synced pet. Returns a short status string
    for logging/tests ('' when nothing changed)."""
    global PULL_REACHED, DIVERGED
    DIVERGED = False
    if not name:
        PULL_REACHED = True              # no account: the cloud isn't in play
        return ""
    save = pull_save(uri, name, pw, timeout)
    if not save:
        # UNREACHABLE vs EMPTY are the same None here, so assume the worse of
        # the two: we could not confirm what the cloud holds, and the session
        # pusher must not overwrite it blind (see PULL_REACHED).
        PULL_REACHED = False
        return ""
    PULL_REACHED = True
    cloud_ts = float(save.get("_saved_at") or 0)
    if cloud_ts <= persistence.local_saved_at():
        # Local is newer BY THE CLOCK -- which only says this device was
        # played more recently, NOT that it holds the account's real pet.
        # A desktop sitting on an old playthrough is permanently "newer"
        # than the phone you actually play, so it never pulls, and then its
        # autosave pushes its stale pet over the cloud.  That is how the
        # same account lost a pet twice (2026-07-27).  When the cloud holds
        # a DIFFERENT pet, the clock does not get to decide: keep local,
        # push NOTHING, and let the player's next real session on the other
        # device move the cloud ahead -- then this one pulls it normally.
        if _other_pet(save):
            PULL_REACHED, DIVERGED = False, True
            return "diverged"
        return ""                                    # same pet, just older
    persistence.rescue_copy()                        # the pulled-over pet STAYS
    # never clobber a valid local save with a blob that can't even become a
    # pet (a malformed cloud payload used to mean a silent fresh-egg wipe) --
    # and never accept a FOREIGN-format save (strict: an outdated client's
    # push must not replace this build's pet; 2026-07-04 'Child' incident)
    probe, _ = persistence.pet_from_save(dict(save), strict=True)
    if probe is None:
        return "cloud-save-invalid"
    persistence.write_save_dict(save)
    return "pulled"
