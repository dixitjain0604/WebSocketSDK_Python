"""
WebSocketSDK Master-Master Deep Sync Engine (FINAL)
=====================================================
Does NOT just check if user ID exists — compares actual DATA
inside each user and pushes whatever pieces are missing.

Also handles deletion: if a user is removed from one device,
removes from all others.

Usage:
    $ cd "/home/batman/Downloads/WebSocketSDK 20250611/WebSocketSDK_Python"
    $ source venv/bin/activate
    $ export PYTHONPATH="$(pwd)/packages"
    $ python sync_engine.py
"""

import sys
import time
import logging
import base64
import traceback
from xml.etree import ElementTree
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from copy import deepcopy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
LOG = logging.getLogger("sync")
logging.getLogger("asyncio").setLevel(logging.WARNING)

try:
    from devicebroker.client import Client, Device
except ImportError:
    print("ERROR: Cannot import devicebroker.")
    print('Run: export PYTHONPATH="$(pwd)/packages"')
    sys.exit(1)

BROKER_ADDRESS = "127.0.0.1:8002"
POLL_INTERVAL  = 15
CMD_DELAY      = 0.5


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------
def make_xml(tags: dict) -> str:
    root = ElementTree.Element("Message")
    for k, v in tags.items():
        el = ElementTree.SubElement(root, k)
        if v is not None:
            el.text = str(v)
    return ElementTree.tostring(root, encoding="unicode")


def parse(xml_str: str) -> Optional[ElementTree.Element]:
    try:
        return ElementTree.fromstring(xml_str)
    except Exception:
        return None


def val(el: ElementTree.Element, tag: str, default: str = "") -> str:
    ch = el.find(tag)
    if ch is not None and ch.text is not None:
        return ch.text.strip()
    return default


def has_data(el: ElementTree.Element, tag: str) -> bool:
    ch = el.find(tag)
    return ch is not None and ch.text is not None and len(ch.text.strip()) > 0


def dump(el: ElementTree.Element) -> dict:
    return {ch.tag: (ch.text.strip() if ch.text else "") for ch in el}


def is_fail(el: ElementTree.Element) -> bool:
    for tag in ["r", "Result"]:
        v = val(el, tag)
        if v.upper().startswith("FAIL"):
            return True
    return False


def is_ok(el: ElementTree.Element) -> bool:
    for tag in ["r", "Result"]:
        v = val(el, tag)
        if v.upper().startswith("OK"):
            return True
    return False


def send(client: Client, conn_id: int, did: str, xml: str) -> Optional[ElementTree.Element]:
    time.sleep(CMD_DELAY)
    try:
        raw = client.execute_command(conn_id, xml)
    except Exception as e:
        LOG.error(f"[{did}] Command error: {e}")
        return None
    return parse(raw)


def send_raw(client: Client, conn_id: int, did: str, xml: str) -> Optional[ElementTree.Element]:
    """Send pre-built XML string (for fingerprint push with full template)."""
    time.sleep(CMD_DELAY)
    try:
        raw = client.execute_command(conn_id, xml)
    except Exception as e:
        LOG.error(f"[{did}] Command error: {e}")
        return None
    return parse(raw)


def decode_name(b64: str) -> str:
    if not b64:
        return "(no name)"
    try:
        return base64.b64decode(b64).decode("utf-16-le").rstrip("\x00")
    except Exception:
        return b64[:20]


# ---------------------------------------------------------------------------
# User record — holds EVERYTHING
# ---------------------------------------------------------------------------
@dataclass
class FullUser:
    user_id:      str = ""
    name:         str = ""
    privilege:    str = ""
    department:   str = ""
    enabled:      str = ""
    timeset1:     str = ""
    timeset2:     str = ""
    timeset3:     str = ""
    timeset4:     str = ""
    timeset5:     str = ""
    period_used:  str = ""
    period_start: str = ""
    period_end:   str = ""
    card:         str = ""
    password:     str = ""
    qr:           str = ""
    fingers:      Dict[int, Tuple[str, str]] = field(default_factory=dict)
    face:         str = ""
    photo:        str = ""
    photo_size:   str = "0"

    def finger_count(self) -> int:
        return len(self.fingers)

    def has_face(self) -> bool:
        return bool(self.face and len(self.face) > 10)

    def has_photo(self) -> bool:
        return bool(self.photo and len(self.photo) > 10)

    def has_card(self) -> bool:
        return bool(self.card and self.card != "AAAAAA==" and self.card != "0" and self.card != "")

    def has_password(self) -> bool:
        return bool(self.password and self.password.strip() != "")

    def has_qr(self) -> bool:
        return bool(self.qr and self.qr != "AAAAAA==" and self.qr != "0" and self.qr != "")

    def summary(self) -> str:
        return (f"fingers={self.finger_count()}, face={'Y' if self.has_face() else 'N'}, "
                f"photo={'Y' if self.has_photo() else 'N'}, card={'Y' if self.has_card() else 'N'}, "
                f"pwd={'Y' if self.has_password() else 'N'}, qr={'Y' if self.has_qr() else 'N'}")


