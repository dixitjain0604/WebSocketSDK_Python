
"""
sync_users_biz.py - Sync engine business logic for Django web UI
Firmware-compatible with Tempus-TC5000 and standard SDK devices.
CONNECTION FIX: Reuses single connection per operation instead of per-command.
"""

import time
import logging
from xml.etree import ElementTree
from sdkdemoapp.biz import connection

CMD_DELAY = 0.35

logger = logging.getLogger("sync_users")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [SYNC] %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


# ── XML helpers (firmware-compatible) ─────────────────────────────────

def _build_xml(tag_dict):
    root = ElementTree.Element("Message")
    for key, val in tag_dict.items():
        if val is None or val == "":
            continue
        el = ElementTree.SubElement(root, key)
        el.text = str(val)
    return ElementTree.tostring(root, encoding="unicode")


def _parse(raw):
    if not raw:
        return None
    try:
        return ElementTree.fromstring(raw)
    except Exception:
        return None


def _val(el, tag, default=""):
    if el is None:
        return default
    child = el.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return default


def _is_ok(el):
    if el is None:
        return False
    for tag in ["r", "Result"]:
        v = _val(el, tag)
        if v and v.upper().startswith("OK"):
            return True
    return False


def _is_fail(el):
    if el is None:
        return True
    for tag in ["r", "Result"]:
        v = _val(el, tag)
        if v and v.upper().startswith("FAIL"):
            return True
    return False


def _has_data(el, tag):
    if el is None:
        return False
    return len(_val(el, tag)) > 0


def _send_with_conn(conn, cid, xml_str, label=""):
    """Send a command using an EXISTING connection. No new connection per call."""
    time.sleep(CMD_DELAY)
    try:
        raw = conn.execute_command(cid, xml_str)
        return _parse(raw)
    except Exception as exc:
        logger.error(f"  {label} -> EXCEPTION: {exc}")
        return None


def _send_fresh(cid, xml_str, label=""):
    """Send a command by opening a fresh connection. Use sparingly."""
    time.sleep(CMD_DELAY)
    try:
        with connection.open() as c:
            raw = c.execute_command(cid, xml_str)
        return _parse(raw)
    except Exception as exc:
        logger.error(f"  {label} -> EXCEPTION: {exc}")
        return None


# ── Device listing ────────────────────────────────────────────────────

def get_devices_with_status():
    """Return list of online Device objects with user/fp/face/card counts.
    Uses ONE connection for all status queries."""
    try:
        with connection.open() as c:
            devices = c.get_all_online_devices()

            # Query each device status using the SAME connection
            for dev in devices:
                dev.user_count = "?"
                dev.fp_count = "?"
                dev.face_count = "?"
                dev.card_count = "?"
                cid = getattr(dev, "connection_id", None)
                if cid is not None:
                    try:
                        xml = _build_xml({"Request": "GetDeviceStatusAll"})
                        time.sleep(0.15)
                        raw = c.execute_command(cid, xml)
                        resp = _parse(raw)
                        if resp is not None:
                            dev.user_count = _val(resp, "UserCount", "?")
                            dev.fp_count = _val(resp, "FpCount", "?")
                            dev.face_count = _val(resp, "FaceCount", "?")
                            dev.card_count = _val(resp, "CardCount", "?")
                    except Exception:
                        pass
    except Exception:
        return []
    return devices


def _normalize_privilege(raw):
    r = raw.strip().upper()
    if r in ("ADMIN", "ADMINISTRATOR", "1", "SUPER_ADMIN"):
        return "Admin"
    return "User"


# ── PULL: Get all users + biometrics from one device ──────────────────

