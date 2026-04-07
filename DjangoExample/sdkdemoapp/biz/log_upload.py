import base64
import datetime
from typing import Optional, TypeVar

from ..models import AttendanceLog, ManagementLog

_T = TypeVar('T')

def to_int_optional(value : Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)

def to_bool(value : Optional[str], default : _T = False) -> bool | _T:
    if value is None:
        return default
    if value == "Yes" or value == "True" or value == "Y" or value == "T":
        return True
    elif value == "No" or value == "False" or value == "N" or value == "F":
        return False
    else:
        return default

def base64_to_bin(value : Optional[str]) -> Optional[bytes]:
    if value is None or value == "":
        return None
    return base64.b64decode(value)

def to_datetime(value : Optional[str], default : _T = None) -> datetime.datetime | _T:
    if value is None:
        return default

    try:
        date_portion_end = value.find("-T")
        if date_portion_end < 0:
            return default

        year, month, day = value[: date_portion_end].split("-")

        value = value[date_portion_end + 2 :]
        if not value.endswith("Z"):
            return default

        hour, minute, second = value[: -1].split(":")

        return datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    except:
        return default

def save_device_log(contents : dict):
    event_type : str = contents["Event"]
    if event_type.startswith("TimeLog"):
        o : AttendanceLog = AttendanceLog()
        o.device_id        = contents["DeviceSerialNo"]
        o.log_id           = int(contents["LogID"])
        o.time             = to_datetime(contents.get("Time", None))
        o.user_id          = to_int_optional(contents.get("UserID", None))
        o.timezone_offset  = to_int_optional(contents.get("UtcTimezoneMinutes", None))
        o.attend_status    = contents.get("AttendStat", None)
        o.action           = contents.get("Action", None)
        o.job_code         = to_int_optional(contents.get("JobCode", None))
        o.body_temperature = to_int_optional(contents.get("BodyTemperature100", None))
        o.attend_only      = to_bool(contents.get("AttendOnly", False))
        o.expired          = to_bool(contents.get("Expired", False))
        o.latitude         = contents.get("Latitude", None)
        o.longitude        = contents.get("Longitude", None)

        if to_bool(contents.get("Photo", None)):
            o.photo = base64_to_bin(contents["LogImage"])
        else:
            o.photo = None

        o.save()

    elif event_type.startswith("AdminLog"):
        o : ManagementLog = ManagementLog()
        o.device_id         = contents["DeviceSerialNo"]
        o.log_id            = int(contents["LogID"])
        o.time              = to_datetime(contents.get("Time", None))
        o.admin_id          = to_int_optional(contents.get("AdminID", None))
        o.employee_id       = to_int_optional(contents.get("UserID", None))
        o.action            = contents.get("Action", None)
        o.result            = to_int_optional(contents.get("Stat", None))

        o.save()