# ---------------------------------------------------------------------------
# GET DEVICE STATUS
# ---------------------------------------------------------------------------
def get_status(client: Client, dev: Device) -> dict:
    resp = send(client, dev.connection_id, dev.device_id,
                make_xml({"Request": "GetDeviceStatusAll"}))
    return dump(resp) if resp else {}


# ---------------------------------------------------------------------------
# FIND ALL USER IDS
# ---------------------------------------------------------------------------
def find_all_user_ids(client: Client, dev: Device, user_count: int) -> List[str]:
    did = dev.device_id
    conn = dev.connection_id

    if user_count <= 0:
        return []

    # Try enumeration first
    resp = send(client, conn, did, make_xml({"Request": "GetFirstUserData"}))
    if resp is not None and not is_fail(resp) and has_data(resp, "UserID"):
        ids = []
        d = dump(resp)
        uid = d.get("UserID", "")
        if uid:
            ids.append(uid)
        more = d.get("More", "No")
        while more == "Yes":
            resp = send(client, conn, did, make_xml({"Request": "GetNextUserData"}))
            if resp is None or is_fail(resp):
                break
            d = dump(resp)
            uid = d.get("UserID", "")
            if uid:
                ids.append(uid)
            more = d.get("More", "No")
        if len(ids) >= user_count:
            return ids

    # Brute-force scan
    scan_max = max(user_count * 15, 100)
    LOG.info(f"[{did}] Scanning IDs 1..{scan_max}...")
    found = []
    for i in range(1, scan_max + 1):
        resp = send(client, conn, did,
                    make_xml({"Request": "GetUserData", "UserID": str(i)}))
        if resp is not None and not is_fail(resp) and has_data(resp, "UserID"):
            found.append(str(i))
        if len(found) >= user_count:
            break
    return found


# ---------------------------------------------------------------------------
# PULL EVERYTHING for one user
# ---------------------------------------------------------------------------
def pull_user(client: Client, dev: Device, user_id: str) -> Optional[FullUser]:
    conn = dev.connection_id
    did = dev.device_id
    user = FullUser(user_id=user_id)

    # PROFILE
    resp = send(client, conn, did,
                make_xml({"Request": "GetUserData", "UserID": user_id}))
    if resp is None or is_fail(resp):
        return None

    d = dump(resp)
    user.name        = d.get("Name", "") or d.get("n", "")
    user.privilege   = d.get("Privilege", "")
    user.department  = d.get("Depart", "")
    user.enabled     = d.get("Enabled", "")
    user.timeset1    = d.get("TimeSet1", "")
    user.timeset2    = d.get("TimeSet2", "")
    user.timeset3    = d.get("TimeSet3", "")
    user.timeset4    = d.get("TimeSet4", "")
    user.timeset5    = d.get("TimeSet5", "")
    user.period_used = d.get("UserPeriod_Used", "")
    user.period_start = d.get("UserPeriod_Start", "")
    user.period_end  = d.get("UserPeriod_End", "")
    user.card        = d.get("Card", "")
    user.password    = d.get("PWD", "")
    user.qr          = d.get("QR", "")

    # ALL 10 FINGER SLOTS — try every single one
    for fno in range(10):
        resp = send(client, conn, did, make_xml({
            "Request": "GetFingerData",
            "UserID": user_id,
            "FingerNo": str(fno),
            "FingerOnly": "1",
        }))
        if resp is not None and not is_fail(resp) and has_data(resp, "FingerData"):
            template = val(resp, "FingerData")
            duress = val(resp, "Duress", "No")
            if len(template) > 10:
                user.fingers[fno] = (template, duress)

    # FACE
    resp = send(client, conn, did,
                make_xml({"Request": "GetFaceData", "UserID": user_id}))
    if resp is not None and not is_fail(resp) and has_data(resp, "FaceData"):
        user.face = val(resp, "FaceData")

    # PHOTO
    resp = send(client, conn, did,
                make_xml({"Request": "GetUserPhoto", "UserID": user_id}))
    if resp is not None and not is_fail(resp) and has_data(resp, "PhotoData"):
        user.photo = val(resp, "PhotoData")
        try:
            user.photo_size = str(len(base64.b64decode(user.photo)))
        except Exception:
            user.photo_size = "0"

    # CARD (dedicated call)
    if not user.has_card():
        resp = send(client, conn, did,
                    make_xml({"Request": "GetUserCardNo", "UserID": user_id}))
        if resp is not None and not is_fail(resp):
            cn = val(resp, "CardNo")
            if cn and cn != "AAAAAA==" and cn != "0":
                user.card = cn

    # PASSWORD (dedicated call)
    if not user.has_password():
        resp = send(client, conn, did,
                    make_xml({"Request": "GetUserPassword", "UserID": user_id}))
        if resp is not None and not is_fail(resp):
            pw = val(resp, "Password")
            if pw and pw.strip():
                user.password = pw

    # QR (dedicated call)
    if not user.has_qr():
        resp = send(client, conn, did,
                    make_xml({"Request": "GetUserQR", "UserID": user_id}))
        if resp is not None and not is_fail(resp):
            qr = val(resp, "QR")
            if qr and qr != "AAAAAA==":
                user.qr = qr

    LOG.info(f"[{did}] Pulled user {user_id} '{decode_name(user.name)}': {user.summary()}")
    return user


