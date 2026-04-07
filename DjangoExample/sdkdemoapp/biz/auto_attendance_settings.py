from typing import List, Optional

from devicebroker.device_cmd.m50 import attendance_setting, device_limits
from . import connection
from ..forms import AutoAttendanceSettingsForm
from .utils import format_hh_mm, parse_hh_mm

class AutoAttendanceSettingsModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_auto_attendance_settings(connection_id : int, form : AutoAttendanceSettingsForm, model : AutoAttendanceSettingsModel) -> AutoAttendanceSettingsForm:
    try:
        with connection.open() as client:
            resp : attendance_setting.GetAutoAttendanceSettingsResponse = attendance_setting.GetAutoAttendanceSettingsRequest().transact(client, connection_id)

        if resp.has_succeeded():
            data = {}
            for i, section in enumerate(resp.time_sections):
                data[f"start_{i+1}"]    = format_hh_mm(section.start_time)
                data[f"end_{i+1}"]      = format_hh_mm(section.end_time)
                data[f"status_{i+1}"]   = section.status.name
            form = AutoAttendanceSettingsForm(data)

            model.info_msg = "Successfully retrieved auto-attendance settings."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading auto-attendance settings: ({ex})"

    return form

def write_auto_attendance_settings(connection_id : int, form : AutoAttendanceSettingsForm, model : AutoAttendanceSettingsModel) -> AutoAttendanceSettingsForm:
    time_sections : List[attendance_setting.AutoAttendance] = list()
    for i in range(0, device_limits.NUM_TR_TIMESECTIONS):
        section = attendance_setting.AutoAttendance()

        section.start_time = parse_hh_mm(form.cleaned_data[f"start_{i+1}"])
        if section.start_time is None:
            model.error_msg = f"Malformed input for start time of section {i+1}. Please enter time in hh:mm format."
            return form

        section.end_time = parse_hh_mm(form.cleaned_data[f"end_{i+1}"])
        if section.end_time is None:
            model.error_msg = f"Malformed input for end time of section {i+1}. Please enter time in hh:mm format."
            return form

        try:
            section.status = attendance_setting.AttendStatus[form.cleaned_data[f"status_{i+1}"]]
        except ValueError:
            model.error_msg = f"Please select status for time section {i+1}."
            return form

        time_sections.append(section)

    try:
        with connection.open() as client:
            resp = attendance_setting.SetAutoAttendanceSettingsRequest(time_sections = time_sections).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied auto-attendance settings."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying auto-attendance settings: ({ex})"

    return form
