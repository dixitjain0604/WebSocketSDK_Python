from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import UserMiscCredForm

class UserMiscCredModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

    password    : Optional[str] = None
    card        : Optional[int] = None
    qr          : Optional[int] = None

def read_user_password(connection_id : int, form : UserMiscCredForm) -> Tuple[UserMiscCredModel, UserMiscCredForm]:
    model = UserMiscCredModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserPasswordResponse = user_data.GetUserPasswordRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            model.password = resp.password
            model.info_msg = "Successfully retrieved user password." if resp.password else "Password is not enrolled for this ID."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while getting user password ({ex})"

    return model, form

def read_user_card(connection_id : int, form : UserMiscCredForm) -> Tuple[UserMiscCredModel, UserMiscCredForm]:
    model = UserMiscCredModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserCardResponse = user_data.GetUserCardRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            model.card = resp.card
            model.info_msg = "Successfully retrieved card." if resp.card is not None else "Card is not enrolled for this ID."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while getting card ({ex})"

    return model, form

def read_user_qr(connection_id : int, form : UserMiscCredForm) -> Tuple[UserMiscCredModel, UserMiscCredForm]:
    model = UserMiscCredModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserQRResponse = user_data.GetUserQRRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            model.qr = resp.qr
            model.info_msg = "Successfully retrieved QR." if resp.card is not None else "QR is not enrolled for this ID."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while getting QR ({ex})"

    return model, form
