import json
import secrets
from sqlite3 import connect
from typing import Optional
import urllib
from django.shortcuts import render
from django.template import loader
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.urls import is_valid_path, reverse
from django.views.decorators.csrf import csrf_exempt
import requests

from .biz import devices, users, faces, fingerprints, misc_creds, user_photo, user_attend_only, user_message, user_german
from .biz import device_controls, ntp_server_setting, webserverurl_setting, network_settings
from .biz import department_settings, bell_settings, auto_attendance_settings, access_timezone_settings, lock_control, attend_logs
from . import forms
from . import models

@csrf_exempt
def check_device_registration(request : HttpRequest):
    return JsonResponse({
        "token": secrets.token_hex(16)
    })

@csrf_exempt
def check_device_login(request : HttpRequest):
    return JsonResponse({})

@csrf_exempt
def upload_device_log(request : HttpRequest):
    from .biz.log_upload import save_device_log
    contents = json.loads(request.body)
    save_device_log(contents)
    return JsonResponse({})

def index(request : HttpRequest):
    template = loader.get_template('index.html')

    return HttpResponse(template.render(
        {},
        request))

def oem_settings(request: HttpRequest):
    from .models import OEMSettings
    oem = OEMSettings.get()
    error = None
    success = False

    if request.method == 'POST':
        oem.app_name          = request.POST.get('app_name', oem.app_name).strip() or oem.app_name
        oem.company_name      = request.POST.get('company_name', '').strip()
        oem.navbar_color      = request.POST.get('navbar_color', oem.navbar_color).strip()
        oem.navbar_text_color = request.POST.get('navbar_text_color', oem.navbar_text_color).strip()
        oem.primary_color     = request.POST.get('primary_color', oem.primary_color).strip()
        oem.logo_url          = request.POST.get('logo_url', '').strip()
        oem.footer_text       = request.POST.get('footer_text', oem.footer_text).strip()
        oem.save()
        success = True

    template = loader.get_template('oem_settings.html')
    return HttpResponse(template.render({'oem': oem, 'success': success, 'error': error}, request))

def online_devices(request : HttpRequest):
    template = loader.get_template('online_devices.html')
    
    return HttpResponse(template.render(
        { "model" : devices.get_all() },
        request))

def control_device(request : HttpRequest, connection_id : int):
    template = loader.get_template('control_device.html')
    
    return HttpResponse(template.render(
        {
           "connection_id" : connection_id,
           "model": devices.get(connection_id)
        },
        request))

