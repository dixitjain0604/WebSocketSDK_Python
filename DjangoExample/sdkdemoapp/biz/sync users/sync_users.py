"""
Business logic for syncing users across devices.
Place this file at: DjangoExample/sdkdemoapp/biz/sync_users.py
"""

import time
import base64
from xml.etree import ElementTree
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from . import connection
from devicebroker.client import Client


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CMD_DELAY = 0.5


# ---------------------------------------------------------------------------
# XML helpers (Tempus-TC5000 compatible)
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


def send_cmd(client: Client, conn_id: int, xml: str) -> Optional[ElementTree.Element]:
    time.sleep(CMD_DELAY)
    try:
        raw = client.execute_command(conn_id, xml)
    except Exception:
        return None
    return parse(raw)


# ---------------------------------------------------------------------------
# User data record
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

    def has_card(self): return bool(self.card and self.card != "AAAAAA==" and self.card != "0")
    def has_password(self): return bool(self.password and self.password.strip())
    def has_qr(self): return bool(self.qr and self.qr != "AAAAAA==" and self.qr != "0")
    def has_face(self): return bool(self.face and len(self.face) > 10)
    def has_photo(self): return bool(self.photo and len(self.photo) > 10)


@dataclass
class DeviceInfo:
    device_id:     str = ""
    connection_id: int = 0
    terminal_type: str = ""
    product_name:  str = ""
    user_count:    Optional[int] = None
    fp_count:      Optional[int] = None
    face_count:    Optional[int] = None
    card_count:    Optional[int] = None


# ---------------------------------------------------------------------------
# Get device info with status
# ---------------------------------------------------------------------------
def get_devices_with_status() -> List[DeviceInfo]:
    """Get all online devices with their user/fingerprint/face counts."""
    result = []
    try:
        with connection.open() as c:
            raw_devices = c.get_all_online_devices()

            for d in raw_devices:
                info = DeviceInfo(
                    device_id=d.device_id,
                    connection_id=d.connection_id,
                    terminal_type=d.attributes.get("terminal_type", ""),
                    product_name=d.attributes.get("product_name", ""),
                )

                resp = send_cmd(c, d.connection_id, make_xml({"Request": "GetDeviceStatusAll"}))
                if resp is not None:
                    st = dump(resp)
                    try: info.user_count = int(st.get("UserCount", "0") or "0")
                    except: pass
                    try: info.fp_count = int(st.get("FpCount", "0") or "0")
                    except: pass
                    try: info.face_count = int(st.get("FaceCount", "0") or "0")
                    except: pass
                    try: info.card_count = int(st.get("CardCount", "0") or "0")
                    except: pass

                result.append(info)
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# Find all user IDs on a device
# ---------------------------------------------------------------------------
def find_user_ids(client: Client, conn_id: int, user_count: int) -> List[str]:
    if user_count <= 0:
        return []

    # Method 1: Enumeration
    resp = send_cmd(client, conn_id, make_xml({"Request": "GetFirstUserData"}))
    if resp is not None and not is_fail(resp) and has_data(resp, "UserID"):
        ids = []
        d = dump(resp)
        uid = d.get("UserID", "")
        if uid:
            ids.append(uid)
        more = d.get("More", "No")
        while more == "Yes":
            resp = send_cmd(client, conn_id, make_xml({"Request": "GetNextUserData"}))
            if resp is None or is_fail(resp):
                break
            d = dump(resp)
            uid = d.get("UserID", "")
            if uid:
                ids.append(uid)
            more = d.get("More", "No")
        if len(ids) >= user_count:
            return ids

    # Method 2: Brute-force
    scan_max = max(user_count * 15, 100)
    found = []
    for i in range(1, scan_max + 1):
        resp = send_cmd(client, conn_id, make_xml({"Request": "GetUserData", "UserID": str(i)}))
        if resp is not None and not is_fail(resp) and has_data(resp, "UserID"):
            found.append(str(i))
        if len(found) >= user_count:
            break
    return found


