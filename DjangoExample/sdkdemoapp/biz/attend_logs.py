from dataclasses import dataclass
from typing import Optional
import urllib.parse

import devicebroker.device_cmd.m50.log as L
from . import connection
from ..forms import AttendLogsForm

@dataclass
class LogPosInfo:
    log_count   : int
    max_count   : int
    start_pos   : int

class AttendLogsModel:
    error_msg   : Optional[str]         = None
    info_msg    : Optional[str]         = None
    log         : Optional[L.TimeLog]   = None
    pos_info    : Optional[LogPosInfo]  = None

    def timezone_string(self) -> str:
        if self.log is None or self.log.timezone_offset is None:
            return ""

        val = self.log.timezone_offset
        if val >= 0:
            sign = '+'
        else:
            sign = '-'
            val = -val

        return f"UTC{sign}{val // 60 :02d}{val % 60 :02d}"

    def body_temperature_string(self) -> str:
        if self.log is None or self.log.body_temperature is None:
            return ""
        return f"{self.log.body_temperature :.2f}"

    def attendonly_string(self) -> str:
        if self.log is None:
            return ""
        return "Yes" if self.log.attend_only else "No"

    def expired_string(self) -> str:
        if self.log is None:
            return ""
        return "Yes" if self.log.expired else "No"

    def latitude_string(self) -> str:
        if self.log is None or self.log.latitude is None:
            return ""
        return self.log.latitude

    def longitude_string(self) -> str:
        if self.log is None or self.log.longitude is None:
            return ""
        return self.log.longitude

    def encoded_photo_data(self) -> str:
        if self.log is None or self.log.photo is None:
            return ""
        return urllib.parse.quote_from_bytes(self.log.photo)

def get_first_log(connection_id : int, form : AttendLogsForm, model : AttendLogsModel) -> AttendLogsForm:
    try:
        with connection.open() as client:
            resp : L.GetGlogResponse = L.GetFirstGlogRequest(
                user_id     = form.cleaned_data["user_id"],
                start_time  = form.cleaned_data["start_time"],
                end_time    = form.cleaned_data["end_time"]
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.log = resp.log
            data = form.cleaned_data
            data["next_log_id"] = resp.log.log_id + 1
            form = AttendLogsForm(data)
            model.info_msg = "Successfully retrieved log."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading log: ({ex})"

    return form

def get_next_log(connection_id : int, form : AttendLogsForm, model : AttendLogsModel) -> AttendLogsForm:
    if (log_id := form.cleaned_data["next_log_id"]) is None:
        model.error_msg = "Enter a log ID or click 'Get First Log' first to fetch a log."
        return form

    try:
        with connection.open() as client:
            resp : L.GetGlogResponse = L.GetNextGlogRequest(log_id).transact(client, connection_id)

        if resp.has_succeeded():
            model.log = resp.log
            data = form.cleaned_data
            data["next_log_id"] = resp.log.log_id + 1
            form = AttendLogsForm(data)
            model.info_msg = "Successfully retrieved log."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading log: ({ex})"

    return form

def get_log_pos_info(connection_id : int, form : AttendLogsForm, model : AttendLogsModel) -> AttendLogsForm:
    try:
        with connection.open() as client:
            resp : L.GetGlogPosInfoResponse = L.GetGlogPosInfoRequest().transact(client, connection_id)

        if resp.has_succeeded():
            model.pos_info = LogPosInfo(
                log_count = resp.log_count,
                max_count = resp.max_count,
                start_pos = resp.start_pos)
            model.info_msg = "Successfully retrieved pos info."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading pos info: ({ex})"

    return form

def delete_logs(connection_id : int, form : AttendLogsForm, model : AttendLogsModel) -> AttendLogsForm:
    if (log_id := form.cleaned_data["next_log_id"]) is None:
        model.error_msg = "Enter a log ID or click 'Get First Log' first to fetch a log."
        return form

    try:
        with connection.open() as client:
            resp = L.DeleteGlogWithPosRequest(log_id).transact(client, connection_id)

        if resp.has_succeeded():
            data = dict(form.cleaned_data)
            del data["next_log_id"]
            form = AttendLogsForm(data)

            model.info_msg = "Successfully deleted log(s)."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while deleting log: ({ex})"

    return form
