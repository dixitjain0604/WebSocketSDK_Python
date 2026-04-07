from typing import Optional

from devicebroker.device_cmd.m50 import device_info
from . import connection
from ..forms import WebServerUrlSettingForm


class WebServerUrlSettingModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_setting(connection_id : int, form : WebServerUrlSettingForm, model : WebServerUrlSettingModel) -> WebServerUrlSettingForm:
    try:
        with connection.open() as client:
            resp : device_info.GetDeviceInfoExtResponse = device_info.GetDeviceInfoExtRequest(
                device_info.DeviceInfoExtParamType.WebServerUrl
            ).transact(client, connection_id)

        if resp.has_succeeded():
            data = { "web_server_url": resp.value1 }
            form = WebServerUrlSettingForm(data)

            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading setting: ({ex})"

    return form

def write_setting(connection_id : int, form : WebServerUrlSettingForm, model : WebServerUrlSettingModel) -> WebServerUrlSettingForm:
    server_url = form.cleaned_data["web_server_url"]

    try:
        with connection.open() as client:
            resp : device_info.SetDeviceInfoExtResponse = device_info.SetDeviceInfoExtRequest(
                device_info.DeviceInfoExtParamType.WebServerUrl,
                server_url
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return form
