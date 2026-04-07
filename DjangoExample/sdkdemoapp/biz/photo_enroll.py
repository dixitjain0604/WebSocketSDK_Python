from typing import Optional

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import EnrollFaceByPhotoForm

class EnrollFaceByPhotoModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def enroll_face_by_photo(connection_id : int, form : EnrollFaceByPhotoForm, model : EnrollFaceByPhotoModel) -> EnrollFaceByPhotoForm:
    if (user_id := form.cleaned_data["user_id"]) is None:
        model.error_msg = "Please enter user ID."
        return form

    if (photo := form.cleaned_data["photo"]) is None:
        model.error_msg = "Please specify a photo."
        return form

    try:
        with connection.open() as client:
            resp = user_data.EnrollFaceByPhotoRequest(user_id, photo).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully enrolled face by photo."
        else:
            model.error_msg = f"Device reported error ({resp.result}, reason: {resp.fail_reason})"

    except Exception as ex:
        model.error_msg = f"Error occurred while enrolling face by photo: ({ex})"

    return form
