from typing import Optional, Tuple

from devicebroker.device_cmd import messages
from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import FaceDataManagementForm

class FaceDataManagementModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_face_data(connection_id : int, form : FaceDataManagementModel) -> Tuple[FaceDataManagementModel, FaceDataManagementForm]:
    model = FaceDataManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is not None:
            with connection.open() as client:
                resp : user_data.GetFaceDataResponse = user_data.GetFaceDataRequest(user_id).transact(client, connection_id)

            if resp.has_succeeded():
                form = FaceDataManagementForm({
                    "user_id"  : user_id,
                    "face_data": resp.face
                })
                model.info_msg = "Successfully retrieved face data." if resp.face else "Face is not enrolled for this ID."
            else:
                model.error_msg = f"Device reported error: {resp.result}"
        else:
            model.error_msg = "Please enter a user ID."

    except Exception as ex:
        model.error_msg = f"An error occurred while getting face data ({ex})"

    return model, form

def write_face_data(connection_id : int, form : FaceDataManagementForm) -> Tuple[FaceDataManagementModel, FaceDataManagementForm]:
    model = FaceDataManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        if not (face_data := form.cleaned_data["face_data"]):
            model.error_msg = "Please specify face data."
            return model, form

        check_dup = form.cleaned_data["check_duplication"]

        with connection.open() as client:
            resp : messages.GenericResponse = user_data.SetFaceDataRequest(
                user_id,
                face_data,
                check_duplication = bool(int(check_dup)) if check_dup else False
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully set face data."
        else:
            model.error_msg = f"Device reported error: {resp.result}, reason: {resp.fail_reason}"

    except Exception as ex:
        model.error_msg = f"An error occurred while setting face data ({ex})"

    return model, form

def delete_face_data(connection_id : int, form : FaceDataManagementForm) -> Tuple[FaceDataManagementModel, FaceDataManagementForm]:
    model = FaceDataManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        with connection.open() as client:
            resp : messages.GenericResponse = user_data.SetFaceDataRequest(
                user_id,
                None
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully deleted face data."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while setting face data ({ex})"

    return model, form
