"""
flush_device.py — Wipe ALL user data from a device (or multiple devices)
=========================================================================
Deletes every user, their fingerprints, face data, photos, cards, and passwords.
Supports both bulk-clear commands and per-user fallback deletion.

Usage (standalone):
    python flush_device.py                  # interactive: pick devices
    python flush_device.py DEV001           # flush one device
    python flush_device.py DEV001 DEV002    # flush multiple

Place at: DjangoExample/sdkdemoapp/biz/flush_device.py
Also callable from views.py as:  from .biz import flush_device
                                  log = flush_device.run_flush([device_id, ...])
"""

import sys
import time
from xml.etree import ElementTree
from typing import List, Optional, Tuple

from devicebroker.client import Client

BROKER = "127.0.0.1:8002"
DELAY  = 0.30   # seconds between commands — safe for all device types


# ── XML helpers ────────────────────────────────────────────────────────────────

def _xml(tags: dict) -> str:
    """Build a flat <Message> XML string from a dict."""
    root = ElementTree.Element("Message")
    for k, v in tags.items():
        el = ElementTree.SubElement(root, k)
        if v is not None:
            el.text = str(v)
    return ElementTree.tostring(root, encoding="unicode")


def _parse(s: str) -> Optional[ElementTree.Element]:
    try:
        return ElementTree.fromstring(s)
    except Exception:
        return None


def _get(el: ElementTree.Element, tag: str, default: str = "") -> str:
    c = el.find(tag)
    return c.text.strip() if (c is not None and c.text) else default


def _is_ok(el: Optional[ElementTree.Element]) -> bool:
    if el is None:
        return False
    for tag in ("r", "Result"):
        v = _get(el, tag).upper()
        if v.startswith("OK"):
            return True
    return False


def _is_fail(el: Optional[ElementTree.Element]) -> bool:
    if el is None:
        return True
    for tag in ("r", "Result"):
        v = _get(el, tag).upper()
        if v.startswith("FAIL"):
            return True
    return False


# ── Network ────────────────────────────────────────────────────────────────────

def _send(conn_id: int, xml_str: str) -> Optional[ElementTree.Element]:
    """Send one command on a fresh connection; return parsed response or None."""
    time.sleep(DELAY)
    try:
        with Client(BROKER) as c:
            raw = c.execute_command(conn_id, xml_str)
        return _parse(raw)
    except Exception:
        return None


def _conn_id(device_id: str) -> Optional[int]:
    try:
        with Client(BROKER) as c:
            d = c.find_device(device_id)
            return d.connection_id if d else None
    except Exception:
        return None


def _all_device_ids() -> List[str]:
    try:
        with Client(BROKER) as c:
            return [d.device_id for d in c.get_all_online_devices()]
    except Exception:
        return []


# ── Step 1: collect every User ID on the device ────────────────────────────────

def _collect_user_ids(cid: int, log: list, did: str) -> List[str]:
    """
    Try enumeration first (GetFirst/GetNextUserData).
    Fall back to brute-force scan 1-9999 if enumeration returns nothing.
    Returns a sorted list of string user IDs.
    """
    found = set()

    # ── Enumeration path ──
    resp = _send(cid, _xml({"Request": "GetFirstUserData"}))
    if resp is not None and not _is_fail(resp):
        uid = _get(resp, "UserID")
        if uid:
            found.add(uid)
        more = _get(resp, "More", "No")

        while more == "Yes":
            resp = _send(cid, _xml({"Request": "GetNextUserData"}))
            if resp is None or _is_fail(resp):
                break
            uid = _get(resp, "UserID")
            if uid:
                found.add(uid)
            more = _get(resp, "More", "No")

        if found:
            log.append(f"[{did}] Enumeration found {len(found)} user(s): {sorted(found)}")
            return sorted(found)

    # ── Brute-force fallback ──
    log.append(f"[{did}] Enumeration returned nothing — scanning IDs 1..9999")
    for i in range(1, 10000):
        resp = _send(cid, _xml({"Request": "GetUserData", "UserID": str(i)}))
        if resp is not None and not _is_fail(resp) and _get(resp, "UserID"):
            found.add(str(i))
            log.append(f"[{did}]   Found user {i}")

    log.append(f"[{did}] Brute-force found {len(found)} user(s): {sorted(found)}")
    return sorted(found)


# ── Step 2: delete one user completely ─────────────────────────────────────────

def _delete_user(cid: int, uid: str, log: list, did: str) -> bool:
    """
    Delete a single user:
      1. Erase all 10 finger slots individually (safest — avoids cross-user bleed).
      2. Erase face data.
      3. Erase photo.
      4. Delete the user record.
    Returns True if the user record deletion succeeded.
    """

    # ── Fingerprints: always erase all 10 slots explicitly ──
    for fno in range(10):
        resp = _send(cid, _xml({
            "Request"  : "DeleteFingerData",
            "UserID"   : uid,
            "FingerNo" : str(fno),
        }))
        # Failure here just means the slot was already empty — that's fine.

    # ── Face ──
    _send(cid, _xml({"Request": "DeleteFaceData", "UserID": uid}))

    # ── Photo ──
    _send(cid, _xml({"Request": "DeleteUserPhoto", "UserID": uid}))

    # ── Card ──
    _send(cid, _xml({"Request": "DeleteUserCardNo", "UserID": uid}))

    # ── Password ──
    _send(cid, _xml({"Request": "DeleteUserPassword", "UserID": uid}))

    # ── QR ──
    _send(cid, _xml({"Request": "DeleteUserQR", "UserID": uid}))

    # ── User record ──
    resp = _send(cid, _xml({"Request": "DeleteUser", "UserID": uid}))
    ok = _is_ok(resp)
    status = "OK" if ok else "FAILED"
    log.append(f"[{did}]   User {uid:>6} → {status}")
    return ok


