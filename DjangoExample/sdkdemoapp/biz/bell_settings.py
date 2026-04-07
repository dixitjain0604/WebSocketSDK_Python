from typing import List, Optional

from devicebroker.device_cmd.m50 import attendance_setting, device_limits
from . import connection
from ..forms import BellSettingsForm


class BellSettingsModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_bell_settings(connection_id : int, form : BellSettingsForm, model : BellSettingsModel) -> BellSettingsForm:
    try:
        with connection.open() as client:
            resp : attendance_setting.GetBellSettingsResponse = attendance_setting.GetBellSettingsRequest().transact(client, connection_id)

        if resp.has_succeeded():
            data = {"ring_times" : resp.ring_times}
            for i, bell in enumerate(resp.bells):
                data[f"valid_{i+1}"]  = str(int(bell.valid))
                data[f"type_{i+1}"]   = str(bell.bell_type)
                data[f"hour_{i+1}"]   = bell.hour
                data[f"minute_{i+1}"] = bell.minute
            form = BellSettingsForm(data)

            model.info_msg = "Successfully retrieved bell settings."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading bell settings: ({ex})"

    return form

def write_bell_settings(connection_id : int, form : BellSettingsForm, model : BellSettingsModel) -> BellSettingsForm:
    if (ring_times := form.cleaned_data["ring_times"]) is None:
        model.error_msg = "Please enter ring times."
        return form

    bells : List[attendance_setting.Bell] = list()
    for i in range(0, device_limits.NUM_BELLS):
        bell = attendance_setting.Bell()
        bell.valid      = bool(int(form.cleaned_data[f"valid_{i+1}"]))
        bell.bell_type  = int(form.cleaned_data[f"type_{i+1}"])
        if bell.valid:
            try:
                bell.hour   = int(form.cleaned_data[f"hour_{i+1}"])
                bell.minute = int(form.cleaned_data[f"minute_{i+1}"])
            except ValueError:
                model.error_msg = f"Please enter time and hour for Bell {i+1}"
                return form
        bells.append(bell)

    try:
        with connection.open() as client:
            resp = attendance_setting.SetBellSettingsRequest(
                ring_times = ring_times,
                bells = bells
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied bell settings."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying bell settings: ({ex})"

    return form
