from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from xml.etree import ElementTree

from devicebroker.device_cmd.m50 import device_limits

from .. import messages

@dataclass
class AccessTimeSection:
    start_time  : int   = 0
    end_time    : int   = 0

class GetAccessTimezoneResponse(messages.GenericResponse):
    time_sections : List[AccessTimeSection]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.time_sections = list()
        for i in range(0, device_limits.TIMESECTION_COUNT_PER_TIMEZONE):
            section = AccessTimeSection()

            data = messages.parse_str(doc, f"TimeSection_{i}")
            if data:
                try:
                    start, end = data.split(',')
                    section.start_time  = int(start.strip())
                    section.end_time    = int(end.strip())
                except ValueError:
                    pass

            self.time_sections.append(section)

class GetAccessTimezoneRequest(messages.GenericRequest):
    response_type = GetAccessTimezoneResponse
    timezone_no : int

    def __init__(self, timezone_no : int):
        super().__init__("GetAccessTimeZone")
        self.timezone_no = timezone_no

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("TimeZoneNo", self.timezone_no))
        return result

class SetAccessTimezoneRequest(messages.GenericRequest):
    timezone_no     : int
    time_sections   : List[AccessTimeSection]

    def __init__(self, timezone_no : int, time_sections : List[AccessTimeSection]):
        super().__init__("SetAccessTimeZone")
        self.timezone_no    = timezone_no
        self.time_sections  = time_sections

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("TimeZoneNo", self.timezone_no))
        for i, section in enumerate(self.time_sections):
            result.append(messages.make_text_node(f"TimeSection_{i}", f"{section.start_time},{section.end_time}"))
        return result

class LockControlMode(Enum):
    ForceOpen       = 1
    ForceClose      = 2
    NormalOpen      = 3
    AutoRecover     = 4
    Restart         = 5
    CancelWarning   = 6
    IllegalOpen     = 7

class GetLockControlModeResponse(messages.GenericResponse):
    mode : LockControlMode

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.mode = LockControlMode(messages.parse_int(doc, "Mode"))

class GetLockControlModeRequest(messages.GenericRequest):
    response_type = GetLockControlModeResponse

    def __init__(self):
        super().__init__("LockControlStatus")

class SetLockControlModeRequest(messages.GenericRequest):
    mode : LockControlMode

    def __init__(self, mode : LockControlMode):
        super().__init__("LockControl")
        self.mode = mode

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("Mode", self.mode.value))
        return result