# ---------------------------------------------------------------------------
# MERGE two user records — take the most complete version of each field
# ---------------------------------------------------------------------------
def merge_users(a: FullUser, b: FullUser) -> FullUser:
    """Merge two records of the same user, keeping the most data."""
    merged = FullUser(user_id=a.user_id)

    # For each field, keep whichever is non-empty (prefer a)
    merged.name        = a.name or b.name
    merged.privilege   = a.privilege or b.privilege
    merged.department  = a.department or b.department
    merged.enabled     = a.enabled or b.enabled
    merged.timeset1    = a.timeset1 or b.timeset1
    merged.timeset2    = a.timeset2 or b.timeset2
    merged.timeset3    = a.timeset3 or b.timeset3
    merged.timeset4    = a.timeset4 or b.timeset4
    merged.timeset5    = a.timeset5 or b.timeset5
    merged.period_used = a.period_used or b.period_used
    merged.period_start = a.period_start or b.period_start
    merged.period_end  = a.period_end or b.period_end

    # Credentials: keep whichever has real data
    merged.card     = a.card if a.has_card() else (b.card if b.has_card() else a.card)
    merged.password = a.password if a.has_password() else (b.password if b.has_password() else "")
    merged.qr       = a.qr if a.has_qr() else (b.qr if b.has_qr() else "")

    # Fingers: union of both
    merged.fingers = dict(a.fingers)
    for fno, data in b.fingers.items():
        if fno not in merged.fingers:
            merged.fingers[fno] = data

    # Face: keep whichever exists
    merged.face = a.face if a.has_face() else b.face

    # Photo: keep whichever exists
    merged.photo = a.photo if a.has_photo() else b.photo
    merged.photo_size = a.photo_size if a.has_photo() else b.photo_size

    return merged


# ---------------------------------------------------------------------------
# CHECK what a device is missing compared to the master record
# ---------------------------------------------------------------------------
def needs_sync(device_user: Optional[FullUser], master: FullUser) -> dict:
    """Return a dict describing what needs to be pushed."""
    needs = {
        "profile": False,
        "fingers": [],      # list of finger numbers to push
        "face": False,
        "photo": False,
    }

    if device_user is None:
        # User doesn't exist at all — push everything
        needs["profile"] = True
        needs["fingers"] = list(master.fingers.keys())
        needs["face"] = master.has_face()
        needs["photo"] = master.has_photo()
        return needs

    # Check profile fields
    if master.name and master.name != device_user.name:
        needs["profile"] = True
    if master.has_card() and not device_user.has_card():
        needs["profile"] = True
    if master.has_password() and not device_user.has_password():
        needs["profile"] = True
    if master.has_qr() and not device_user.has_qr():
        needs["profile"] = True

    # Check each finger
    for fno in master.fingers:
        if fno not in device_user.fingers:
            needs["fingers"].append(fno)

    # Check face
    if master.has_face() and not device_user.has_face():
        needs["face"] = True

    # Check photo
    if master.has_photo() and not device_user.has_photo():
        needs["photo"] = True

    return needs