# ---------------------------------------------------------------------------
# Pull complete user
# ---------------------------------------------------------------------------
def pull_user(client: Client, conn_id: int, user_id: str) -> Optional[FullUser]:
    resp = send_cmd(client, conn_id, make_xml({"Request": "GetUserData", "UserID": user_id}))
    if resp is None or is_fail(resp):
        return None

    d = dump(resp)
    user = FullUser(
        user_id=user_id,
        name=d.get("Name", "") or d.get("n", ""),
        privilege=d.get("Privilege", ""),
        department=d.get("Depart", ""),
        enabled=d.get("Enabled", ""),
        timeset1=d.get("TimeSet1", ""), timeset2=d.get("TimeSet2", ""),
        timeset3=d.get("TimeSet3", ""), timeset4=d.get("TimeSet4", ""),
        timeset5=d.get("TimeSet5", ""),
        period_used=d.get("UserPeriod_Used", ""),
        period_start=d.get("UserPeriod_Start", ""),
        period_end=d.get("UserPeriod_End", ""),
        card=d.get("Card", ""), password=d.get("PWD", ""), qr=d.get("QR", ""),
    )

    # All 10 finger slots
    for fno in range(10):
        resp = send_cmd(client, conn_id, make_xml({
            "Request": "GetFingerData", "UserID": user_id,
            "FingerNo": str(fno), "FingerOnly": "1",
        }))
        if resp is not None and not is_fail(resp) and has_data(resp, "FingerData"):
            tpl = val(resp, "FingerData")
            duress = val(resp, "Duress", "No")
            if len(tpl) > 10:
                user.fingers[fno] = (tpl, duress)

    # Face
    resp = send_cmd(client, conn_id, make_xml({"Request": "GetFaceData", "UserID": user_id}))
    if resp is not None and not is_fail(resp) and has_data(resp, "FaceData"):
        user.face = val(resp, "FaceData")

    # Photo
    resp = send_cmd(client, conn_id, make_xml({"Request": "GetUserPhoto", "UserID": user_id}))
    if resp is not None and not is_fail(resp) and has_data(resp, "PhotoData"):
        user.photo = val(resp, "PhotoData")
        try: user.photo_size = str(len(base64.b64decode(user.photo)))
        except: pass

    # Card (dedicated)
    if not user.has_card():
        resp = send_cmd(client, conn_id, make_xml({"Request": "GetUserCardNo", "UserID": user_id}))
        if resp is not None and not is_fail(resp):
            cn = val(resp, "CardNo")
            if cn and cn != "AAAAAA==":
                user.card = cn

    # Password (dedicated)
    if not user.has_password():
        resp = send_cmd(client, conn_id, make_xml({"Request": "GetUserPassword", "UserID": user_id}))
        if resp is not None and not is_fail(resp):
            pw = val(resp, "Password")
            if pw: user.password = pw

    # QR (dedicated)
    if not user.has_qr():
        resp = send_cmd(client, conn_id, make_xml({"Request": "GetUserQR", "UserID": user_id}))
        if resp is not None and not is_fail(resp):
            qr = val(resp, "QR")
            if qr and qr != "AAAAAA==":
                user.qr = qr

    return user


# ---------------------------------------------------------------------------
# Merge two user records
# ---------------------------------------------------------------------------
def merge_users(a: FullUser, b: FullUser) -> FullUser:
    m = FullUser(user_id=a.user_id)
    m.name = a.name or b.name
    m.privilege = a.privilege or b.privilege
    m.department = a.department or b.department
    m.enabled = a.enabled or b.enabled
    m.timeset1 = a.timeset1 or b.timeset1
    m.timeset2 = a.timeset2 or b.timeset2
    m.timeset3 = a.timeset3 or b.timeset3
    m.timeset4 = a.timeset4 or b.timeset4
    m.timeset5 = a.timeset5 or b.timeset5
    m.period_used = a.period_used or b.period_used
    m.period_start = a.period_start or b.period_start
    m.period_end = a.period_end or b.period_end
    m.card = a.card if a.has_card() else b.card
    m.password = a.password if a.has_password() else b.password
    m.qr = a.qr if a.has_qr() else b.qr
    m.fingers = dict(a.fingers)
    for fno, data in b.fingers.items():
        if fno not in m.fingers:
            m.fingers[fno] = data
    m.face = a.face if a.has_face() else b.face
    m.photo = a.photo if a.has_photo() else b.photo
    m.photo_size = a.photo_size if a.has_photo() else b.photo_size
    return m


# ---------------------------------------------------------------------------
# Compare what's missing
# ---------------------------------------------------------------------------
def needs_sync(dev_user: Optional[FullUser], master: FullUser) -> dict:
    needs = {"profile": False, "fingers": [], "face": False, "photo": False}
    if dev_user is None:
        needs["profile"] = True
        needs["fingers"] = list(master.fingers.keys())
        needs["face"] = master.has_face()
        needs["photo"] = master.has_photo()
        return needs
    if master.name and master.name != dev_user.name: needs["profile"] = True
    if master.has_card() and not dev_user.has_card(): needs["profile"] = True
    if master.has_password() and not dev_user.has_password(): needs["profile"] = True
    if master.has_qr() and not dev_user.has_qr(): needs["profile"] = True
    for fno in master.fingers:
        if fno not in dev_user.fingers:
            needs["fingers"].append(fno)
    if master.has_face() and not dev_user.has_face(): needs["face"] = True
    if master.has_photo() and not dev_user.has_photo(): needs["photo"] = True
    return needs


