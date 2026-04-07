from typing import Optional

from ..forms import UploadFirmwareForm
from ..models import FirmwareBinary

class UploadFirmwareBinaryModel:
    error_msg   : Optional[str] = None
    info_msg    : Optional[str] = None

def upload_firmware(form : UploadFirmwareForm, model : UploadFirmwareBinaryModel) -> bool:
    if not (name := form.cleaned_data["firmware_name"]):
        model.error_msg = "Please specify a firmware name."
        return False

    if not (data := form.cleaned_data["firmware_data"]):
        model.error_msg = "Please specify firmware data."
        return False

    try:
        o = FirmwareBinary()
        o.name = name
        o.data = data
        o.save()
    except Exception as ex:
        model.error_msg = f"Error while saving data: {ex}"
        return False

    return True
