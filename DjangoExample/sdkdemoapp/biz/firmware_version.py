from typing import Optional
from devicebroker.device_cmd.m50 import maintenance
from . import connection

class FirmwareVersionModel:
    error_msg       : Optional[str] = None
    info_msg        : Optional[str] = None
    fw_version      : Optional[str] = None
    fw_build_number : Optional[str] = None

def get_firmware_version(connection_id : int, model : FirmwareVersionModel):
    try:
        with connection.open() as client:
            resp : maintenance.GetFirmwareVersionResponse = maintenance.GetFirmwareVersionRequest().transact(client, connection_id)

        model.fw_version        = resp.version
        model.fw_build_number   = resp.build_number
        model.info_msg = "Successfully retrieved device firmware version."
    except Exception as ex:
        model.error_msg = f"An error occurred while retrieving version info ({ex})"
