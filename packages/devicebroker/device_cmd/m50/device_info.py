from enum import Enum
from typing import Dict, List, Optional
from xml.etree import ElementTree

from .. import messages

class DeviceInfoParamType(Enum):
    ManagersNumber                      = 1
    MachineID                           = 2
    Language                            = 3
    LockReleaseTime                     = 4
    SLogWarning                         = 5
    GLogWarning                         = 6
    ReverifyTime                        = 7
    Baudrate                            = 8
    IdentifyMode                        = 9
    LockMode                            = 10
    DoorSensorType                      = 11
    DoorOpenTimeout                     = 12
    AutoSleepTime                       = 13
    EventSendType                       = 14
    WiegandFormat                       = 15
    CommPassword                        = 16
    UseProxyInput                       = 17
    ProxyDlgTimeout                     = 18
    SoundVolume                         = 19
    ShowRealtimeCamera                  = 20
    UseFailLog                          = 21
    FaceEngineThreshold                 = 22
    FaceEngineUseAntispoofing           = 23
    NeedWearingMask                     = 24
    SuggestWearingMask                  = 25
    UseMeasureTemperature               = 26
    UseVisitorMode                      = 27
    ShowRealtimeTemperature             = 28
    AbnormalTempDisableDoorOpen         = 29
    MeasuringDurationType               = 30
    MeasuringDistanceType               = 31
    TemperatureUnit                     = 32
    AbnormalTempThreshold_Celsius       = 33
    AbnormalTempThreshold_Fahrenheit    = 34
    UtcTimezoneMinutes                  = 35
    BackgroundColor                     = 36

class DeviceLanguage(Enum):
    English                 = 0
    Chinese_Simplified      = 1
    Chinese_Traditional     = 2
    Turkish                 = 3
    Korean                  = 4
    Indonesian              = 5
    Arabic                  = 6

class DoorSensorType(Enum):
    NoDoorSensor            = 0
    NormalOpen              = 1
    NormalClose             = 2

class EventSendType(Enum):
    Disabled                = 0
    Tcp                     = 1
    Rs485                   = 2

class WiegandOutputType(Enum):
    Wiegand26               = 0
    Wiegand34               = 1

class LockOperationMode(Enum):
    UnconditionalClose      = 0
    UnconditionalOpen       = 1
    AutoRecover             = 2

class VerifyMode(Enum):
    SystemDefault           = 0
    Any                     = 1
    Card_Finger             = 3
    Card_Password           = 7
    Finger_Password         = 8
    Finger_Card_Password    = 9
    Card_Face               = 11
    Face_Password           = 12
    Face_Card_Password      = 13
    Face_Finger             = 14


class GetDeviceInfoResponse(messages.GenericResponse):
    param_value : Optional[int] = None

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.param_value = messages.parse_int(doc, "Value", None)

class GetDeviceInfoRequest(messages.GenericRequest):
    response_type = GetDeviceInfoResponse
    param : DeviceInfoParamType

    def __init__(self, param : DeviceInfoParamType):
        super().__init__("GetDeviceInfo")
        self.param = param

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("ParamName", self.param.name))
        return result

class SetDeviceInfoRequest(messages.GenericRequest):
    param : DeviceInfoParamType
    value : int

    def __init__(self, param : DeviceInfoParamType, value : int):
        super().__init__("SetDeviceInfo")
        self.param = param
        self.value = value

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("ParamName", self.param.name))
        result.append(messages.make_int_node("Value", self.value))
        return result

class GetDeviceInfoAllResponse(messages.GenericResponse):
    device_info : Dict[DeviceInfoParamType, int]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.device_info = dict()
        for param in DeviceInfoParamType:
            val = messages.parse_int(doc, param.name, None)
            if val is not None:
                self.device_info[param] = val

class GetDeviceInfoAllRequest(messages.GenericRequest):
    response_type = GetDeviceInfoAllResponse

    def __init__(self):
        super().__init__("GetDeviceInfoAll")

class DeviceInfoExtParamType(Enum):
    WebServerUrl    = 1
    SendLogUrl      = 2
    DeviceName      = 3
    MobileNetwork   = 4
    NTPServer       = 5
    VPNServer       = 6
    GPS             = 7

class GetDeviceInfoExtResponse(messages.GenericResponse):
    value1 : str
    value2 : str
    value3 : str
    value4 : str
    value5 : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.value1 = messages.parse_str(doc, "Value1")
        self.value2 = messages.parse_str(doc, "Value2")
        self.value3 = messages.parse_str(doc, "Value3")
        self.value4 = messages.parse_str(doc, "Value4")
        self.value5 = messages.parse_str(doc, "Value5")

class GetDeviceInfoExtRequest(messages.GenericRequest):
    response_type = GetDeviceInfoExtResponse
    param   : DeviceInfoExtParamType

    def __init__(self, param : DeviceInfoExtParamType):
        super().__init__("GetDeviceInfoExt")
        self.param = param

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("ParamName", self.param.name))
        return result

class SetDeviceInfoExtRequest(messages.GenericRequest):
    param   : DeviceInfoExtParamType
    value1  : Optional[str] = None
    value2  : Optional[str] = None
    value3  : Optional[str] = None
    value4  : Optional[str] = None
    value5  : Optional[str] = None

    def __init__(
        self,
        param : DeviceInfoExtParamType,
        value1 : Optional[str] = None,
        value2 : Optional[str] = None,
        value3 : Optional[str] = None,
        value4 : Optional[str] = None,
        value5 : Optional[str] = None
    ):
        super().__init__("SetDeviceInfoExt")
        self.param = param
        self.value1 = value1
        self.value2 = value2
        self.value3 = value3
        self.value4 = value4
        self.value5 = value5

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("ParamName", self.param.name))
        if self.value1 is not None:
            result.append(messages.make_text_node("Value1", self.value1))
        if self.value2 is not None:
            result.append(messages.make_text_node("Value2", self.value2))
        if self.value3 is not None:
            result.append(messages.make_text_node("Value3", self.value3))
        if self.value4 is not None:
            result.append(messages.make_text_node("Value4", self.value4))
        if self.value5 is not None:
            result.append(messages.make_text_node("Value5", self.value5))
        return result