def _pull_all_users(conn, cid, log):
    """Enumerate all users. Uses the passed-in connection (no new opens)."""
    users = {}

    def _log(msg):
        logger.info(msg)
        log.append(msg)

    _log(f"  Enumerating users from CID={cid}...")

    xml = _build_xml({"Request": "GetFirstUserData"})
    resp = _send_with_conn(conn, cid, xml, "GetFirstUserData")
    if resp is None or _is_fail(resp):
        _log("  GetFirstUserData failed - device may have no users")
        return users

    uid = _val(resp, "UserID")
    if uid:
        users[uid] = _parse_profile(resp)
        _log(f"    Found UID={uid}")

    more = _val(resp, "More", "No").upper()
    while more in ("YES", "1", "TRUE"):
        xml = _build_xml({"Request": "GetNextUserData"})
        resp = _send_with_conn(conn, cid, xml, "GetNextUserData")
        if resp is None or _is_fail(resp):
            break
        uid = _val(resp, "UserID")
        if uid:
            users[uid] = _parse_profile(resp)
            _log(f"    Found UID={uid}")
        more = _val(resp, "More", "No").upper()

    _log(f"  Found {len(users)} user profiles")

    # Pull biometrics for each user
    for uid, user in users.items():
        _log(f"  Pulling biometrics for UID={uid}...")

        # Scan ALL 10 finger slots (bitmask unreliable)
        for finger_no in range(10):
            xml = _build_xml({
                "Request": "GetFingerData",
                "UserID": uid,
                "FingerNo": str(finger_no),
                "FingerOnly": "1",
            })
            resp = _send_with_conn(conn, cid, xml, f"GetFinger UID={uid} F={finger_no}")
            if resp is not None and not _is_fail(resp) and _has_data(resp, "FingerData"):
                user["fingers"][finger_no] = _val(resp, "FingerData")
                _log(f"    Finger {finger_no}: OK")

        # Face
        xml = _build_xml({"Request": "GetFaceData", "UserID": uid})
        resp = _send_with_conn(conn, cid, xml, f"GetFace UID={uid}")
        if resp is not None and not _is_fail(resp) and _has_data(resp, "FaceData"):
            user["face"] = _val(resp, "FaceData")
            _log(f"    Face: OK")

        # Photo
        xml = _build_xml({"Request": "GetUserPhoto", "UserID": uid})
        resp = _send_with_conn(conn, cid, xml, f"GetPhoto UID={uid}")
        if resp is not None and not _is_fail(resp) and _has_data(resp, "PhotoData"):
            user["photo"] = _val(resp, "PhotoData")
            user["photo_size"] = _val(resp, "PhotoSize")
            _log(f"    Photo: OK")

    return users


def _parse_profile(el):
    name = _val(el, "Name") or _val(el, "n")
    return {
        "name": name,
        "privilege": _normalize_privilege(_val(el, "Privilege", "User")),
        "enabled": _val(el, "Enabled", "Yes"),
        "department": _val(el, "Dept"),
        "timeset1": _val(el, "TimeSet1", "0"),
        "timeset2": _val(el, "TimeSet2", "0"),
        "timeset3": _val(el, "TimeSet3", "0"),
        "timeset4": _val(el, "TimeSet4", "0"),
        "timeset5": _val(el, "TimeSet5", "0"),
        "period_used": _val(el, "UserPeriod_Used"),
        "period_start": _val(el, "UserPeriod_Start"),
        "period_end": _val(el, "UserPeriod_End"),
        "card": _val(el, "Card"),
        "password": _val(el, "PWD"),
        "qr": _val(el, "QR"),
        "fingers": {},
        "face": "",
        "photo": "",
        "photo_size": "",
    }


# ── PUSH: Send one user + biometrics to a device ─────────────────────

