from dataclasses import dataclass
from enum import Enum
from typing import Final
from xml.etree import ElementTree

from .. import messages

CENTER_SCREEN_MSG_LEN : Final[int] = 100

@dataclass
class CenterScreenMessageSetting:
    message         : str   = ""
    color           : int   = 0
    border_color    : int   = 0
    disable_verify  : bool  = False

class GetCenterScreenMessageSettingResponse:
    setting : CenterScreenMessageSetting

    def parse(self, doc : ElementTree.Element):
        message = messages.parse_base64_string(doc, "center_screen_message")
        if (index := message.find('\x00')) >= 0:
            message = message[: index]

        self.setting = CenterScreenMessageSetting(
            message         = message,
            color           = messages.parse_int(doc, "center_screen_message_color", default = 0, base = 16) & 0xFFFFFF,
            border_color    = messages.parse_int(doc, "center_screen_message_border_color", default = 0, base = 16) & 0xFFFFFF,
            disable_verify  = bool(messages.parse_int(doc, "verify_disable"))
        )

class GetCenterScreenMessageSettingRequest(messages.GenericRequest):
    response_type = GetCenterScreenMessageSettingResponse

    def __init__(self):
        super().__init__("GetCenterScreenMessage")

class SetCenterScreenMessageSettingRequest(messages.GenericRequest):
    setting : CenterScreenMessageSetting

    def __init__(self, setting : CenterScreenMessageSetting):
        super().__init__("SetCenterScreenMessage")
        self.setting = setting

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        
        message = self.setting.message
        if len(message) > CENTER_SCREEN_MSG_LEN:
            message = message[:CENTER_SCREEN_MSG_LEN]
        else:
            message = message + "\x00" * (CENTER_SCREEN_MSG_LEN - len(message))
        result.append(messages.make_base64_node("center_screen_message", message.encode(encoding = "unicodelittleunmarked")))

        result.append(messages.make_text_node("center_screen_message_color", f"FF{self.setting.color:06X}"))
        result.append(messages.make_text_node("center_screen_message_border_color", f"FF{self.setting.border_color:06X}"))
        result.append(messages.make_int_node("verify_disable", int(self.setting.disable_verify)))
        return result

class RtspResolution(Enum):
    _1920x1080  = 0
    _1280x720   = 1
    _960x540    = 2
    _640x360    = 3

class RtspBitrate(Enum):
    Default     = 0
    _1          = 1
    _2          = 2
    _3          = 3
    _4          = 4
    _5          = 5
    _6          = 6
    _7          = 7
    _8          = 8
    _9          = 9
    _10         = 10
    _11         = 11
    _12         = 12
    _13         = 13
    _14         = 14
    _15         = 15
    _16         = 16
    _17         = 17
    _18         = 18
    _19         = 19
    _20         = 20

@dataclass
class RtspSetting:
    enabled     : bool = False
    resolution  : RtspResolution = RtspResolution(0)
    bitrate     : RtspBitrate = RtspBitrate(0)

class GetVideoStreamingSettingResponse:
    setting : RtspSetting

    def parse(self, doc : ElementTree.Element):
        self.setting = RtspSetting()
        self.setting.enabled    = bool(messages.parse_int(doc, "rtsp_enable"))
        self.setting.resolution = RtspResolution(messages.parse_int(doc, "rtsp_resolution"))
        self.setting.bitrate    = RtspBitrate(messages.parse_int(doc, "rtsp_bitrate_mbps"))

class GetVideoStreamingSettingRequest(messages.GenericRequest):
    response_type = GetVideoStreamingSettingResponse

    def __init__(self):
        super().__init__("GetVideoStreamSetting")

class SetVideoStreamingSettingRequest(messages.GenericRequest):
    setting : RtspSetting

    def __init__(self, setting : RtspSetting):
        super().__init__("SetVideoStreamSetting")
        self.setting = setting

    def to_xml(self) -> ElementTree.Element:
        doc = super().to_xml()
        doc.append(messages.make_int_node("rtsp_enable", int(self.setting.enabled)))
        doc.append(messages.make_int_node("rtsp_resolution", self.setting.resolution.value))
        doc.append(messages.make_int_node("rtsp_bitrate_mbps", self.setting.bitrate.value))
        return doc