# ---------------------------------------------------------------------------
# PUSH specific data to a device
# ---------------------------------------------------------------------------
def push_profile(client: Client, dev: Device, user: FullUser) -> bool:
    """Push user profile + name + credentials."""
    conn = dev.connection_id
    did = dev.device_id

    tags = {
        "Request":            "SetUserData",
        "UserID":             user.user_id,
        "Type":               "Set",
        "AllowNoCertificate": "Yes",
    }

    if user.name:
        tags["Name"] = user.name
        tags["n"] = user.name
    for key, value in [
        ("Privilege", user.privilege), ("Enabled", user.enabled),
        ("TimeSet1", user.timeset1), ("TimeSet2", user.timeset2),
        ("TimeSet3", user.timeset3), ("TimeSet4", user.timeset4),
        ("TimeSet5", user.timeset5),
        ("UserPeriod_Used", user.period_used),
        ("UserPeriod_Start", user.period_start),
        ("UserPeriod_End", user.period_end),
    ]:
        if value:
            tags[key] = value
    if user.has_card():
        tags["Card"] = user.card
    if user.has_password():
        tags["PWD"] = user.password
    if user.has_qr():
        tags["QR"] = user.qr
    if user.has_face():
        tags["FaceData"] = user.face

    resp = send(client, conn, did, make_xml(tags))
    if resp is None or is_fail(resp):
        LOG.error(f"[{did}]   Profile push FAILED")
        return False
    LOG.info(f"[{did}]   Profile + name + credentials: OK")
    return True


def push_finger(client: Client, dev: Device, user_id: str, fno: int,
                template: str, duress: str, privilege: str) -> bool:
    """Push one finger using ElementTree to preserve full template."""
    conn = dev.connection_id
    did = dev.device_id

    root = ElementTree.Element("Message")
    for tag, text in [
        ("Request", "SetFingerData"),
        ("UserID", user_id),
        ("Privilege", privilege or "User"),
        ("FingerNo", str(fno)),
        ("DuplicationCheck", "1"),
        ("Duress", "1" if duress == "Yes" else "0"),
    ]:
        el = ElementTree.SubElement(root, tag)
        el.text = text
    fd = ElementTree.SubElement(root, "FingerData")
    fd.text = template

    xml = ElementTree.tostring(root, encoding="unicode")
    resp = send_raw(client, conn, did, xml)

    if resp is not None and is_ok(resp):
        LOG.info(f"[{did}]   Finger {fno}: OK")
        return True
    else:
        err = dump(resp) if resp else "no response"
        LOG.warning(f"[{did}]   Finger {fno}: FAILED {err}")
        return False


def push_face(client: Client, dev: Device, user_id: str, face: str, privilege: str) -> bool:
    conn = dev.connection_id
    did = dev.device_id
    resp = send(client, conn, did, make_xml({
        "Request": "SetFaceData",
        "UserID": user_id,
        "Privilege": privilege or "User",
        "DuplicationCheck": "Yes",
        "FaceData": face,
    }))
    if resp is not None and is_ok(resp):
        LOG.info(f"[{did}]   Face: OK")
        return True
    LOG.info(f"[{did}]   Face: skipped (may already be set via profile)")
    return True  # not critical


def push_photo(client: Client, dev: Device, user_id: str, photo: str, size: str) -> bool:
    conn = dev.connection_id
    did = dev.device_id
    resp = send(client, conn, did, make_xml({
        "Request": "SetUserPhoto",
        "UserID": user_id,
        "PhotoSize": size,
        "PhotoData": photo,
    }))
    if resp is not None and is_ok(resp):
        LOG.info(f"[{did}]   Photo: OK")
        return True
    LOG.warning(f"[{did}]   Photo: FAILED")
    return False


def delete_user(client: Client, dev: Device, user_id: str) -> bool:
    """Delete a user from a device."""
    conn = dev.connection_id
    did = dev.device_id
    resp = send(client, conn, did, make_xml({
        "Request": "SetUserData",
        "UserID": user_id,
        "Type": "Delete",
    }))
    if resp is not None and is_ok(resp):
        LOG.info(f"[{did}] Deleted user {user_id}")
        return True
    LOG.warning(f"[{did}] Failed to delete user {user_id}")
    return False