def _push_user(conn, cid, uid, user, log):
    """Push complete user. Uses existing connection."""
    def _log(msg):
        logger.info(msg)
        log.append(msg)

    tags = {
        "Request": "SetUserData",
        "UserID": uid,
        "Type": "Set",
        "Name": user["name"],
        "n": user["name"],
        "Privilege": user["privilege"],
        "Enabled": user["enabled"],
        "TimeSet1": user["timeset1"],
        "TimeSet2": user["timeset2"],
        "TimeSet3": user["timeset3"],
        "TimeSet4": user["timeset4"],
        "TimeSet5": user["timeset5"],
        "AllowNoCertificate": "Yes",
    }
    if user["department"]:
        tags["Dept"] = user["department"]
    if user["card"]:
        tags["Card"] = user["card"]
    if user["password"]:
        tags["PWD"] = user["password"]
    if user["qr"]:
        tags["QR"] = user["qr"]
    if user["face"]:
        tags["FaceData"] = user["face"]
    if user.get("period_used", "").upper() in ("YES", "1", "TRUE"):
        tags["UserPeriod_Used"] = "Yes"
        if user["period_start"]:
            tags["UserPeriod_Start"] = user["period_start"]
        if user["period_end"]:
            tags["UserPeriod_End"] = user["period_end"]

    xml = _build_xml(tags)
    resp = _send_with_conn(conn, cid, xml, f"SetUserData UID={uid}")
    if _is_fail(resp):
        _log(f"    Profile: FAILED")
        return False
    _log(f"    Profile + name + credentials: OK")

    # Fingers
    for finger_no, template in user["fingers"].items():
        xml = _build_xml({
            "Request": "SetFingerData",
            "UserID": uid,
            "Privilege": user["privilege"],
            "FingerNo": str(finger_no),
            "DuplicationCheck": "1",
            "Duress": "0",
            "FingerData": template,
        })
        resp = _send_with_conn(conn, cid, xml, f"SetFinger UID={uid} F={finger_no}")
        ok = not _is_fail(resp)
        _log(f"    Finger {finger_no}: {'OK' if ok else 'FAILED'}")

    # Face
    if user["face"]:
        xml = _build_xml({
            "Request": "SetFaceData",
            "UserID": uid,
            "Privilege": user["privilege"],
            "DuplicationCheck": "Yes",
            "FaceData": user["face"],
        })
        resp = _send_with_conn(conn, cid, xml, f"SetFace UID={uid}")
        ok = not _is_fail(resp)
        _log(f"    Face: {'OK' if ok else 'FAILED'}")

    # Photo
    if user["photo"]:
        xml = _build_xml({
            "Request": "SetUserPhoto",
            "UserID": uid,
            "PhotoSize": user["photo_size"] or str(len(user["photo"])),
            "PhotoData": user["photo"],
        })
        resp = _send_with_conn(conn, cid, xml, f"SetPhoto UID={uid}")
        ok = not _is_fail(resp)
        _log(f"    Photo: {'OK' if ok else 'FAILED'}")

    return True


# ── Main sync functions (called by views.py) ──────────────────────────

