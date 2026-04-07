from typing import Optional

from devicebroker.device_cmd.m50 import access_control
from . import connection
from ..forms import LockControlForm

class LockControlModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_lock_control_mode(connection_id : int, form : LockControlForm, model : LockControlModel) -> LockControlForm:
    try:
        with connection.open() as client:
            resp : access_control.GetLockControlModeResponse = access_control.GetLockControlModeRequest().transact(client, connection_id)

        if resp.has_succeeded():
            data = { "mode": resp.mode.name }
            form = LockControlForm(data)

            model.info_msg = "Successfully retrieved lock control mode."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading lock control mode: ({ex})"

    return form

def write_lock_control_mode(connection_id : int, form : LockControlForm, model : LockControlModel) -> LockControlForm:
    try:
        mode = access_control.LockControlMode[form.cleaned_data["mode"]]
    except ValueError:
        model.error_msg = "Please select a lock control mode."
        return form

    try:
        with connection.open() as client:
            resp = access_control.SetLockControlModeRequest(mode).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied lock control mode."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying lock control mode: ({ex})"

    return form
