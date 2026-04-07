from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import UserManagementForm

class UserManagementModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def set_user_data_to_form(user : user_data.UserInfo) -> UserManagementForm:
    data = {
        "user_id"           : user.user_id,
        "name"              : user.name,
        "privilege"         : user.privilege.value,
        "enabled"           : int(user.enabled),
        "department"        : user.department,
        "timeset_1"         : user.timesets[0],
        "timeset_2"         : user.timesets[1],
        "timeset_3"         : user.timesets[2],
        "timeset_4"         : user.timesets[3],
        "timeset_5"         : user.timesets[4],
        "card"              : user.card,
        "qr"                : user.qr,
        "password"          : user.password,
        "face_enrolled"     : int(user.face.enrolled),
        "fingerprint_1"     : int(user.fingerprints[0].enrolled),
        "fingerprint_2"     : int(user.fingerprints[1].enrolled),
        "fingerprint_3"     : int(user.fingerprints[2].enrolled),
        "fingerprint_4"     : int(user.fingerprints[3].enrolled),
        "fingerprint_5"     : int(user.fingerprints[4].enrolled),
        "fingerprint_6"     : int(user.fingerprints[5].enrolled),
        "fingerprint_7"     : int(user.fingerprints[6].enrolled),
        "fingerprint_8"     : int(user.fingerprints[7].enrolled),
        "fingerprint_9"     : int(user.fingerprints[8].enrolled),
        "fingerprint_10"    : int(user.fingerprints[9].enrolled),
    }
    if user.period is not None:
        data["userperiod_start"], data["userperiod_end"] = user.period
    return UserManagementForm(initial = data)

def display_user_data(resp : user_data.GetUserDataResponse, model : UserManagementModel, form : UserManagementForm) -> UserManagementForm:
    if resp.has_succeeded():
        form = set_user_data_to_form(resp.user)
    else:
        model.error_msg = f"Device reported error: {resp.result}"
    return form

def get_user_data_from_form(form : UserManagementForm, model : UserManagementModel, user : user_data.UserInfo) -> bool:
    user.user_id    = form.cleaned_data["user_id"]
    if user.user_id is None:
        model.error_msg = "Please enter user ID."
        return False

    user.name           = form.cleaned_data["name"] or ""
    try:
        user.privilege  = user_data.UserPrivilege(int(form.cleaned_data["privilege"]))
    except ValueError:
        user.privilege  = user_data.UserPrivilege.STANDARD_USER
    user.enabled        = bool(int(form.cleaned_data["enabled"])) or False
    user.department     = form.cleaned_data["department"] or 0
    user.timesets[0]    = form.cleaned_data["timeset_1"] or -1
    user.timesets[1]    = form.cleaned_data["timeset_2"] or -1
    user.timesets[2]    = form.cleaned_data["timeset_3"] or -1
    user.timesets[3]    = form.cleaned_data["timeset_4"] or -1
    user.timesets[4]    = form.cleaned_data["timeset_5"] or -1
    user.card           = form.cleaned_data["card"] or None
    user.qr             = form.cleaned_data["qr"] or None
    user.password       = form.cleaned_data["password"] or None

    period_start        = form.cleaned_data["userperiod_start"]
    period_end          = form.cleaned_data["userperiod_end"]
    if period_start is not None and period_end is not None:
        user.period = (period_start, period_end)
    elif period_start is None and period_end is None:
        user.period = None
    else:
        model.error_msg = "Please enter both start and end period."
        return False

    return True


def get_first_user_data(connection_id : int, form : UserManagementForm) -> Tuple[UserManagementModel, UserManagementForm]:
    model = UserManagementModel()

    try:
        with connection.open() as client:
            resp : user_data.GetNextUserDataResponse = user_data.GetFirstUserDataRequest().transact(client, connection_id)

        form = display_user_data(resp, model, form)
        if resp.has_succeeded():
            if resp.has_more:
                model.info_msg = "Click 'Get Next User' to navigate through users."
            else:
                model.info_msg = "This is the last user."
    except Exception as ex:
        model.error_msg = f"An error occurred while reading user data ({ex})"

    return model, form

def get_next_user_data(connection_id : int, form : UserManagementForm) -> Tuple[UserManagementModel, UserManagementForm]:
    model = UserManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is not None:
            with connection.open() as client:
                resp : user_data.GetNextUserDataResponse = user_data.GetNextUserDataRequest(user_id).transact(client, connection_id)

            form = display_user_data(resp, model, form)
            if resp.has_succeeded():
                if resp.has_more:
                    model.info_msg = "Click 'Get Next User' to navigate through users."
                else:
                    model.info_msg = "This is the last user."
        else:
            model.error_msg = "Please enter a user ID."

    except Exception as ex:
        model.error_msg = f"An error occurred while reading user data ({ex})"

    return model, form

def read_user_data(connection_id : int, form : UserManagementForm) -> Tuple[UserManagementModel, UserManagementForm]:
    model = UserManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is not None:
            with connection.open() as client:
                resp : user_data.GetUserDataResponse = user_data.GetUserDataRequest(user_id).transact(client, connection_id)

            form = display_user_data(resp, model, form)
        else:
            model.error_msg = "Please enter a user ID."

    except Exception as ex:
        model.error_msg = f"An error occurred while reading user data ({ex})"

    return model, form

def write_user_data(connection_id : int, form : UserManagementForm) -> Tuple[UserManagementModel, UserManagementForm]:
    model = UserManagementModel()

    try:
        user = user_data.UserInfo()
        if get_user_data_from_form(form, model, user):
            with connection.open() as client:
                resp : user_data.SetUserDataResponse = user_data.SetUserDataRequest(user).transact(client, connection_id)
            
            if resp.has_succeeded():
                model.info_msg = "Successfully set user data."
            else:
                model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while setting user data ({ex})"

    return model, form

def delete_user(connection_id : int, form : UserManagementForm) -> Tuple[UserManagementModel, UserManagementForm]:
    model = UserManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is not None:
            with connection.open() as client:
                resp : user_data.SetUserDataResponse = user_data.DeleteUserRequest(user_id).transact(client, connection_id)

            if resp.has_succeeded():
                model.info_msg = "Successfully deleted user."
                form = UserManagementForm()
            else:
                model.error_msg = f"Device reported error: {resp.result}"
        else:
            model.error_msg = "Please enter a user ID."

    except Exception as ex:
        model.error_msg = f"An error occurred while deleting user data ({ex})"

    return model, form
