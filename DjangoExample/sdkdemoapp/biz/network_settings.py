from typing import Optional

from devicebroker.device_cmd.m50 import network_setting
from . import connection
from ..forms import EthernetSettingForm, WifiSettingForm

class NetworkSettingModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_ethernet_setting(connection_id : int, form : EthernetSettingForm, model : NetworkSettingModel) -> EthernetSettingForm:
    try:
        with connection.open() as client:
            resp : network_setting.GetEthernetSettingResponse = network_setting.GetEthernetSettingRequest().transact(client, connection_id)

        if resp.has_succeeded():
            data = {
                "use_dhcp"              : str(int(resp.use_dhcp)),
                "ip_address"            : resp.ip_address,
                "subnet_mask"           : resp.subnet_mask,
                "gateway"               : resp.gateway,
                "port"                  : resp.port,
                "mac_address"           : resp.mac_address,
                "ip_address_from_dhcp"  : resp.ip_address_from_dhcp,
                "subnet_mask_from_dhcp" : resp.subnet_mask_from_dhcp,
                "gateway_from_dhcp"     : resp.gateway_from_dhcp,
            }
            form = EthernetSettingForm(data)

            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading setting: ({ex})"

    return form

def write_ethernet_setting(connection_id : int, form : EthernetSettingForm, model : NetworkSettingModel) -> EthernetSettingForm:
    if not (use_dhcp := form.cleaned_data["use_dhcp"]):
        model.error_msg = "Please choose whether to use DHCP or not."
        return form
    if (port := form.cleaned_data["port"]) is None:
        model.error_msg = "Please enter port number."
        return form

    try:
        with connection.open() as client:
            resp = network_setting.SetEthernetSettingRequest(
                use_dhcp    = use_dhcp,
                ip_address  = form.cleaned_data["ip_address"],
                subnet_mask = form.cleaned_data["subnet_mask"],
                gateway     = form.cleaned_data["gateway"],
                port        = port
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return form

def read_wifi_setting(connection_id : int, form : WifiSettingForm, model : NetworkSettingModel) -> WifiSettingForm:
    try:
        with connection.open() as client:
            resp : network_setting.GetWifiSettingResponse = network_setting.GetWifiSettingRequest().transact(client, connection_id)

        if resp.has_succeeded():
            data = {
                "use_wifi"              : str(int(resp.use_wifi)),
                "ssid"                  : resp.ssid,
                "key"                   : resp.key,
                "use_dhcp"              : str(int(resp.use_dhcp)),
                "ip_address"            : resp.ip_address,
                "subnet_mask"           : resp.subnet_mask,
                "gateway"               : resp.gateway,
                "port"                  : resp.port,
                "ip_address_from_dhcp"  : resp.ip_address_from_dhcp,
                "subnet_mask_from_dhcp" : resp.subnet_mask_from_dhcp,
                "gateway_from_dhcp"     : resp.gateway_from_dhcp,
            }
            form = WifiSettingForm(data)

            model.info_msg = "Successfully retrieved setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading setting: ({ex})"

    return form

def write_wifi_setting(connection_id : int, form : WifiSettingForm, model : NetworkSettingModel) -> WifiSettingForm:
    if not (use_wifi := form.cleaned_data["use_wifi"]):
        model.error_msg = "Please choose whether to use Wi-Fi or not."
        return form

    if not (use_dhcp := form.cleaned_data["use_dhcp"]):
        model.error_msg = "Please choose whether to use DHCP or not."
        return form
    if (port := form.cleaned_data["port"]) is None:
        model.error_msg = "Please enter port number."
        return form

    try:
        with connection.open() as client:
            resp = network_setting.SetWifiSettingRequest(
                use_wifi    = use_wifi,
                ssid        = form.cleaned_data["ssid"],
                key         = form.cleaned_data["key"],
                use_dhcp    = use_dhcp,
                ip_address  = form.cleaned_data["ip_address"],
                subnet_mask = form.cleaned_data["subnet_mask"],
                gateway     = form.cleaned_data["gateway"],
                port        = port
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied setting."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying setting: ({ex})"

    return form
