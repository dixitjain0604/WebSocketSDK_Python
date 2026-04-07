from typing import Optional

from devicebroker.device_cmd.m50 import device_control
from . import connection
from ..forms import SetTrIconForm

class SetTrIconModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def set_tr_icon(connection_id : int, form : SetTrIconForm, model : SetTrIconModel) -> SetTrIconForm:
    if (icon_no := form.cleaned_data["icon_no"]) is None:
        model.error_msg = "Please enter icon no."
        return form

    if (icon_status := form.cleaned_data["icon_status"]) is None:
        model.error_msg = "Please enter icon Status."
        return form

    icon_data = form.cleaned_data["icon_data"]
    
    need_delete = bool(int(form.cleaned_data["delete"])) if form.cleaned_data["delete"] else False

    if not need_delete:
        if icon_data is None:
            model.error_msg = "Please specify a png file."
            return form

    try:
        with connection.open() as client:
            resp = device_control.SetTrIconRequest(icon_no, icon_status, need_delete, icon_data).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully set tr icon."
        else:
            model.error_msg = f"Device reported error ({resp.result}, reason: {resp.fail_reason})"

    except Exception as ex:
        model.error_msg = f"Error occurred while setting tr icon: ({ex})"

    return form