# ---------------------------------------------------------------------------
# Push functions
# ---------------------------------------------------------------------------
def push_profile(client: Client, conn_id: int, user: FullUser) -> bool:
    tags = {"Request": "SetUserData", "UserID": user.user_id, "Type": "Set", "AllowNoCertificate": "Yes"}
    if user.name:
        tags["Name"] = user.name
        tags["n"] = user.name
    for k, v in [("Privilege", user.privilege), ("Enabled", user.enabled),
                 ("TimeSet1", user.timeset1), ("TimeSet2", user.timeset2),
                 ("TimeSet3", user.timeset3), ("TimeSet4", user.timeset4),
                 ("TimeSet5", user.timeset5), ("UserPeriod_Used", user.period_used),
                 ("UserPeriod_Start", user.period_start), ("UserPeriod_End", user.period_end)]:
        if v: tags[k] = v
    if user.has_card(): tags["Card"] = user.card
    if user.has_password(): tags["PWD"] = user.password
    if user.has_qr(): tags["QR"] = user.qr
    if user.has_face(): tags["FaceData"] = user.face
    resp = send_cmd(client, conn_id, make_xml(tags))
    return resp is not None and not is_fail(resp)


def push_finger(client: Client, conn_id: int, user_id: str, fno: int,
                template: str, duress: str, privilege: str) -> bool:
    root = ElementTree.Element("Message")
    for tag, text in [("Request", "SetFingerData"), ("UserID", user_id),
                      ("Privilege", privilege or "User"), ("FingerNo", str(fno)),
                      ("DuplicationCheck", "1"), ("Duress", "1" if duress == "Yes" else "0")]:
        el = ElementTree.SubElement(root, tag)
        el.text = text
    fd = ElementTree.SubElement(root, "FingerData")
    fd.text = template
    xml = ElementTree.tostring(root, encoding="unicode")
    resp = send_cmd(client, conn_id, xml)
    return resp is not None and is_ok(resp)


def push_face(client: Client, conn_id: int, user_id: str, face: str, privilege: str) -> bool:
    resp = send_cmd(client, conn_id, make_xml({
        "Request": "SetFaceData", "UserID": user_id,
        "Privilege": privilege or "User", "DuplicationCheck": "Yes", "FaceData": face,
    }))
    return resp is not None and is_ok(resp)


def push_photo(client: Client, conn_id: int, user_id: str, photo: str, size: str) -> bool:
    resp = send_cmd(client, conn_id, make_xml({
        "Request": "SetUserPhoto", "UserID": user_id, "PhotoSize": size, "PhotoData": photo,
    }))
    return resp is not None and is_ok(resp)


# ---------------------------------------------------------------------------
# Decode name for display
# ---------------------------------------------------------------------------
def decode_name(b64: str) -> str:
    if not b64: return "(no name)"
    try: return base64.b64decode(b64).decode("utf-16-le").rstrip("\x00")
    except: return b64[:20]


