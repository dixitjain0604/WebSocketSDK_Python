from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from xml.etree import ElementTree

from devicebroker.device_cmd.m50 import device_limits

from .. import messages

class GetDepartmentResponse(messages.GenericResponse):
    name : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.name = messages.parse_base64_string(doc, "Name")

class GetDepartmentRequest(messages.GenericRequest):
    response_type = GetDepartmentResponse
    depart_no : int

    def __init__(self, depart_no : int):
        super().__init__("GetDepartment")
        self.depart_no = depart_no

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("DeptNo", self.depart_no))
        return result

class SetDepartmentRequest(messages.GenericRequest):
    depart_no   : int
    name        : str

    def __init__(self, depart_no : int, name : str):
        super().__init__("SetDepartment")
        self.depart_no  = depart_no
        self.name       = name

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("DeptNo", self.depart_no))
        result.append(messages.make_base64_node("Data", self.name.encode(encoding = "unicodelittleunmarked")))
        return result

class GetProxyDepartmentResponse(messages.GenericResponse):
    name : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.name = messages.parse_base64_string(doc, "Name")

class GetProxyDepartmentRequest(messages.GenericRequest):
    response_type = GetProxyDepartmentResponse
    depart_no : int

    def __init__(self, depart_no : int):
        super().__init__("GetProxyDept")
        self.depart_no = depart_no

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("ProxyNo", self.depart_no))
        return result

class SetProxyDepartmentRequest(messages.GenericRequest):
    depart_no   : int
    name        : str

    def __init__(self, depart_no : int, name : str):
        super().__init__("SetProxyDept")
        self.depart_no  = depart_no
        self.name       = name

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("ProxyNo", self.depart_no))
        result.append(messages.make_base64_node("Data", self.name.encode(encoding = "unicodelittleunmarked")))
        return result
    
@dataclass
class Bell:
    valid       : bool = False
    bell_type   : int  = 0
    hour        : int  = 0
    minute      : int  = 0

class GetBellSettingsResponse(messages.GenericResponse):
    ring_times  : int
    bells       : List[Bell]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.ring_times = messages.parse_int(doc, "BellRingTimes")
        count = messages.parse_int(doc, "BellCount")

        self.bells = list()
        for i in range(0, count):
            bell : Bell = Bell()

            data = messages.parse_str(doc, f"Bell_{i}");
            if data:
                try:
                    valid, bell_type, hour, minute = data.split(',')
                    bell.valid      = bool(int(valid.strip()))
                    bell.bell_type  = int(bell_type.strip())
                    bell.hour       = int(hour.strip())
                    bell.minute     = int(minute.strip())
                except ValueError:
                    pass

            self.bells.append(bell)

class GetBellSettingsRequest(messages.GenericRequest):
    response_type = GetBellSettingsResponse
    def __init__(self):
        super().__init__("GetBellTime")

class SetBellSettingsRequest(messages.GenericRequest):
    ring_times  : int
    bells       : List[Bell]

    def __init__(self, ring_times : int, bells : List[Bell]):
        super().__init__("SetBellTime")
        self.ring_times = ring_times
        self.bells      = bells

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("BellRingTimes", self.ring_times))
        result.append(messages.make_int_node("BellPeriod", 0))
        result.append(messages.make_int_node("BellCount", len(self.bells)))
        for i, bell in enumerate(self.bells):
            result.append(messages.make_text_node(f"Bell_{i}", f"{int(bell.valid)},{bell.bell_type},{bell.hour},{bell.minute}"))
        return result

class AttendStatus(Enum):
    DutyOn        = 0
    DutyOff       = 1
    OvertimeOn    = 2
    OvertimeOff   = 3
    In            = 4
    Out           = 5

@dataclass
class AutoAttendance:
    start_time  : int = 0
    end_time    : int = 0
    status      : AttendStatus = AttendStatus.DutyOn

class GetAutoAttendanceSettingsResponse(messages.GenericResponse):
    time_sections : List[AutoAttendance]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.time_sections = list()

        for i in range(0, device_limits.NUM_TR_TIMESECTIONS):
            item = AutoAttendance()
            data = messages.parse_str(doc, f"TimeSection_{i}")
            if data:
                try:
                    start, end, status = data.split(',')
                    item.start_time = int(start.strip())
                    item.end_time   = int(end.strip())
                    item.status     = AttendStatus(int(status.strip()))
                except ValueError:
                    pass
            self.time_sections.append(item)

class GetAutoAttendanceSettingsRequest(messages.GenericRequest):
    response_type = GetAutoAttendanceSettingsResponse
    def __init__(self):
        super().__init__("GetAutoAttendance")

class SetAutoAttendanceSettingsRequest(messages.GenericRequest):
    time_sections : List[AutoAttendance]

    def __init__(self, time_sections : List[AutoAttendance]):
        super().__init__("SetAutoAttendance")
        self.time_sections = time_sections

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        for i, section in enumerate(self.time_sections):
            result.append(messages.make_text_node(f"TimeSection_{i}", f"{section.start_time},{section.end_time},{section.status.value}"))
        return result
