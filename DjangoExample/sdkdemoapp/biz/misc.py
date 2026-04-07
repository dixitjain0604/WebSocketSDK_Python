from dataclasses import dataclass
from typing import Optional
from xml.etree import ElementTree

from devicebroker.device_cmd.m50 import misc as M
from . import connection
from ..forms import CenterMessageSettingForm, VideoStreamingSettingForm

class CenterMessageSettingModel:
    error_msg   : Optional[str] = None
    info_msg    : Optional[str] = None

def parse_color(value : Optional[str]) -> Optional[int]:
    if not value:
        return None

    try:
        t = int(value, base = 16)
        if t < 0 or t >= 0x1000000:
            return None
        return t
    except:
        return None

def get_center_message_setting(connection_id : int, form : CenterMessageSettingForm, model : CenterMessageSettingModel) -> CenterMessageSettingForm:
    try:
        with connection.open() as client:
            resp : M.GetCenterScreenMessageSettingResponse = M.GetCenterScreenMessageSettingRequest().transact(client, connection_id)

        data = {
            "message"           : resp.setting.message,
            "color"             : f"{resp.setting.color:06X}",
            "border_color"      : f"{resp.setting.border_color:06X}",
            "disable_verify"    : int(resp.setting.disable_verify),
        }
        form = CenterMessageSettingForm(data)

        model.info_msg = "Successfully retrieved setting."

    except Exception as ex:
        model.error_msg = f"Error occurred while reading setting: ({ex})"

    return form

def set_center_message_setting(connection_id : int, form : CenterMessageSettingForm, model : CenterMessageSettingModel) -> CenterMessageSettingForm:
    setting = M.CenterScreenMessageSetting()
    setting.message = form.cleaned_data["message"] or ""

    setting.color = parse_color(form.cleaned_data["color"])
    if setting.color is None:
        model.error_msg = "Please input a valid color value."
        return form

    setting.border_color = parse_color(form.cleaned_data["border_color"])
    if setting.border_color is None:
        model.error_msg = "Please input a valid border color value."
        return form

    if not (t := form.cleaned_data["disable_verify"]):
        model.error_msg = "Please select whether to disable verify or not."
        return form
    setting.disable_verify = bool(int(t))

    try:
        with connection.open() as client:
            resp = M.SetCenterScreenMessageSettingRequest(setting).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return form

class VideoStreamingSettingModel:
    error_msg   : Optional[str] = None
    info_msg    : Optional[str] = None

def get_video_streaming_setting(connection_id : int, form : VideoStreamingSettingForm, model : VideoStreamingSettingModel) -> VideoStreamingSettingForm:
    try:
        with connection.open() as client:
            resp : M.GetVideoStreamingSettingResponse = M.GetVideoStreamingSettingRequest().transact(client, connection_id)

        data = {
            "enabled"       : str(int(resp.setting.enabled)),
            "resolution"    : str(resp.setting.resolution.value),
            "bitrate"       : str(resp.setting.bitrate.value),
        }
        form = VideoStreamingSettingForm(data)

        model.info_msg = "Successfully retrieved setting."

    except Exception as ex:
        model.error_msg = f"Error occurred while reading setting: ({ex})"

    return form

def set_video_streaming_setting(connection_id : int, form : VideoStreamingSettingForm, model : VideoStreamingSettingModel) -> VideoStreamingSettingForm:
    setting = M.RtspSetting()

    if not(temp := form.cleaned_data["enabled"]):
        model.error_msg = "Please select whether to enable video streaming or not."
        return form
    setting.enabled = bool(int(temp))

    if not (temp := form.cleaned_data["resolution"]):
        model.error_msg = "Please select resolution."
        return form
    setting.resolution = M.RtspResolution(int(temp))

    if not (temp := form.cleaned_data["bitrate"]):
        model.error_msg = "Please select bitrate."
        return form
    setting.bitrate = M.RtspBitrate(int(temp))

    try:
        with connection.open() as client:
            resp = M.SetVideoStreamingSettingRequest(setting).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return form
