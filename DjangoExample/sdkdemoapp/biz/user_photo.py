from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import UserPhotoManagementForm

class UserPhotoManagementModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_user_photo(connection_id : int, form : UserPhotoManagementForm) -> Tuple[UserPhotoManagementModel, UserPhotoManagementForm]:
    model = UserPhotoManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : user_data.GetUserPhotoResponse = user_data.GetUserPhotoRequest(user_id).transact(client, connection_id)

        if resp.has_succeeded():
            form = UserPhotoManagementForm({
                "user_id"   : user_id,
                "photo"     : resp.photo
            })
            model.info_msg = "Successfully retrieved user photo." if resp.photo else "User photo is not available for this ID."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while getting user photo ({ex})"

    return model, form

def write_user_photo(connection_id : int, form : UserPhotoManagementForm) -> Tuple[UserPhotoManagementModel, UserPhotoManagementForm]:
    model = UserPhotoManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        if (photo := form.cleaned_data["photo"]) is None:
            model.error_msg = "Please provide a photo."
            return model, form

        with connection.open() as client:
            resp = user_data.SetUserPhotoRequest(user_id, photo).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully set user photo."
        else:
            model.error_msg = f"Device reported error: {resp.result}, reason: {resp.fail_reason}"

    except Exception as ex:
        model.error_msg = f"An error occurred while setting user photo ({ex})"

    return model, form

def delete_user_photo(connection_id : int, form : UserPhotoManagementForm) -> Tuple[UserPhotoManagementModel, UserPhotoManagementForm]:
    model = UserPhotoManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp = user_data.SetUserPhotoRequest(user_id, None).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully deleted user photo."
        else:
            model.error_msg = f"Device reported error: {resp.result}, reason: {resp.fail_reason}"

    except Exception as ex:
        model.error_msg = f"An error occurred while deleting user photo ({ex})"

    return model, form
