import datetime
import json
from typing import Callable, Dict, List, Optional

from devicebroker.device_cmd.messages import GenericRequest, GenericResponse
from devicebroker.device_cmd.m50 import device_control, device_info
from . import connection
from ..forms import DeviceConfigAndStatusForm

DEVICE_INFO_PARAM_ENUMERATION_MAPPING : Dict[device_info.DeviceInfoParamType, type] = {
    device_info.DeviceInfoParamType.Language        : device_info.DeviceLanguage,
    device_info.DeviceInfoParamType.DoorSensorType  : device_info.DoorSensorType,
    device_info.DeviceInfoParamType.EventSendType   : device_info.EventSendType,
    device_info.DeviceInfoParamType.WiegandFormat   : device_info.WiegandOutputType,
    device_info.DeviceInfoParamType.LockMode        : device_info.LockOperationMode,
    device_info.DeviceInfoParamType.IdentifyMode    : device_info.VerifyMode
}

class DeviceControlsModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None
    result_str  : Optional[str] = None
    device_info_choices : str = json.dumps(dict([
        (param.name, [x.name for x in enum_type])
        for param, enum_type in DEVICE_INFO_PARAM_ENUMERATION_MAPPING.items()
    ]))

def execute_command(
    connection_id   : int,
    model           : DeviceControlsModel,
    request         : GenericRequest,
    display_data    : Optional[Callable[[GenericResponse, DeviceControlsModel], None]] = None):
    try:
        with connection.open() as client:
            resp = request.transact(client, connection_id)

        if resp.has_succeeded():
            if display_data is not None:
                display_data(resp, model)

            model.info_msg = "Command executed successfully."
        else:
            model.error_msg = f"Device reported error: {resp.result}"

    except Exception as ex:
        model.error_msg = f"An error occurred while executing command ({ex})"

def disable_device(connection_id : int, model : DeviceControlsModel):
    execute_command(connection_id, model, device_control.EnableDeviceRequest(False))

def enable_device(connection_id : int, model : DeviceControlsModel):
    execute_command(connection_id, model, device_control.EnableDeviceRequest(True))

def get_device_time(connection_id : int, model : DeviceControlsModel):
    def display_data(resp : device_control.GetTimeResponse, model : DeviceControlsModel):
        model.result_str = str(resp.time)
    execute_command(connection_id, model, device_control.GetTimeRequest(), display_data)

def set_device_time(connection_id : int, model : DeviceControlsModel):
    execute_command(connection_id, model, device_control.SetTimeRequest(datetime.datetime.now()))

def device_status_to_str(value : int, param : device_control.DeviceStatusParamType):
    result = str(value)
    match param:
        case device_control.DeviceStatusParamType.DoorStatus:
            try:
                name = device_control.DoorSensorStatus(value).name
            except ValueError:
                name = "Unknown"
            result += f" ({name})"

        case device_control.DeviceStatusParamType.AlarmStatus:
            alarms : List[str] = [flag.name for flag in device_control.AlarmFlag if (flag.value & value)]
            if len(alarms) == 0:
                alarms.append("None")
            result += f" ({','.join(alarms)})"
    return result

def get_device_status(connection_id : int, model : DeviceControlsModel, form : DeviceConfigAndStatusForm):
    if not (param := form.cleaned_data["device_status_param"]):
        model.error_msg = "Please select a device status param."
        return
    param = device_control.DeviceStatusParamType[param]

    def display_data(resp : device_control.GetDeviceStatusResponse, model : DeviceControlsModel):
        model.result_str = device_status_to_str(resp.param_value, param)

    execute_command(connection_id, model, device_control.GetDeviceStatusRequest(param), display_data)

def get_device_status_all(connection_id : int, model : DeviceControlsModel):
    def display_data(resp : device_control.GetDeviceStatusAllResponse, model : DeviceControlsModel):
        model.result_str = '\n'.join([f"{param.name} : {device_status_to_str(val, param)}" for param, val in resp.device_status.items()])

    execute_command(connection_id, model, device_control.GetDeviceStatusAllRequest(), display_data)

def device_info_to_str(value : int, param : device_info.DeviceInfoParamType):
    result = str(value)

    enum_type = DEVICE_INFO_PARAM_ENUMERATION_MAPPING.get(param, None)
    if enum_type is not None:
        try:
            name = enum_type(value).name
        except ValueError:
            name = "Unknown"

        result += f" ({name})"

    return result

def get_device_info(connection_id : int, model : DeviceControlsModel, form : DeviceConfigAndStatusForm):
    if not (param := form.cleaned_data["device_info_param"]):
        model.error_msg = "Please select a device info param."
        return
    param = device_info.DeviceInfoParamType[param]

    def display_data(resp : device_info.GetDeviceInfoResponse, model : DeviceControlsModel):
        model.result_str = device_info_to_str(resp.param_value, param)

    execute_command(connection_id, model, device_info.GetDeviceInfoRequest(param), display_data)

def set_device_info(connection_id : int, model : DeviceControlsModel, form : DeviceConfigAndStatusForm):
    if not (param := form.cleaned_data["device_info_param"]):
        model.error_msg = "Please select a device info param."
        return
    param = device_info.DeviceInfoParamType[param]

    if (enum_type := DEVICE_INFO_PARAM_ENUMERATION_MAPPING.get(param, None)) is not None:
        if not (value := form.cleaned_data["device_info_value_choice"]):
            model.error_msg = "Please select a valid option."
            return
        value = enum_type[value].value
    else:
        if (value := form.cleaned_data["device_info_value"]) is None:
            model.error_msg = "Please input a value to set."
            return

    execute_command(connection_id, model, device_info.SetDeviceInfoRequest(param, value))

def get_device_info_all(connection_id : int, model : DeviceControlsModel):
    def display_data(resp : device_info.GetDeviceInfoAllResponse, model : DeviceControlsModel):
        model.result_str = '\n'.join([f"{param.name} : {device_info_to_str(val, param)}" for param, val in resp.device_info.items()])

    execute_command(connection_id, model, device_info.GetDeviceInfoAllRequest(), display_data)
