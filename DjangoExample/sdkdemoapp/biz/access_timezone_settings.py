from typing import List, Optional

from devicebroker.device_cmd.m50 import access_control, device_limits
from . import connection
from ..forms import AccessTimezoneSettingsForm
from .utils import format_hh_mm, parse_hh_mm

class AccessTimezoneSettingsModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_access_timezone_settings(connection_id : int, form : AccessTimezoneSettingsForm, model : AccessTimezoneSettingsModel) -> AccessTimezoneSettingsForm:
    if (timezone_no := form.cleaned_data["timezone_no"]) is None:
        model.error_msg = "Please enter timezone number."
        return form

    try:
        with connection.open() as client:
            resp : access_control.GetAccessTimezoneResponse = access_control.GetAccessTimezoneRequest(timezone_no).transact(client, connection_id)

        if resp.has_succeeded():
            data = { "timezone_no": timezone_no }
            for i, section in enumerate(resp.time_sections):
                data[f"start_{i+1}"]    = format_hh_mm(section.start_time)
                data[f"end_{i+1}"]      = format_hh_mm(section.end_time)
            form = AccessTimezoneSettingsForm(data)

            model.info_msg = "Successfully retrieved access timezone settings."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading access timezone settings: ({ex})"

    return form

def write_access_timezone_settings(connection_id : int, form : AccessTimezoneSettingsForm, model : AccessTimezoneSettingsModel) -> AccessTimezoneSettingsForm:
    if (timezone_no := form.cleaned_data["timezone_no"]) is None:
        model.error_msg = "Please enter timezone number."
        return form

    time_sections : List[access_control.AccessTimeSection] = list()
    for i, row in enumerate(form.rows()):
        section = access_control.AccessTimeSection()

        section.start_time = parse_hh_mm(form.cleaned_data[f"start_{i+1}"])
        if section.start_time is None:
            model.error_msg = f"Malformed input for start time of {row.weekday}. Please enter time in hh:mm format."
            return form

        section.end_time = parse_hh_mm(form.cleaned_data[f"end_{i+1}"])
        if section.end_time is None:
            model.error_msg = f"Malformed input for end time of {row.weekday}. Please enter time in hh:mm format."
            return form

        time_sections.append(section)

    try:
        with connection.open() as client:
            resp = access_control.SetAccessTimezoneRequest(timezone_no = timezone_no, time_sections = time_sections).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied access timezone settings."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying access timezone settings: ({ex})"

    return form
