from typing import Optional

from devicebroker.device_cmd.m50 import attendance_setting
from . import connection
from ..forms import DepartmentSettingsForm, ProxyDepartmentSettingsForm


class DepartmentSettingsModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def read_department_setting(connection_id : int, form : DepartmentSettingsForm, model : DepartmentSettingsModel) -> DepartmentSettingsForm:
    if (depart_no := form.cleaned_data["depart_no"]) is None:
        model.error_msg = "Please enter department number."
        return form

    try:
        with connection.open() as client:
            resp : attendance_setting.GetDepartmentResponse = attendance_setting.GetDepartmentRequest(depart_no).transact(client, connection_id)

        if resp.has_succeeded():
            data = {
                "depart_no"     : depart_no,
                "depart_name"   : resp.name
            }
            form = DepartmentSettingsForm(data)

            model.info_msg = "Successfully retrieved department."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading department: ({ex})"

    return form

def write_department_setting(connection_id : int, form : DepartmentSettingsForm, model : DepartmentSettingsModel) -> DepartmentSettingsForm:
    if (depart_no := form.cleaned_data["depart_no"]) is None:
        model.error_msg = "Please enter department number."
        return form

    try:
        with connection.open() as client:
            resp = attendance_setting.SetDepartmentRequest(
                depart_no = depart_no,
                name = form.cleaned_data["depart_name"]
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied department."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying department: ({ex})"

    return form

def read_proxy_department_setting(connection_id : int, form : ProxyDepartmentSettingsForm, model : DepartmentSettingsModel) -> ProxyDepartmentSettingsForm:
    if (depart_no := form.cleaned_data["depart_no"]) is None:
        model.error_msg = "Please enter department number."
        return form

    try:
        with connection.open() as client:
            resp : attendance_setting.GetProxyDepartmentResponse = attendance_setting.GetProxyDepartmentRequest(depart_no).transact(client, connection_id)

        if resp.has_succeeded():
            data = {
                "depart_no"     : depart_no,
                "depart_name"   : resp.name
            }
            form = ProxyDepartmentSettingsForm(data)

            model.info_msg = "Successfully retrieved department."
        else:
            model.error_msg = f"Device reported error ({resp.result})"

    except Exception as ex:
        model.error_msg = f"Error occurred while reading department: ({ex})"

    return form

def write_proxy_department_setting(connection_id : int, form : ProxyDepartmentSettingsForm, model : DepartmentSettingsModel) -> ProxyDepartmentSettingsForm:
    if (depart_no := form.cleaned_data["depart_no"]) is None:
        model.error_msg = "Please enter department number."
        return form

    try:
        with connection.open() as client:
            resp = attendance_setting.SetProxyDepartmentRequest(
                depart_no = depart_no,
                name = form.cleaned_data["depart_name"]
            ).transact(client, connection_id)

        if resp.has_succeeded():
            model.info_msg = "Successfully applied department."
        else:
            model.error_msg = f"Device reported error ({resp.result})"
        
    except Exception as ex:
        model.error_msg = f"Error occurred while applying department: ({ex})"

    return form
