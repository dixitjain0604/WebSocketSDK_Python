from typing import Optional

from devicebroker.device_cmd.m50 import clear_data as C
from . import connection
from ..forms import ClearDataForm

class ClearDataModel:
    info_msg    : Optional[str] = None
    error_msg   : Optional[str] = None

def clear_user_data(connection_id : int, form : ClearDataForm, model : ClearDataModel) -> ClearDataForm:
    try:
        with connection.open() as client:
            resp = C.ClearUserDataRequest().transact(client, connection_id)
        if resp.has_succeeded():
            model.info_msg = "Successfully cleared user data."
        else:
            model.error_msg = f"Device reported error: {resp.result}"
    except Exception as ex:
        model.error_msg = f"An error occurred while clearing user data ({ex})"
    return form

def take_off_managers(connection_id : int, form : ClearDataForm, model : ClearDataModel) -> ClearDataForm:
    try:
        with connection.open() as client:
            resp = C.TakeOffManagerRequest().transact(client, connection_id)
        if resp.has_succeeded():
            model.info_msg = "Successfully took off all managers."
        else:
            model.error_msg = f"Device reported error: {resp.result}"
    except Exception as ex:
        model.error_msg = f"An error occurred while taking off managers ({ex})"
    return form

def clear_attendance_logs(connection_id : int, form : ClearDataForm, model : ClearDataModel) -> ClearDataForm:
    try:
        with connection.open() as client:
            resp = C.ClearAttendanceLogRequest().transact(client, connection_id)
        if resp.has_succeeded():
            model.info_msg = "Successfully cleared attendance logs."
        else:
            model.error_msg = f"Device reported error: {resp.result}"
    except Exception as ex:
        model.error_msg = f"An error occurred while clearing attendance logs ({ex})"
    return form

def clear_management_logs(connection_id : int, form : ClearDataForm, model : ClearDataModel) -> ClearDataForm:
    try:
        with connection.open() as client:
            resp = C.ClearManagementLogRequest().transact(client, connection_id)
        if resp.has_succeeded():
            model.info_msg = "Successfully cleared management logs."
        else:
            model.error_msg = f"Device reported error: {resp.result}"
    except Exception as ex:
        model.error_msg = f"An error occurred while clearing management logs ({ex})"
    return form

def clear_all(connection_id : int, form : ClearDataForm, model : ClearDataModel) -> ClearDataForm:
    try:
        with connection.open() as client:
            resp = C.ClearAllDataRequest().transact(client, connection_id)
        if resp.has_succeeded():
            model.info_msg = "Successfully cleared device data."
        else:
            model.error_msg = f"Device reported error: {resp.result}"
    except Exception as ex:
        model.error_msg = f"An error occurred while clearing device data ({ex})"
    return form
