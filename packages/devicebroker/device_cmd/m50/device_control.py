import datetime
from enum import Enum
from typing import Dict, Optional
from xml.etree import ElementTree

from .. import messages

class EnableDeviceRequest(messages.GenericRequest):
    enable : bool

    def __init__(self, enable : bool):
        super().__init__("EnableDevice")
        self.enable = enable

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_boolean_node("Enable", self.enable))
        return result

class GetTimeResponse(messages.GenericResponse):
    time : datetime.datetime

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.time = messages.parse_datetime(doc, "Time")
        if self.time is None:
            raise ValueError("Malformed datetime string.")

class GetTimeRequest(messages.GenericRequest):
    response_type = GetTimeResponse
    def __init__(self):
        super().__init__("GetTime")

class SetTimeRequest(messages.GenericRequest):
    time : datetime.datetime

    def __init__(self, time : datetime.datetime):
        super().__init__("SetTime")
        self.time = time

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_datetime_node("Time", self.time))
        return result
    
class DeviceStatusParamType(Enum):
    ManagerCount    = 1
    UserCount       = 2
    FaceCount       = 3
    FpCount         = 4
    CardCount       = 5
    PwdCount        = 6
    QRCount         = 7
    DoorStatus      = 8
    AlarmStatus     = 9

class DoorSensorStatus(Enum):
    Closed          = 0
    Open            = 1

class AlarmFlag(Enum):
    Duress          = 1
    Tamper          = 2
    IllegalOpen     = 4
    NoClose         = 8
    LogOverflow     = 16

class GetDeviceStatusResponse(messages.GenericResponse):
    param_value : Optional[int]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.param_value = messages.parse_int(doc, "Value", None)

class GetDeviceStatusRequest(messages.GenericRequest):
    response_type = GetDeviceStatusResponse
    param : DeviceStatusParamType

    def __init__(self, param : DeviceStatusParamType):
        super().__init__("GetDeviceStatus")
        self.param = param

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("ParamName", self.param.name))
        return result

class GetDeviceStatusAllResponse(messages.GenericResponse):
    device_status : Dict[DeviceStatusParamType, int]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.device_status = dict()
        for param in DeviceStatusParamType:
            val = messages.parse_int(doc, param.name, None)
            if val is not None:
                self.device_status[param] = val

class GetDeviceStatusAllRequest(messages.GenericRequest):
    response_type = GetDeviceStatusAllResponse

    def __init__(self):
        super().__init__("GetDeviceStatusAll")

class SetTrIconRequest(messages.GenericRequest):
    response_type = messages.GenericResponse
    icon_no     : int
    icon_status : int
    need_delete : bool
    icon_data  : bytes

    def __init__(self, icon_no : int, icon_status : int, need_delete : bool, icon_data : bytes):
        super().__init__("SetTrIcon")
        self.icon_no    = icon_no
        self.icon_status = icon_status
        self.need_delete = need_delete
        self.icon_data = icon_data

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("IconNo", self.icon_no))
        result.append(messages.make_int_node("Status", self.icon_status))
        result.append(messages.make_boolean_node("Delete", self.need_delete))
        if not self.need_delete:
            result.append(messages.make_int_node("IconSize", len(self.icon_data)))
            result.append(messages.make_base64_node("IconData", self.icon_data))
        return result