# ---------------------------------------------------------------------------
# SYNC ENGINE
# ---------------------------------------------------------------------------
class SyncEngine:
    def __init__(self):
        self.prev_users: Dict[str, Set[str]] = {}  # {device_id: set(user_ids)}

    def get_devices(self) -> List[Device]:
        try:
            with Client(BROKER_ADDRESS) as c:
                return c.get_all_online_devices()
        except Exception as e:
            LOG.error(f"Cannot connect to devicebroker: {e}")
            return []

    def deep_sync(self):
        """
        DEEP SYNC: Pull every user from every device, merge into
        master records, then push missing data to each device.
        """
        devices = self.get_devices()
        if len(devices) < 2:
            LOG.info(f"Need 2+ devices, found {len(devices)}")
            return

        LOG.info("=" * 60)
        LOG.info("DEEP SYNC — comparing actual data on all devices")
        for d in devices:
            LOG.info(f"  {d.device_id} ({d.attributes.get('product_name','?')})")
        LOG.info("=" * 60)

        # ===== PHASE 1: STATUS =====
        dev_counts: Dict[str, int] = {}
        for dev in devices:
            with Client(BROKER_ADDRESS) as c:
                st = get_status(c, dev)
            uc = int(st.get("UserCount", "0") or "0")
            dev_counts[dev.device_id] = uc
            LOG.info(f"[{dev.device_id}] Users={uc} FP={st.get('FpCount','0')} "
                     f"Face={st.get('FaceCount','0')} Card={st.get('CardCount','0')}")

        # ===== PHASE 2: FIND ALL USER IDS =====
        dev_ids: Dict[str, List[str]] = {}
        for dev in devices:
            with Client(BROKER_ADDRESS) as c:
                ids = find_all_user_ids(c, dev, dev_counts.get(dev.device_id, 0))
            dev_ids[dev.device_id] = ids
            self.prev_users[dev.device_id] = set(ids)
            LOG.info(f"[{dev.device_id}] Users: {ids}")

        # Master set of all user IDs
        all_ids = set()
        for ids in dev_ids.values():
            all_ids.update(ids)
        LOG.info(f"Master user IDs: {sorted(all_ids)}")

        if not all_ids:
            LOG.info("No users found anywhere.")
            return

        # ===== PHASE 3: PULL FULL DATA FOR EVERY USER FROM EVERY DEVICE =====
        LOG.info("")
        LOG.info("Pulling full data for all users from all devices...")
        # {user_id: {device_id: FullUser}}
        all_data: Dict[str, Dict[str, Optional[FullUser]]] = {}

        for uid in sorted(all_ids):
            all_data[uid] = {}
            for dev in devices:
                if uid in dev_ids.get(dev.device_id, []):
                    LOG.info(f"Pulling user {uid} from {dev.device_id}...")
                    with Client(BROKER_ADDRESS) as c:
                        user_data = pull_user(c, dev, uid)
                    all_data[uid][dev.device_id] = user_data
                else:
                    all_data[uid][dev.device_id] = None

        # ===== PHASE 4: MERGE INTO MASTER RECORDS =====
        LOG.info("")
        LOG.info("Building master records (merging best data)...")
        master_records: Dict[str, FullUser] = {}

        for uid in sorted(all_ids):
            records = [v for v in all_data[uid].values() if v is not None]
            if not records:
                continue
            # Start with first record, merge in others
            master = records[0]
            for other in records[1:]:
                master = merge_users(master, other)
            master_records[uid] = master
            LOG.info(f"  Master user {uid} '{decode_name(master.name)}': {master.summary()}")

        # ===== PHASE 5: COMPARE AND PUSH MISSING DATA =====
        LOG.info("")
        LOG.info("=" * 60)
        LOG.info("PUSHING missing data to each device...")
        LOG.info("=" * 60)

        total_ops = 0
        for dev in devices:
            did = dev.device_id
            LOG.info(f"")
            LOG.info(f"--- Checking {did} ---")

            for uid in sorted(all_ids):
                master = master_records.get(uid)
                if master is None:
                    continue

                device_record = all_data[uid].get(did)
                diff = needs_sync(device_record, master)

                # Check if anything needs syncing
                needs_anything = (diff["profile"] or diff["fingers"]
                                  or diff["face"] or diff["photo"])

                if not needs_anything:
                    LOG.info(f"[{did}] User {uid}: fully in sync")
                    continue

                LOG.info(f"[{did}] User {uid} '{decode_name(master.name)}' NEEDS: "
                         f"profile={diff['profile']}, fingers={diff['fingers']}, "
                         f"face={diff['face']}, photo={diff['photo']}")

                # Always push profile first (creates user if missing)
                with Client(BROKER_ADDRESS) as c:
                    if not push_profile(c, dev, master):
                        LOG.error(f"[{did}] Cannot create/update user {uid} — skipping")
                        continue
                total_ops += 1

                # Push missing fingers
                for fno in diff["fingers"]:
                    if fno in master.fingers:
                        template, duress = master.fingers[fno]
                        with Client(BROKER_ADDRESS) as c:
                            push_finger(c, dev, uid, fno, template, duress, master.privilege)
                        total_ops += 1

                # Push face
                if diff["face"] and master.has_face():
                    with Client(BROKER_ADDRESS) as c:
                        push_face(c, dev, uid, master.face, master.privilege)
                    total_ops += 1

                # Push photo
                if diff["photo"] and master.has_photo():
                    with Client(BROKER_ADDRESS) as c:
                        push_photo(c, dev, uid, master.photo, master.photo_size)
                    total_ops += 1

        # ===== PHASE 6: VERIFY =====
        LOG.info("")
        LOG.info("=" * 60)
        LOG.info(f"DEEP SYNC COMPLETE — {total_ops} operations")
        LOG.info("VERIFICATION:")
        for dev in devices:
            with Client(BROKER_ADDRESS) as c:
                st = get_status(c, dev)
            LOG.info(f"  [{dev.device_id}] Users={st.get('UserCount','?')} "
                     f"FP={st.get('FpCount','?')} Face={st.get('FaceCount','?')} "
                     f"Card={st.get('CardCount','?')}")
        LOG.info("=" * 60)

    def monitor(self):
        """Monitor for new enrollments and deletions."""
        devices = self.get_devices()
        if len(devices) < 2:
            return

        changes_detected = False

        for dev in devices:
            with Client(BROKER_ADDRESS) as c:
                st = get_status(c, dev)
            uc = int(st.get("UserCount", "0") or "0")

            with Client(BROKER_ADDRESS) as c:
                ids = find_all_user_ids(c, dev, uc)

            current = set(ids)
            prev = self.prev_users.get(dev.device_id, set())

            new_ids = current - prev
            deleted_ids = prev - current

            if new_ids:
                LOG.info(f"[{dev.device_id}] NEW enrollment: {new_ids}")
                changes_detected = True

            if deleted_ids:
                LOG.info(f"[{dev.device_id}] DELETED users: {deleted_ids}")
                changes_detected = True

                # Delete from all other devices
                for uid in deleted_ids:
                    for other_dev in devices:
                        if other_dev.device_id == dev.device_id:
                            continue
                        other_ids = self.prev_users.get(other_dev.device_id, set())
                        if uid in other_ids:
                            LOG.info(f"  Deleting user {uid} from {other_dev.device_id}...")
                            with Client(BROKER_ADDRESS) as c:
                                delete_user(c, other_dev, uid)

            self.prev_users[dev.device_id] = current

        # If any changes detected, run a deep sync to push all data
        if changes_detected:
            LOG.info("Changes detected — running deep sync...")
            self.deep_sync()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print()
    print("=" * 60)
    print("  WebSocketSDK Deep Sync Engine (FINAL)")
    print("  - Compares actual data, not just user IDs")
    print("  - Pushes missing fingerprints/face/card/photo")
    print("  - Deletes sync across all devices")
    print("  - Both devices are MASTER")
    print(f"  Broker: {BROKER_ADDRESS} | Poll: {POLL_INTERVAL}s")
    print("=" * 60)
    print()

    engine = SyncEngine()

    LOG.info("Waiting for 2+ devices...")
    while True:
        devs = engine.get_devices()
        if len(devs) >= 2:
            LOG.info(f"Found {len(devs)} devices:")
            for d in devs:
                LOG.info(f"  {d.device_id} - {d.attributes.get('product_name','?')}")
            break
        time.sleep(5)

    # Full deep sync on startup
    engine.deep_sync()

    LOG.info("")
    LOG.info(f"Monitoring every {POLL_INTERVAL}s...")
    LOG.info("Enroll/delete on any device -> syncs to all others.")
    LOG.info("Ctrl+C to stop.")

    while True:
        try:
            time.sleep(POLL_INTERVAL)
            engine.monitor()
        except KeyboardInterrupt:
            LOG.info("Stopped.")
            break
        except Exception as e:
            LOG.error(f"Error: {e}")
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