# ── Step 3: attempt a bulk wipe first, then verify ─────────────────────────────

_BULK_COMMANDS = [
    "ClearAllUserData",
    "DeleteAllUsers",
    "ClearUsers",
    "EraseAllUsers",
]


def _try_bulk_wipe(cid: int, log: list, did: str) -> bool:
    """
    Try known bulk-erase commands. Returns True if one succeeds.
    Not all firmware supports these; that is fine — we fall back to per-user.
    """
    for cmd in _BULK_COMMANDS:
        resp = _send(cid, _xml({"Request": cmd}))
        if _is_ok(resp):
            log.append(f"[{did}] Bulk wipe succeeded with: {cmd}")
            return True
    return False


# ── Status snapshot ────────────────────────────────────────────────────────────

def _status(cid: int, log: list, did: str):
    resp = _send(cid, _xml({"Request": "GetDeviceStatusAll"}))
    if resp is None:
        log.append(f"[{did}] Status: (no response)")
        return
    counts = {c.tag: (c.text.strip() if c.text else "?") for c in resp}
    log.append(
        f"[{did}] Status → "
        f"Users={counts.get('UserCount','?')}  "
        f"FP={counts.get('FpCount','?')}  "
        f"Face={counts.get('FaceCount','?')}  "
        f"Card={counts.get('CardCount','?')}"
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def run_flush(device_ids: List[str], *, confirm: bool = True) -> List[str]:
    """
    Flush all user data from every device in *device_ids*.

    Parameters
    ----------
    device_ids : list of device ID strings
    confirm    : if True (default), a safety check is printed to stdout
                 (set False when calling from a web view that already confirmed)

    Returns
    -------
    log : list of strings — one per log line
    """
    log: List[str] = []

    if not device_ids:
        log.append("ERROR: No device IDs provided.")
        return log

    log.append("=" * 60)
    log.append(f"FLUSH TARGETS: {device_ids}")
    log.append("=" * 60)

    for did in device_ids:
        log.append("")
        log.append(f"── Device: {did} {'─' * (50 - len(did))}")

        # ── Connect ──
        cid = _conn_id(did)
        if cid is None:
            log.append(f"[{did}] OFFLINE — skipping")
            continue

        # ── Before snapshot ──
        log.append(f"[{did}] Before flush:")
        _status(cid, log, did)

        # ── Collect user IDs first (needed for per-user path regardless) ──
        uids = _collect_user_ids(cid, log, did)

        if not uids:
            log.append(f"[{did}] No users found — device already clean.")
            continue

        log.append(f"[{did}] {len(uids)} user(s) to remove: {uids}")

        # ── Try bulk wipe ──
        bulk_ok = _try_bulk_wipe(cid, log, did)

        if bulk_ok:
            # Verify bulk wipe actually worked
            remaining = _collect_user_ids(cid, log, did)
            if remaining:
                log.append(f"[{did}] Bulk wipe reported OK but {len(remaining)} user(s) remain — "
                            f"falling through to per-user deletion.")
            else:
                log.append(f"[{did}] Bulk wipe confirmed clean.")
                log.append(f"[{did}] After flush:")
                _status(cid, log, did)
                continue  # done for this device

        # ── Per-user deletion (authoritative path) ──
        log.append(f"[{did}] Deleting {len(uids)} user(s) one by one...")
        ok_count = 0
        fail_uids = []
        for uid in uids:
            success = _delete_user(cid, uid, log, did)
            if success:
                ok_count += 1
            else:
                fail_uids.append(uid)

        log.append(f"[{did}] Deleted {ok_count}/{len(uids)} users.")
        if fail_uids:
            log.append(f"[{did}] FAILED to delete: {fail_uids}")

        # ── After snapshot ──
        log.append(f"[{did}] After flush:")
        _status(cid, log, did)

    log.append("")
    log.append("=" * 60)
    log.append("FLUSH COMPLETE")
    log.append("=" * 60)
    return log


# ── CLI entry-point ────────────────────────────────────────────────────────────

def _interactive_pick(all_ids: List[str]) -> List[str]:
    print("\nOnline devices:")
    for i, did in enumerate(all_ids, 1):
        print(f"  [{i}] {did}")
    raw = input("\nEnter numbers to flush (e.g. 1 3) or ALL: ").strip()
    if raw.upper() == "ALL":
        return all_ids
    chosen = []
    for tok in raw.split():
        try:
            chosen.append(all_ids[int(tok) - 1])
        except (ValueError, IndexError):
            pass
    return chosen


if __name__ == "__main__":
    targets = sys.argv[1:]   # optional: pass device IDs as CLI args

    if not targets:
        online = _all_device_ids()
        if not online:
            print("No devices online. Exiting.")
            sys.exit(1)
        targets = _interactive_pick(online)

    if not targets:
        print("Nothing selected. Exiting.")
        sys.exit(0)

    print(f"\n⚠️  About to ERASE ALL USER DATA on: {targets}")
    ans = input("Type YES to continue: ").strip()
    if ans != "YES":
        print("Aborted.")
        sys.exit(0)

    lines = run_flush(targets, confirm=False)
    print("\n".join(lines))
