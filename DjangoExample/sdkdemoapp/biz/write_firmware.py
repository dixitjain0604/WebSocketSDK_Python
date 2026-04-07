from typing import Optional

from devicebroker.device_cmd.m50 import maintenance
from . import connection
from ..forms import WriteFirmwareForm
from ..models import FirmwareBinary

class WriteFirmwareModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def write_firmware(connection_id : int, form : WriteFirmwareForm, model : WriteFirmwareModel):
    if not (fw_name := form.cleaned_data["firmware_name"]):
        model.error_msg = "Please select a firmware."
        return

    if not (url := form.cleaned_data["public_url"]):
        model.error_msg = "Please enter public server URL."
        return

    if not url.endswith('/'):
        url += "/"

    url += f"get_firmware/{fw_name}"

    try:
        with connection.open() as client:
            resp = maintenance.WriteFirmwareRequest(url).transact(client, connection_id)
        if resp.has_succeeded():
            model.info_msg = "Successfully sent firmware write command."
        else:
            model.error_msg = f"Device reported error: {resp.result}"
    except Exception as ex:
        model.error_msg = f"An error occurred while sending command ({ex})"