# ---------------------------------------------------------------------------
# MAIN SYNC FUNCTION — called from view
# ---------------------------------------------------------------------------
def run_sync(device_ids_and_conns: List[Tuple[str, int]]) -> List[str]:
    """
    Run deep sync across specified devices.
    device_ids_and_conns: list of (device_id, connection_id) tuples.
    Returns a list of log strings for display.
    """
    log = []

    if len(device_ids_and_conns) < 2:
        log.append("ERROR: Need at least 2 devices to sync.")
        return log

    log.append("=" * 55)
    log.append("DEEP SYNC STARTING")
    log.append(f"Devices: {[d[0] for d in device_ids_and_conns]}")
    log.append("=" * 55)

    # Phase 1: Get user counts
    dev_counts: Dict[str, int] = {}
    for dev_id, conn_id in device_ids_and_conns:
        with connection.open() as c:
            resp = send_cmd(c, conn_id, make_xml({"Request": "GetDeviceStatusAll"}))
            if resp:
                st = dump(resp)
                uc = int(st.get("UserCount", "0") or "0")
                dev_counts[dev_id] = uc
                log.append(f"[{dev_id}] Users={uc} FP={st.get('FpCount','0')} "
                          f"Face={st.get('FaceCount','0')} Card={st.get('CardCount','0')}")

    # Phase 2: Find all user IDs
    dev_ids: Dict[str, List[str]] = {}
    for dev_id, conn_id in device_ids_and_conns:
        with connection.open() as c:
            ids = find_user_ids(c, conn_id, dev_counts.get(dev_id, 0))
        dev_ids[dev_id] = ids
        log.append(f"[{dev_id}] User IDs: {ids}")

    # Phase 3: Master set
    all_ids: Set[str] = set()
    id_source: Dict[str, Tuple[str, int]] = {}
    for dev_id, conn_id in device_ids_and_conns:
        for uid in dev_ids.get(dev_id, []):
            all_ids.add(uid)
            if uid not in id_source:
                id_source[uid] = (dev_id, conn_id)

    log.append(f"")
    log.append(f"Master set: {sorted(all_ids)} ({len(all_ids)} users)")

    if not all_ids:
        log.append("No users found on any device. Nothing to sync.")
        return log

    # Phase 4: Pull full data from all devices
    all_data: Dict[str, Dict[str, Optional[FullUser]]] = {}
    for uid in sorted(all_ids):
        all_data[uid] = {}
        for dev_id, conn_id in device_ids_and_conns:
            if uid in dev_ids.get(dev_id, []):
                log.append(f"Pulling user {uid} from {dev_id}...")
                with connection.open() as c:
                    user_data = pull_user(c, conn_id, uid)
                all_data[uid][dev_id] = user_data
                if user_data:
                    log.append(f"  '{decode_name(user_data.name)}': "
                              f"{len(user_data.fingers)} finger(s), "
                              f"face={'Y' if user_data.has_face() else 'N'}, "
                              f"photo={'Y' if user_data.has_photo() else 'N'}")
            else:
                all_data[uid][dev_id] = None

    # Phase 5: Merge into master records
    master_records: Dict[str, FullUser] = {}
    for uid in sorted(all_ids):
        records = [v for v in all_data[uid].values() if v is not None]
        if not records:
            continue
        master = records[0]
        for other in records[1:]:
            master = merge_users(master, other)
        master_records[uid] = master

    # Phase 6: Compare and push
    log.append("")
    log.append("=" * 55)
    log.append("PUSHING MISSING DATA")
    log.append("=" * 55)

    total_ops = 0
    for dev_id, conn_id in device_ids_and_conns:
        for uid in sorted(all_ids):
            master = master_records.get(uid)
            if not master:
                continue

            dev_record = all_data[uid].get(dev_id)
            diff = needs_sync(dev_record, master)
            needs_anything = diff["profile"] or diff["fingers"] or diff["face"] or diff["photo"]

            if not needs_anything:
                continue

            dname = decode_name(master.name)
            log.append(f"")
            log.append(f"[{dev_id}] User {uid} '{dname}' NEEDS: "
                      f"profile={diff['profile']}, fingers={diff['fingers']}, "
                      f"face={diff['face']}, photo={diff['photo']}")

            # Push profile
            with connection.open() as c:
                ok = push_profile(c, conn_id, master)
            log.append(f"[{dev_id}]   Profile: {'OK' if ok else 'FAILED'}")
            if not ok:
                continue
            total_ops += 1

            # Push fingers
            for fno in diff["fingers"]:
                if fno in master.fingers:
                    template, duress = master.fingers[fno]
                    with connection.open() as c:
                        ok = push_finger(c, conn_id, uid, fno, template, duress, master.privilege)
                    log.append(f"[{dev_id}]   Finger {fno}: {'OK' if ok else 'FAILED'}")
                    total_ops += 1

            # Push face
            if diff["face"] and master.has_face():
                with connection.open() as c:
                    ok = push_face(c, conn_id, uid, master.face, master.privilege)
                log.append(f"[{dev_id}]   Face: {'OK' if ok else 'FAILED'}")
                total_ops += 1

            # Push photo
            if diff["photo"] and master.has_photo():
                with connection.open() as c:
                    ok = push_photo(c, conn_id, uid, master.photo, master.photo_size)
                log.append(f"[{dev_id}]   Photo: {'OK' if ok else 'FAILED'}")
                total_ops += 1

    # Phase 7: Verify
    log.append("")
    log.append("=" * 55)
    log.append(f"SYNC COMPLETE — {total_ops} operations")
    log.append("VERIFICATION:")
    for dev_id, conn_id in device_ids_and_conns:
        with connection.open() as c:
            resp = send_cmd(c, conn_id, make_xml({"Request": "GetDeviceStatusAll"}))
            if resp:
                st = dump(resp)
                log.append(f"  [{dev_id}] Users={st.get('UserCount','?')} "
                          f"FP={st.get('FpCount','?')} Face={st.get('FaceCount','?')} "
                          f"Card={st.get('CardCount','?')}")
    log.append("=" * 55)

    return log
