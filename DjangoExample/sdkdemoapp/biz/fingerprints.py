from importlib.resources import is_resource
from typing import Optional, Tuple

from devicebroker.device_cmd.m50 import user_data
from . import connection
from ..forms import FingerprintManagementForm


class FingerprintManagementModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_fingerprint_data(connection_id : int, form : FingerprintManagementModel) -> Tuple[FingerprintManagementModel, FingerprintManagementForm]:
    model = FingerprintManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        if (finger_no := form.cleaned_data["finger_no"]) is None:
            model.error_msg = "Please select a finger number."
            return model, form

        with connection.open() as client:
            resp : user_data.GetFingerprintDataResponse = user_data.GetFingerprintDataRequest(user_id, finger_no).transact(client, connection_id)

        if resp.has_succeeded():
            form = FingerprintManagementForm({
                "user_id"           : resp.user_id,
                "finger_no"         : resp.finger_no,
                "fingerprint_data"  : resp.fingerprint_data,
                "duress"            : int(resp.is_duress)
            })
            model.info_msg = "Successfully retrieved fingerprint data." if resp.fingerprint_data else "Fingerprint is not enrolled for this ID."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while getting fingerprint data ({ex})"

    return model, form

def write_fingerprint_data(connection_id : int, form : FingerprintManagementForm) -> Tuple[FingerprintManagementModel, FingerprintManagementForm]:
    model = FingerprintManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        if (finger_no := form.cleaned_data["finger_no"]) is None:
            model.error_msg = "Please select a finger number."
            return model, form

        if not (fp_data := form.cleaned_data["fingerprint_data"]):
            model.error_msg = "Please specify fingerprint data."
            return model, form

        check_dup = form.cleaned_data["check_duplication"]
        is_duress = form.cleaned_data["duress"]

        with connection.open() as client:
            resp = user_data.SetFingerprintDataRequest(
                user_id, finger_no, fp_data,
                is_duress = bool(int(is_duress)) if is_duress else False,
                check_duplication = bool(int(check_dup)) if check_dup else False
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully set fingerprint data."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while setting fingerprint data ({ex})"

    return model, form

def delete_fingerprint_data(connection_id : int, form : FingerprintManagementForm) -> Tuple[FingerprintManagementModel, FingerprintManagementForm]:
    model = FingerprintManagementModel()

    try:
        if (user_id := form.cleaned_data["user_id"]) is None:
            model.error_msg = "Please enter a user ID."
            return model, form

        if (finger_no := form.cleaned_data["finger_no"]) is None:
            model.error_msg = "Please select a finger number."
            return model, form

        with connection.open() as client:
            resp = user_data.SetFingerprintDataRequest(
                user_id, finger_no, None
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully deleted fingerprint."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while deleting fingerprint ({ex})"

    return model, form
