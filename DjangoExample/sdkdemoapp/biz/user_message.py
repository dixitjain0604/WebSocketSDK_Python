from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import UserMessageManagementForm

class UserMessageManagementModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def get_user_message(connection_id : int, form : UserMessageManagementForm) -> Tuple[UserMessageManagementModel, UserMessageManagementForm]:
    model = UserMessageManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserMessageResponse = user_data.GetUserMessageRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            form = UserMessageManagementForm({
                "user_id"       : user_id,
                "message"       : resp.message
            })
            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while reading setting ({ex})"

    return model, form

def set_user_message(connection_id : int, form : UserMessageManagementForm) -> Tuple[UserMessageManagementModel, UserMessageManagementForm]:
    model = UserMessageManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        message = form.cleaned_data["message"] or ""

        with connection.open() as client:
            resp = user_data.SetUserMessageRequest(user_id, message).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully modified setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while modifying setting ({ex})"

    return model, form

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

def get_message_color(connection_id : int, form : UserMessageManagementForm) -> Tuple[UserMessageManagementModel, UserMessageManagementForm]:
    model = UserMessageManagementModel()

    try:
        with connection.open() as client:
            resp : user_data.GetUserMessageColorResponse = user_data.GetUserMessageColorRequest().transact(client, connection_id)

        if resp.has_succeeded():
            form = UserMessageManagementForm({
                "color"             : f"{resp.color:06X}",
                "bk_color"          : f"{resp.bk_color:06X}",
            })
            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while reading setting ({ex})"

    return model, form

def set_message_color(connection_id : int, form : UserMessageManagementForm) -> Tuple[UserMessageManagementModel, UserMessageManagementForm]:
    model = UserMessageManagementModel()

    color = parse_color(form.cleaned_data["color"])
    if color is None:
        model.error_msg = "Please input a valid color value."
        return model, form

    bk_color = parse_color(form.cleaned_data["bk_color"])
    if bk_color is None:
        model.error_msg = "Please input a valid back color value."
        return model, form

    try:
        with connection.open() as client:
            resp = user_data.SetUserMessageColorRequest(color, bk_color).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return model, form
