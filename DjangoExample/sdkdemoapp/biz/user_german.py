from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import UserManagementGermanForm

class UserManagementGermanModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def get_user_message(connection_id : int, form : UserManagementGermanForm) -> Tuple[UserManagementGermanModel, UserManagementGermanForm]:
    model = UserManagementGermanModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserMessageResponse = user_data.GetUserMessageRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            form = UserManagementGermanForm({
                "user_id"       : user_id,
                "message"       : resp.message
            })
            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while reading setting ({ex})"

    return model, form

def set_user_message(connection_id : int, form : UserManagementGermanForm) -> Tuple[UserManagementGermanModel, UserManagementGermanForm]:
    model = UserManagementGermanModel()

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

def get_balance_time(connection_id : int, form : UserManagementGermanForm) -> Tuple[UserManagementGermanModel, UserManagementGermanForm]:
    model = UserManagementGermanModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserBalanceTimeResponse = user_data.GetUserBalanceTimeRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            form = UserManagementGermanForm({
                "user_id"       : user_id,
                "balance_hour"  : int(resp.balance_time_in_minutes / 60),
                "balance_minute"  : resp.balance_time_in_minutes % 60,
            })
            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while reading setting ({ex})"

    return model, form

def set_balance_time(connection_id : int, form : UserManagementGermanForm) -> Tuple[UserManagementGermanModel, UserManagementGermanForm]:
    model = UserManagementGermanModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        balance_hour = int(form.cleaned_data["balance_hour"] or 0)
        balance_minute = int(form.cleaned_data["balance_minute"] or 0)

        balance_time= balance_hour * 60 + balance_minute
        if balance_time > 65535:
            model.info_msg = "Balance time should be in range 00:00~1092:15."
            return model, form

        with connection.open() as client:
            resp = user_data.SetUserBalanceTimeRequest(user_id, balance_hour * 60 + balance_minute).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully modified setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while modifying setting ({ex})"

    return model, form


def get_holidays(connection_id : int, form : UserManagementGermanForm) -> Tuple[UserManagementGermanModel, UserManagementGermanForm]:
    model = UserManagementGermanModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserHolidaysResponse = user_data.GetUserHolidaysRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            form = UserManagementGermanForm({
                "user_id"       : user_id,
                "holidays"      : resp.holidays_in_10 / 10
            })
            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while reading setting ({ex})"

    return model, form

def set_holidays(connection_id : int, form : UserManagementGermanForm) -> Tuple[UserManagementGermanModel, UserManagementGermanForm]:
    model = UserManagementGermanModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        holidays_in_10 = int(float(form.cleaned_data["holidays"] or 0) * 10)
        if holidays_in_10 < 0 or holidays_in_10 > 65535 :
            model.info_msg = "Holidays should be in range 0.0~6553.5."
            return model, form

        with connection.open() as client:
            resp = user_data.SetUserHolidaysRequest(user_id, holidays_in_10).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully modified setting."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while modifying setting ({ex})"

    return model, form