def run_sync(host_id, target_ids, mirror=False):
    log = []
    log.append("=" * 60)
    log.append(f"SYNC: Host={host_id} -> Targets={target_ids}")
    log.append("=" * 60)

    devices = get_devices_with_status()
    dev_map = {str(getattr(d, "device_id", "")): getattr(d, "connection_id", None) for d in devices}

    host_cid = dev_map.get(str(host_id))
    if host_cid is None:
        log.append(f"ERROR: Host device {host_id} not found or offline")
        return log

    # ONE connection for the entire sync operation
    with connection.open() as conn:

        log.append(f"\nPHASE 1: Pulling all users from {host_id}...")
        host_users = _pull_all_users(conn, host_cid, log)

        if not host_users:
            log.append("No users found on host device.")
            return log

        log.append(f"\nPulled {len(host_users)} users:")
        for uid, u in host_users.items():
            fc = len(u["fingers"])
            log.append(f"  UID={uid}  Name={'set' if u['name'] else 'empty'}  "
                        f"Fingers={fc}  Face={'Yes' if u['face'] else 'No'}")

        for tid in target_ids:
            target_cid = dev_map.get(str(tid))
            if target_cid is None:
                log.append(f"\nERROR: Target {tid} not found or offline - skipping")
                continue

            log.append(f"\nPHASE 2: Pushing to {tid} (CID={target_cid})...")

            if mirror:
                log.append(f"  MIRROR MODE: Flushing all users from target {tid}...")
                target_users = _pull_all_users(conn, target_cid, log)
                for tuid in target_users:
                    log.append(f"  Deleting UID={tuid} from target...")
                    for fno in range(10):
                        xml = _build_xml({
                            "Request": "SetFingerData",
                            "UserID": tuid,
                            "FingerNo": str(fno),
                            "FingerData": "",
                        })
                        _send_with_conn(conn, target_cid, xml, f"DelFinger UID={tuid} F={fno}")
                    xml = _build_xml({"Request": "SetFaceData", "UserID": tuid, "FaceData": ""})
                    _send_with_conn(conn, target_cid, xml, f"DelFace UID={tuid}")
                    xml = _build_xml({"Request": "SetUserPhoto", "UserID": tuid, "PhotoData": ""})
                    _send_with_conn(conn, target_cid, xml, f"DelPhoto UID={tuid}")
                    xml = _build_xml({"Request": "SetUserData", "UserID": tuid, "Type": "Delete"})
                    resp = _send_with_conn(conn, target_cid, xml, f"Delete UID={tuid}")
                    ok = not _is_fail(resp)
                    log.append(f"    Delete UID={tuid}: {'OK' if ok else 'FAILED'}")
                log.append(f"  Flush complete. Now pushing {len(host_users)} users fresh...")

            for uid, user in host_users.items():
                log.append(f"\n  Pushing UID={uid}...")
                _push_user(conn, target_cid, uid, user, log)

    log.append("\n" + "=" * 60)
    log.append("SYNC COMPLETE")
    log.append("=" * 60)
    return log


run_sync_one_way = run_sync  # Alias for views.py


def run_sync_bidirectional(device_ids):
    log = []
    log.append("=" * 60)
    log.append(f"BIDIRECTIONAL SYNC: {device_ids}")
    log.append("=" * 60)

    devices = get_devices_with_status()
    dev_map = {str(getattr(d, "device_id", "")): getattr(d, "connection_id", None) for d in devices}

    all_users = {}
    device_has = {}

    # ONE connection for everything
    with connection.open() as conn:

        for did in device_ids:
            cid = dev_map.get(str(did))
            if cid is None:
                log.append(f"ERROR: Device {did} not online - skipping")
                continue

            log.append(f"\nPulling from {did}...")
            users = _pull_all_users(conn, cid, log)
            device_has[did] = set(users.keys())

            for uid, user in users.items():
                if uid not in all_users:
                    all_users[uid] = user
                else:
                    existing = all_users[uid]
                    if not existing["name"] and user["name"]:
                        existing["name"] = user["name"]
                    if not existing["face"] and user["face"]:
                        existing["face"] = user["face"]
                    if not existing["photo"] and user["photo"]:
                        existing["photo"] = user["photo"]
                        existing["photo_size"] = user["photo_size"]
                    if not existing["card"] and user["card"]:
                        existing["card"] = user["card"]
                    if not existing["password"] and user["password"]:
                        existing["password"] = user["password"]
                    if not existing["qr"] and user["qr"]:
                        existing["qr"] = user["qr"]
                    for fno, tmpl in user["fingers"].items():
                        if fno not in existing["fingers"]:
                            existing["fingers"][fno] = tmpl

        log.append(f"\nMerged master: {len(all_users)} unique users")

        for did in device_ids:
            cid = dev_map.get(str(did))
            if cid is None:
                continue
            has = device_has.get(did, set())
            missing_uids = set(all_users.keys()) - has
            if not missing_uids:
                log.append(f"\n{did}: All users already present")
                continue
            log.append(f"\n{did}: Pushing {len(missing_uids)} missing users...")
            for uid in missing_uids:
                log.append(f"  Pushing UID={uid}...")
                _push_user(conn, cid, uid, all_users[uid], log)

    log.append("\n" + "=" * 60)
    log.append("BIDIRECTIONAL SYNC COMPLETE")
    log.append("=" * 60)
    return log
