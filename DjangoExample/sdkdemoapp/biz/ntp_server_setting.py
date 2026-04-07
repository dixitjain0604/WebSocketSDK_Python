from typing import Optional, Tuple

from devicebroker.device_cmd.messages import GenericRequest, GenericResponse
from devicebroker.device_cmd.m50 import device_info
from . import connection
from ..forms import NtpServerSettingForm

class NtpServerSettingModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def format_timezone_offset_str(offset : int) -> str:
    if offset >= 0:
        sign = "+"
    else:
        sign = "-"
        offset = -offset

    return f"{sign}{offset // 60 :02d}:{offset % 60 :02d}"

def parse_timezone_offset_str(tz_offset : str) -> Optional[int]:
    try:
        if tz_offset == "":
            return 0

        negative = False
        if tz_offset.startswith('+'):
            tz_offset = tz_offset[1:]
        elif tz_offset.startswith('-'):
            tz_offset = tz_offset[1:]
            negative = True

        i = tz_offset.find(':')
        if i >= 0:
            minutes = int(tz_offset[i+1:])
            if minutes < 0 or minutes >= 60:
                return None
            tz_offset = tz_offset[:i]
        else:
            minutes = 0

        hours = int(tz_offset)

        val = hours * 60 + minutes
        if negative:
            val = -val
        return val

    except ValueError:
        return None

def read_setting(connection_id : int, form : NtpServerSettingForm, model : NtpServerSettingModel) -> NtpServerSettingForm:
    try:
        with connection.open() as client:
            resp : device_info.GetDeviceInfoExtResponse = device_info.GetDeviceInfoExtRequest(
                device_info.DeviceInfoExtParamType.NTPServer
            ).transact(client, connection_id)

        if resp.has_succeeded():
            data = {
                "server_address": resp.value1,
                "timezone"      : format_timezone_offset_str(int(resp.value2)),
                "sync_interval" : resp.value3,
            }
            form = NtpServerSettingForm(data)

            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading setting: ({ex})"

    return form

def write_setting(connection_id : int, form : NtpServerSettingForm, model : NtpServerSettingModel) -> NtpServerSettingForm:
    server_address = form.cleaned_data["server_address"]

    if (tz_offset := parse_timezone_offset_str(form.cleaned_data["timezone"])) is None:
        model.error_msg = "Entered time zone offset value is invalid."
        return form

    if (interval := form.cleaned_data["sync_interval"]) < 60:
        model.error_msg = "Sync interval should be greater than or equal to 60."
        return form

    try:
        with connection.open() as client:
            resp : device_info.SetDeviceInfoExtResponse = device_info.SetDeviceInfoExtRequest(
                device_info.DeviceInfoExtParamType.NTPServer,
                server_address,
                str(tz_offset),
                str(interval)
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return form
