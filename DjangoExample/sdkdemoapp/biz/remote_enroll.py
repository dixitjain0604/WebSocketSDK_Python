from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import RemoteEnrollForm

class RemoteEnrollModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def start_remote_enroll(connection_id : int, form : RemoteEnrollForm, model : RemoteEnrollModel) -> RemoteEnrollForm:
    if (user_id := form.cleaned_data["user_id"]) is None:
        model.error_msg = "Please enter user ID."
        return form

    try:
        enroll_type = user_data.RemoteEnrollType[form.cleaned_data["enroll_type"]]
    except:
        model.error_msg = "Please select enroll type."
        return form

    finger_no = None
    if enroll_type == user_data.RemoteEnrollType.FP:
        finger_no = form.cleaned_data["finger_no"]
        if not finger_no:
            model.error_msg = "Please select finger number."
            return form

        finger_no = int(finger_no)

    try:
        with connection.open() as client:
            resp : user_data.BeginRemoteEnrollResponse = user_data.BeginRemoteEnrollRequest(user_id, enroll_type, finger_no).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully started remote enroll."
        else:
            model.error_msg = f"Device reported error (reason: {resp.result_code.name})"

    except Exception as ex:
        model.error_msg = f"Error occurred while starting remote enroll: ({ex})"

    return form

def stop_remote_enroll(connection_id : int, form : RemoteEnrollForm, model : RemoteEnrollModel) -> RemoteEnrollForm:
    try:
        with connection.open() as client:
            resp : user_data.ExitRemoteEnrollResponse = user_data.ExitRemoteEnrollRequest().transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully stopped remote enroll."
        else:
            model.error_msg = f"Device reported error (reason: {resp.result_code.name})"

    except Exception as ex:
        model.error_msg = f"Error occurred while stopping remote enroll: ({ex})"

    return form

def query_status(connection_id : int, form : RemoteEnrollForm, model : RemoteEnrollModel) -> RemoteEnrollForm:
    try:
        with connection.open() as client:
            resp : user_data.QueryRemoteEnrollStatusResponse = user_data.QueryRemoteEnrollStatusRequest().transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = f"Remote enroll status: {resp.result_code.name}"
        else:
            model.error_msg = f"Device reported error (reason: {resp.result_code.name})"

    except Exception as ex:
        model.error_msg = f"Error occurred while querying remote enroll: ({ex})"

    return form
