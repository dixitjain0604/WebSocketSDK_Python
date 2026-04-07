from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import UserAttendOnlyManagementForm

class UserAttendOnlyManagementModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_user_attend_only(connection_id : int, form : UserAttendOnlyManagementForm) -> Tuple[UserAttendOnlyManagementModel, UserAttendOnlyManagementForm]:
    model = UserAttendOnlyManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserAttendOnlySettingResponse = user_data.GetUserAttendOnlySettingRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            form = UserAttendOnlyManagementForm({
                "user_id"       : user_id,
                "attend_only"   : int(resp.value)
            })
            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while reading setting ({ex})"

    return model, form

def write_user_attend_only(connection_id : int, form : UserAttendOnlyManagementForm) -> Tuple[UserAttendOnlyManagementModel, UserAttendOnlyManagementForm]:
    model = UserAttendOnlyManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        if not (value := form.cleaned_data["attend_only"]):
            model.error_msg = "Please choose setting value."
            return model, form

        with connection.open() as client:
            resp = user_data.SetUserAttendOnlySettingRequest(user_id, bool(int(value))).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully modified setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while modifying setting ({ex})"

    return model, form