def manage_users(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_users.html')
    model = None
    if request.method == "POST":
        form = forms.UserManagementForm(request.POST)
        if form.is_valid():
            if 'action_get_first' in request.POST.keys():
                model, form = users.get_first_user_data(connection_id, form)
            elif 'action_get_next' in request.POST.keys():
                model, form = users.get_next_user_data(connection_id, form)
            elif 'action_read' in request.POST.keys():
                model, form = users.read_user_data(connection_id, form)
            elif 'action_write' in request.POST.keys():
                model, form = users.write_user_data(connection_id, form)
            elif 'action_delete' in request.POST.keys():
                model, form = users.delete_user(connection_id, form)
    else:
        form = forms.UserManagementForm()
    
    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def manage_face_data(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_face_data.html')
    model = None
    if request.method == "POST":
        form = forms.FaceDataManagementForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                model, form = faces.read_face_data(connection_id, form)
            elif 'action_write' in request.POST.keys():
                model, form = faces.write_face_data(connection_id, form)
            elif 'action_delete' in request.POST.keys():
                model, form = faces.delete_face_data(connection_id, form)
    else:
        form = forms.FaceDataManagementForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def manage_fingerprint(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_fingerprint.html')
    model = None
    if request.method == "POST":
        form = forms.FingerprintManagementForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                model, form = fingerprints.read_fingerprint_data(connection_id, form)
            elif 'action_write' in request.POST.keys():
                model, form = fingerprints.write_fingerprint_data(connection_id, form)
            elif 'action_delete' in request.POST.keys():
                model, form = fingerprints.delete_fingerprint_data(connection_id, form)
    else:
        form = forms.FingerprintManagementForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def view_user_misc_cred(request : HttpRequest, connection_id : int):
    template = loader.get_template('view_user_misc_cred.html')
    model = None
    if request.method == "POST":
        form = forms.UserMiscCredForm(request.POST)
        if form.is_valid():
            if 'action_read_password' in request.POST.keys():
                model, form = misc_creds.read_user_password(connection_id, form)
            elif 'action_read_card' in request.POST.keys():
                model, form = misc_creds.read_user_card(connection_id, form)
            elif 'action_read_qr' in request.POST.keys():
                model, form = misc_creds.read_user_qr(connection_id, form)
    else:
        form = forms.UserMiscCredForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def manage_user_photo(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_user_photo.html')
    model = None
    if request.method == "POST":
        form = forms.UserPhotoManagementForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                model, form = user_photo.read_user_photo(connection_id, form)
            elif 'action_write' in request.POST.keys():
                model, form = user_photo.write_user_photo(connection_id, form)
            elif 'action_delete' in request.POST.keys():
                model, form = user_photo.delete_user_photo(connection_id, form)
    else:
        form = forms.UserPhotoManagementForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def manage_user_attend_only(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_user_attend_only.html')
    model = None
    if request.method == "POST":
        form = forms.UserAttendOnlyManagementForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                model, form = user_attend_only.read_user_attend_only(connection_id, form)
            elif 'action_write' in request.POST.keys():
                model, form = user_attend_only.write_user_attend_only(connection_id, form)
    else:
        form = forms.UserAttendOnlyManagementForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def remote_enroll(request : HttpRequest, connection_id : int):
    from .biz.remote_enroll import RemoteEnrollModel, start_remote_enroll, stop_remote_enroll, query_status

    template = loader.get_template('remote_enroll.html')
    model = RemoteEnrollModel()
    if request.method == "POST":
        form = forms.RemoteEnrollForm(request.POST)
        if form.is_valid():
            if 'action_start' in request.POST.keys():
                form = start_remote_enroll(connection_id, form, model)
            elif 'action_stop' in request.POST.keys():
                form = stop_remote_enroll(connection_id, form, model)
            elif 'action_query' in request.POST.keys():
                form = query_status(connection_id, form, model)
    else:
        form = forms.RemoteEnrollForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def enroll_face_by_photo(request : HttpRequest, connection_id : int):
    from .biz.photo_enroll import EnrollFaceByPhotoModel, enroll_face_by_photo

    template = loader.get_template('enroll_face_by_photo.html')
    model = EnrollFaceByPhotoModel()
    if request.method == "POST":
        form = forms.EnrollFaceByPhotoForm(request.POST)
        if form.is_valid():
            if 'action_enroll' in request.POST.keys():
                form = enroll_face_by_photo(connection_id, form, model)
    else:
        form = forms.EnrollFaceByPhotoForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def device_config_status(request : HttpRequest, connection_id : int):
    template = loader.get_template('device_config_status.html')
    model = device_controls.DeviceControlsModel()
    if request.method == "POST":
        form = forms.DeviceConfigAndStatusForm(request.POST)
        if form.is_valid():
            if 'action_disable_device' in request.POST.keys():
                device_controls.disable_device(connection_id, model)
            elif 'action_enable_device' in request.POST.keys():
                device_controls.enable_device(connection_id, model)
            elif 'action_get_time' in request.POST.keys():
                device_controls.get_device_time(connection_id, model)
            elif 'action_set_time' in request.POST.keys():
                device_controls.set_device_time(connection_id, model)
            elif 'action_get_status' in request.POST.keys():
                device_controls.get_device_status(connection_id, model, form)
            elif 'action_get_info' in request.POST.keys():
                device_controls.get_device_info(connection_id, model, form)
            elif 'action_set_info' in request.POST.keys():
                device_controls.set_device_info(connection_id, model, form)
            elif 'action_get_status_all' in request.POST.keys():
                device_controls.get_device_status_all(connection_id, model)
            elif 'action_get_info_all' in request.POST.keys():
                device_controls.get_device_info_all(connection_id, model)
    else:
        form = forms.DeviceConfigAndStatusForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_ntp_setting(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_ntp_setting.html')
    model = ntp_server_setting.NtpServerSettingModel()
    if request.method == "POST":
        form = forms.NtpServerSettingForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = ntp_server_setting.read_setting(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = ntp_server_setting.write_setting(connection_id, form, model)
    else:
        form = forms.NtpServerSettingForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_webserverurl_setting(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_webserverurl_setting.html')
    model = webserverurl_setting.WebServerUrlSettingModel()
    if request.method == "POST":
        form = forms.WebServerUrlSettingForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = webserverurl_setting.read_setting(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = webserverurl_setting.write_setting(connection_id, form, model)
    else:
        form = forms.WebServerUrlSettingForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_ethernet_setting(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_ethernet_setting.html')
    model = network_settings.NetworkSettingModel()
    if request.method == "POST":
        form = forms.EthernetSettingForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = network_settings.read_ethernet_setting(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = network_settings.write_ethernet_setting(connection_id, form, model)
    else:
        form = forms.EthernetSettingForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_wifi_setting(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_wifi_setting.html')
    model = network_settings.NetworkSettingModel()
    if request.method == "POST":
        form = forms.WifiSettingForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = network_settings.read_wifi_setting(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = network_settings.write_wifi_setting(connection_id, form, model)
    else:
        form = forms.WifiSettingForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def tr_icon_setting(request : HttpRequest, connection_id : int):
    from .biz.set_tr_icon import SetTrIconModel, set_tr_icon

    template = loader.get_template('tr_icon_setting.html')
    model = SetTrIconModel()
    if request.method == "POST":
        form = forms.SetTrIconForm(request.POST)
        if form.is_valid():
            if 'action_set' in request.POST.keys():
                form = set_tr_icon(connection_id, form, model)
    else:
        form = forms.SetTrIconForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def attendance_settings(request : HttpRequest, connection_id : int):
    template = loader.get_template('attendance_settings.html')

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id
        },
        request))

def manage_departments(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_departments.html')
    model = department_settings.DepartmentSettingsModel()
    if request.method == "POST":
        form = forms.DepartmentSettingsForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = department_settings.read_department_setting(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = department_settings.write_department_setting(connection_id, form, model)
    else:
        form = forms.DepartmentSettingsForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_proxy_departments(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_proxy_departments.html')
    model = department_settings.DepartmentSettingsModel()
    if request.method == "POST":
        form = forms.ProxyDepartmentSettingsForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = department_settings.read_proxy_department_setting(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = department_settings.write_proxy_department_setting(connection_id, form, model)
    else:
        form = forms.ProxyDepartmentSettingsForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_bell_settings(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_bell_settings.html')
    model = bell_settings.BellSettingsModel()
    if request.method == "POST":
        form = forms.BellSettingsForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = bell_settings.read_bell_settings(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = bell_settings.write_bell_settings(connection_id, form, model)
    else:
        form = forms.BellSettingsForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_auto_attendance_settings(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_auto_attendance_settings.html')
    model = auto_attendance_settings.AutoAttendanceSettingsModel()
    if request.method == "POST":
        form = forms.AutoAttendanceSettingsForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = auto_attendance_settings.read_auto_attendance_settings(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = auto_attendance_settings.write_auto_attendance_settings(connection_id, form, model)
    else:
        form = forms.AutoAttendanceSettingsForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_access_timezone_settings(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_access_timezone_settings.html')
    model = access_timezone_settings.AccessTimezoneSettingsModel()
    if request.method == "POST":
        form = forms.AccessTimezoneSettingsForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = access_timezone_settings.read_access_timezone_settings(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = access_timezone_settings.write_access_timezone_settings(connection_id, form, model)
    else:
        form = forms.AccessTimezoneSettingsForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def manage_lock_control(request : HttpRequest, connection_id : int):
    template = loader.get_template('lock_control.html')
    model = lock_control.LockControlModel()
    if request.method == "POST":
        form = forms.LockControlForm(request.POST)
        if form.is_valid():
            if 'action_read' in request.POST.keys():
                form = lock_control.read_lock_control_mode(connection_id, form, model)
            elif 'action_write' in request.POST.keys():
                form = lock_control.write_lock_control_mode(connection_id, form, model)
    else:
        form = forms.LockControlForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def view_device_attend_logs(request : HttpRequest, connection_id : int):
    template = loader.get_template('view_device_attend_logs.html')
    model = attend_logs.AttendLogsModel()
    if request.method == "POST":
        form = forms.AttendLogsForm(request.POST)
        if form.is_valid():
            if 'action_first' in request.POST.keys():
                form = attend_logs.get_first_log(connection_id, form, model)
            elif 'action_next' in request.POST.keys():
                form = attend_logs.get_next_log(connection_id, form, model)
            elif 'action_info' in request.POST.keys():
                form = attend_logs.get_log_pos_info(connection_id, form, model)
            elif 'action_delete' in request.POST.keys():
                form = attend_logs.delete_logs(connection_id, form, model)
    else:
        form = forms.AttendLogsForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def clear_data(request : HttpRequest, connection_id : int):
    from .biz.clear_data import ClearDataModel, clear_user_data, take_off_managers, clear_attendance_logs, clear_management_logs, clear_all

    template = loader.get_template('clear_data.html')
    model = ClearDataModel()
    if request.method == "POST":
        form = forms.ClearDataForm(request.POST)
        if form.is_valid():
            if   'action_clear_user_data' in request.POST.keys():
                form = clear_user_data(connection_id, form, model)
            elif 'action_take_off_managers' in request.POST.keys():
                form = take_off_managers(connection_id, form, model)
            elif 'action_clear_attendance_logs' in request.POST.keys():
                form = clear_attendance_logs(connection_id, form, model)
            elif 'action_clear_management_logs' in request.POST.keys():
                form = clear_management_logs(connection_id, form, model)
            elif 'action_clear_all' in request.POST.keys():
                form = clear_all(connection_id, form, model)
    else:
        form = forms.ClearDataForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))

def firmware_version(request : HttpRequest, connection_id : int):
    from .biz import firmware_version as B
    template = loader.get_template('firmware_version.html')
    model = B.FirmwareVersionModel()

    B.get_firmware_version(connection_id, model)

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
        },
        request))

def write_firmware(request : HttpRequest, connection_id : int):
    from .biz import write_firmware as B
    template = loader.get_template('write_firmware.html')
    model = B.WriteFirmwareModel()

    firmware_names  = [(x.name, x.name) for x in models.FirmwareBinary.objects.only("name").all()]
    public_url      = request.build_absolute_uri(reverse("index"))

    if request.method == "POST":
        form = forms.WriteFirmwareForm(request.POST, name_choices = firmware_names, public_url = public_url)
        if form.is_valid():
            if 'action_write' in request.POST.keys():
                B.write_firmware(connection_id, form, model)
    else:
        form = forms.WriteFirmwareForm(name_choices = firmware_names, public_url = public_url)

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "model": model,
            "form": form
        },
        request))


def manage_firmware(request):
    template = loader.get_template('manage_firmware.html')
    fw_list = models.FirmwareBinary.objects.only("name").all()

    return HttpResponse(template.render(
        {
            "firmware_list" : fw_list,
            "is_empty"      : len(fw_list) == 0
        },
        request))

def upload_firmware(request):
    from .biz.firmware_binaries import UploadFirmwareBinaryModel, upload_firmware
    template = loader.get_template('upload_firmware.html')

    model = UploadFirmwareBinaryModel()
    if request.method == "POST":
        form = forms.UploadFirmwareForm(request.POST)
        if form.is_valid():
            if 'action_upload' in request.POST.keys():
                if upload_firmware(form, model):
                    return HttpResponseRedirect(reverse('manage_firmware'))
    else:
        form = forms.UploadFirmwareForm()

    return HttpResponse(template.render(
        {
            "form": form,
            "model": model
        },
        request))

@csrf_exempt
def get_firmware(request, firmware_name : str):
    try:
        fw = models.FirmwareBinary.objects.get(name = firmware_name)
        return HttpResponse(
            content = fw.data,
            content_type = "application/octet-stream",
            headers = {
                "Content-Disposition": f"attachment; filename=\"{firmware_name}.bin\""
            }
        )
    except models.FirmwareBinary.DoesNotExist:
        return HttpResponseNotFound()

def delete_firmware(request, firmware_name : str):
    try:
        fw = models.FirmwareBinary.objects.only("name").get(name = firmware_name)
        fw.delete()

        return HttpResponseRedirect(reverse('manage_firmware'))
    except models.FirmwareBinary.DoesNotExist:
        return HttpResponseNotFound()

def search_attend_logs(request : HttpRequest, device_id : Optional[str] = None):
    from django.db.models import Q
    template = loader.get_template('search_attend_logs.html')

    count_limit = 100
    query = models.AttendanceLog.objects
    if device_id is not None:
        query = query.filter(device_id = device_id)

    num_deleted : Optional[int] = None

    if request.method == "POST":
        form = forms.AttendLogFilterForm(request.POST, show_device_id = device_id is None)
        if form.is_valid():
            if device_id is None and (form_device_id := form.cleaned_data["device_id"]):
                query = query.filter(device_id = form_device_id)
            if (user_id := form.cleaned_data["user_id"]):
                query = query.filter(user_id = int(user_id))
            if (start_time := form.cleaned_data["start_time"]) is not None:
                query = query.filter(Q(time__gte = start_time))
            if (end_time := form.cleaned_data["end_time"]) is not None:
                query = query.filter(Q(time__lte = end_time))

            if 'action_clear' in request.POST.keys():
                num_deleted, _ = query.all().delete()
    else:
        form = forms.AttendLogFilterForm(show_device_id = device_id is None)

    logs = list(query.order_by("-id")[:count_limit].defer("photo"))

    return HttpResponse(template.render(
        {
            "device_id"     : device_id,
            "logs"          : logs,
            "is_empty"      : len(logs) == 0,
            "count_limit"   : count_limit if len(logs) == count_limit else None,
            "form"          : form,
            "num_deleted"   : num_deleted
        },
        request))

def attend_log_details(request : HttpRequest, id : int):
    template = loader.get_template('attend_log_details.html')

    log = models.AttendanceLog.objects.get(id = id)
    return HttpResponse(template.render(
        {
            "log"                   : log,
            "encoded_photo_data"    : None if log.photo is None else urllib.parse.quote_from_bytes(log.photo),
            "back_url"              : request.GET.get("back_url", None)
        },
        request))

def search_management_logs(request : HttpRequest, device_id : Optional[str] = None):
    from django.db.models import Q
    template = loader.get_template('search_management_logs.html')

    count_limit = 100
    query = models.ManagementLog.objects
    if device_id is not None:
        query = query.filter(device_id = device_id)

    num_deleted : Optional[int] = None

    if request.method == "POST":
        form = forms.ManagementLogFilterForm(request.POST, show_device_id = device_id is None)
        if form.is_valid():
            if device_id is None and (form_device_id := form.cleaned_data["device_id"]):
                query = query.filter(device_id = form_device_id)
            if (start_time := form.cleaned_data["start_time"]) is not None:
                query = query.filter(Q(time__gte = start_time))
            if (end_time := form.cleaned_data["end_time"]) is not None:
                query = query.filter(Q(time__lte = end_time))

            if 'action_clear' in request.POST.keys():
                num_deleted, _ = query.all().delete()
    else:
        form = forms.ManagementLogFilterForm(show_device_id = device_id is None)

    logs = list(query.order_by("-id")[:count_limit])

    return HttpResponse(template.render(
        {
            "device_id"     : device_id,
            "logs"          : logs,
            "is_empty"      : len(logs) == 0,
            "count_limit"   : count_limit if len(logs) == count_limit else None,
            "form"          : form,
            "num_deleted"   : num_deleted
        },
        request))

def center_message_setting(request : HttpRequest, connection_id : int):
    from .biz.misc import CenterMessageSettingModel, get_center_message_setting, set_center_message_setting

    template = loader.get_template('center_message_setting.html')
    model = CenterMessageSettingModel()
    if request.method == "POST":
        form = forms.CenterMessageSettingForm(request.POST)
        if form.is_valid():
            if "action_read" in request.POST.keys():
                form = get_center_message_setting(connection_id, form, model)
            elif "action_write" in request.POST.keys():
                form = set_center_message_setting(connection_id, form, model)
    else:
        form = forms.CenterMessageSettingForm()

    return HttpResponse(template.render(
        {
            "form"          : form,
            "model"         : model,
            "connection_id" : connection_id
        },
        request))

def video_streaming_setting(request : HttpRequest, connection_id : int):
    from .biz.misc import VideoStreamingSettingModel, get_video_streaming_setting, set_video_streaming_setting

    template = loader.get_template('video_streaming_setting.html')
    model = VideoStreamingSettingModel()
    if request.method == "POST":
        form = forms.VideoStreamingSettingForm(request.POST)
        if form.is_valid():
            if "action_read" in request.POST.keys():
                form = get_video_streaming_setting(connection_id, form, model)
            elif "action_write" in request.POST.keys():
                form = set_video_streaming_setting(connection_id, form, model)
    else:
        form = forms.VideoStreamingSettingForm()

    return HttpResponse(template.render(
        {
            "form"          : form,
            "model"         : model,
            "connection_id" : connection_id
        },
        request))

def manage_user_message(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_user_message.html')
    model = None
    if request.method == "POST":
        form = forms.UserMessageManagementForm(request.POST)
        if form.is_valid():
            if 'action_get_user_message' in request.POST.keys():
                model, form = user_message.get_user_message(connection_id, form)
            elif 'action_set_user_message' in request.POST.keys():
                model, form = user_message.set_user_message(connection_id, form)
            if 'action_get_message_color' in request.POST.keys():
                model, form = user_message.get_message_color(connection_id, form)
            elif 'action_set_message_color' in request.POST.keys():
                model, form = user_message.set_message_color(connection_id, form)
    else:
        form = forms.UserMessageManagementForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))

def manage_user_german(request : HttpRequest, connection_id : int):
    template = loader.get_template('manage_user_german.html')
    model = None
    if request.method == "POST":
        form = forms.UserManagementGermanForm(request.POST)
        if form.is_valid():
            if 'action_get_user_message' in request.POST.keys():
                model, form = user_german.get_user_message(connection_id, form)
            elif 'action_set_user_message' in request.POST.keys():
                model, form = user_german.set_user_message(connection_id, form)
            elif 'action_get_balance_time' in request.POST.keys():
                model, form = user_german.get_balance_time(connection_id, form)
            elif 'action_set_balance_time' in request.POST.keys():
                model, form = user_german.set_balance_time(connection_id, form)
            elif 'action_get_holidays' in request.POST.keys():
                model, form = user_german.get_holidays(connection_id, form)
            elif 'action_set_holidays' in request.POST.keys():
                model, form = user_german.set_holidays(connection_id, form)
    else:
        form = forms.UserManagementGermanForm()

    return HttpResponse(template.render(
        {
            "connection_id" : connection_id,
            "form": form,
            "model": model
        },
        request))



    from django.template import loader
    from django.http import HttpResponse


    context = {
        "devices": devices,
        "error_msg": None,
        "success_msg": None,
        "sync_log": None,
    }

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "sync":
            host_id = request.POST.get("host", "")
            target_ids = request.POST.getlist("targets")

            if not host_id:
                context["error_msg"] = "Select a Host device."
            elif not target_ids:
                context["error_msg"] = "Select at least one Target device."
            else:
                # Remove host from targets if present
                target_ids = [t for t in target_ids if t != host_id]
                if not target_ids:
                    context["error_msg"] = "Target must be different from Host."
                else:
                    context["sync_log"] = log
                    context["success_msg"] = "Sync complete: " + host_id + " -> " + ", ".join(target_ids)

    return HttpResponse(template.render(context, request))


    from django.template import loader
    from django.http import HttpResponse


    context = {
        "devices":     devices,
        "error_msg":   None,
        "success_msg": None,
        "sync_log":    None,
    }

    if request.method == "POST" and request.POST.get("action") == "sync":
        host_id    = request.POST.get("host", "").strip()
        target_ids = [t.strip() for t in request.POST.getlist("targets") if t.strip()]

        if not host_id:
            context["error_msg"] = "Please select a Host device."
        elif not target_ids:
            context["error_msg"] = "Please select at least one Target device."
        else:
            # Ensure host is not in targets
            target_ids = [t for t in target_ids if t != host_id]
            if not target_ids:
                context["error_msg"] = "Target must be different from Host."
            else:
                context["sync_log"]    = sync_log
                context["success_msg"] = (
                    f"Sync complete: {host_id} → {', '.join(target_ids)}"
                )

    return HttpResponse(template.render(context, request))


    from django.template import loader
    from django.http import HttpResponse


    context = {
        "devices":     devices,
        "error_msg":   None,
        "success_msg": None,
        "sync_log":    None,
    }

    if request.method == "POST" and request.POST.get("action") == "sync":
        host_id    = request.POST.get("host", "").strip()
        target_ids = [t.strip() for t in request.POST.getlist("targets") if t.strip()]

        if not host_id:
            context["error_msg"] = "Please select a Host device."
        elif not target_ids:
            context["error_msg"] = "Please select at least one Target device."
        else:
            # Ensure host is not in targets
            target_ids = [t for t in target_ids if t != host_id]
            if not target_ids:
                context["error_msg"] = "Target must be different from Host."
            else:
                context["sync_log"]    = sync_log
                context["success_msg"] = (
                    f"Sync complete: {host_id} → {', '.join(target_ids)}"
                )

    return HttpResponse(template.render(context, request))


    from django.template import loader
    from django.http import HttpResponse


    context = {
        "devices":     devices,
        "error_msg":   None,
        "success_msg": None,
        "sync_log":    None,
    }

    if request.method == "POST" and request.POST.get("action") == "sync":
        host_id    = request.POST.get("host", "").strip()
        target_ids = [t.strip() for t in request.POST.getlist("targets") if t.strip()]

        if not host_id:
            context["error_msg"] = "Please select a Host device."
        elif not target_ids:
            context["error_msg"] = "Please select at least one Target device."
        else:
            # Ensure host is not in targets
            target_ids = [t for t in target_ids if t != host_id]
            if not target_ids:
                context["error_msg"] = "Target must be different from Host."
            else:
                context["sync_log"]    = sync_log
                context["success_msg"] = (
                    f"Sync complete: {host_id} → {', '.join(target_ids)}"
                )

    return HttpResponse(template.render(context, request))


    from django.template import loader
    from django.http import HttpResponse


    context = {
        "devices":     devices,
        "error_msg":   None,
        "success_msg": None,
        "sync_log":    None,
    }

    if request.method == "POST" and request.POST.get("action") == "sync":
        mode       = request.POST.get("sync_mode", "merge").strip()
        host_id    = request.POST.get("host", "").strip()
        target_ids = [t.strip() for t in request.POST.getlist("targets") if t.strip()]

        if mode == "bidirectional":
            if len(target_ids) < 2:
                context["error_msg"] = "Select at least 2 devices for bidirectional merge."
            else:
                context["sync_log"]    = sync_log
                context["success_msg"] = "Bidirectional merge complete for: " + ", ".join(target_ids)
        else:
            mirror = (mode == "mirror")
            if not host_id:
                context["error_msg"] = "Please select a Host device."
            elif not target_ids:
                context["error_msg"] = "Please select at least one Target device."
            else:
                target_ids = [t for t in target_ids if t != host_id]
                if not target_ids:
                    context["error_msg"] = "Target must be different from Host."
                else:
                    mode_label = "Mirror" if mirror else "Merge"
                    context["sync_log"]    = sync_log
                    context["success_msg"] = f"{mode_label} complete: {host_id} → {', '.join(target_ids)}"

    return HttpResponse(template.render(context, request))
