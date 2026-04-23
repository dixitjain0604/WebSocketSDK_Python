import csv
import json
import secrets
from typing import Optional
import urllib
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.db.models import F
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, JsonResponse, StreamingHttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import requests

from .biz import devices, users, faces, fingerprints, misc_creds, user_photo, user_attend_only, user_message, user_german
from .biz import device_controls, ntp_server_setting, webserverurl_setting, network_settings
from .biz import department_settings, bell_settings, auto_attendance_settings, access_timezone_settings, lock_control, attend_logs
from . import forms
from . import models

@csrf_exempt
def check_device_registration(request: HttpRequest):
    data = json.loads(request.body) if request.body else {}
    sn = data.get("sn", "")
    terminal_type = data.get("terminal_type", "")
    product_name = data.get("product_name", "")

    if not sn:
        return JsonResponse({"token": ""}, status=400)

    reg, _ = models.DeviceRegistry.objects.get_or_create(serial_number=sn)
    reg.terminal_type = terminal_type or reg.terminal_type
    reg.product_name = product_name or reg.product_name
    if not reg.token:
        reg.token = secrets.token_hex(16)
    reg.save()
    return JsonResponse({"token": reg.token})

@csrf_exempt
def check_device_login(request: HttpRequest):
    data = json.loads(request.body) if request.body else {}
    sn = data.get("sn", "")
    token = data.get("token", "")

    if not sn or not token:
        return JsonResponse({"reason": "Missing SN or token"}, status=403)

    try:
        reg = models.DeviceRegistry.objects.get(serial_number=sn)
        if not reg.is_active:
            return JsonResponse({"reason": "Device disabled"}, status=403)
        if reg.token != token:
            return JsonResponse({"reason": "Invalid token"}, status=403)
        reg.last_seen = timezone.now()
        reg.save(update_fields=["last_seen"])
        return JsonResponse({})
    except models.DeviceRegistry.DoesNotExist:
        return JsonResponse({"reason": "Unknown device"}, status=403)

@csrf_exempt
def connection_event(request: HttpRequest):
    data = json.loads(request.body) if request.body else {}
    device_id = data.get("device_id", "")
    event = data.get("event", "")
    if device_id and event in (models.DeviceConnectionLog.CONNECT, models.DeviceConnectionLog.DISCONNECT):
        models.DeviceConnectionLog.objects.create(device_id=device_id, event=event)
        if event == models.DeviceConnectionLog.CONNECT:
            terminal_type = data.get("terminal_type", "")
            product_name = data.get("product_name", "")
            update_fields = {"last_seen": timezone.now()}
            if terminal_type:
                update_fields["terminal_type"] = terminal_type
            if product_name:
                update_fields["product_name"] = product_name
            models.DeviceRegistry.objects.filter(serial_number=device_id).update(**update_fields)
    return JsonResponse({})

@csrf_exempt
def upload_device_log(request: HttpRequest):
    from .biz.log_upload import save_device_log
    contents = json.loads(request.body)
    save_device_log(contents)

    interlock_devices = []
    log_type = request.GET.get("type", "")
    if log_type in ("TimeLog", "TimeLog_v2"):
        user_id_str = contents.get("UserID", "")
        punched_device = contents.get("_device_id", "")
        client_id = contents.get("_client_id", None)
        if user_id_str and punched_device:
            try:
                uid = int(user_id_str)
                interlock_devices = _process_interlock(uid, punched_device, client_id)
            except (ValueError, TypeError):
                pass

    return JsonResponse({"interlock_devices": interlock_devices})


def _process_interlock(employee_id: int, punched_device: str, punched_client_id) -> list:
    """Return list of client_ids of OTHER interlock-enabled devices where user should be denied."""
    if not models.DeviceRegistry.objects.filter(serial_number=punched_device, interlock_enabled=True).exists():
        return []

    models.InterlockState.objects.update_or_create(
        employee_id=employee_id,
        defaults={"punched_device": punched_device, "punch_time": timezone.now(), "interlock_active": True}
    )

    interlock_serials = list(models.DeviceRegistry.objects.filter(
        interlock_enabled=True
    ).exclude(serial_number=punched_device).values_list("serial_number", flat=True))

    if not interlock_serials:
        return []

    try:
        from .biz import connection as biz_connection
        with biz_connection.open() as c:
            online = c.get_all_online_devices()
        return [d.connection_id for d in online if d.device_id in interlock_serials]
    except Exception:
        return []

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
        oem.footer_text       = request.POST.get('footer_text', oem.footer_text).strip()
        if request.POST.get('remove_logo'):
            if oem.logo:
                oem.logo.delete(save=False)
            oem.logo = None
        elif 'logo' in request.FILES:
            uploaded = request.FILES['logo']
            allowed = {'image/svg+xml', 'image/jpeg', 'image/png', 'application/pdf'}
            if uploaded.content_type not in allowed:
                error = 'Unsupported file type. Please upload SVG, JPEG, PNG, or PDF.'
            else:
                if oem.logo:
                    oem.logo.delete(save=False)
                oem.logo = uploaded
        if not error:
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


# ─── Zone Management ──────────────────────────────────────────────────────────

def zone_list(request: HttpRequest):
    zones = models.Zone.objects.prefetch_related("devices").all()
    return HttpResponse(loader.get_template("zone_list.html").render({"zones": zones}, request))

def zone_create(request: HttpRequest):
    error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if not name:
            error = "Name is required."
        elif models.Zone.objects.filter(name=name).exists():
            error = "A zone with this name already exists."
        else:
            models.Zone.objects.create(name=name, description=description)
            return HttpResponseRedirect(reverse("zone_list"))
    return HttpResponse(loader.get_template("zone_form.html").render({"action": "Create", "error": error}, request))

def zone_edit(request: HttpRequest, zone_id: int):
    zone = get_object_or_404(models.Zone, pk=zone_id)
    error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if not name:
            error = "Name is required."
        elif models.Zone.objects.filter(name=name).exclude(pk=zone_id).exists():
            error = "A zone with this name already exists."
        else:
            zone.name = name
            zone.description = description
            zone.save()
            return HttpResponseRedirect(reverse("zone_list"))
    return HttpResponse(loader.get_template("zone_form.html").render({"action": "Edit", "zone": zone, "error": error}, request))

def zone_delete(request: HttpRequest, zone_id: int):
    zone = get_object_or_404(models.Zone, pk=zone_id)
    if request.method == "POST":
        zone.delete()
        return HttpResponseRedirect(reverse("zone_list"))
    return HttpResponse(loader.get_template("zone_confirm_delete.html").render({"zone": zone}, request))


# ─── Device Registry Management ───────────────────────────────────────────────

def device_registry_list(request: HttpRequest):
    devices_qs = models.DeviceRegistry.objects.select_related("zone").all()
    try:
        from .biz import connection as biz_conn
        with biz_conn.open() as c:
            online = {d.device_id for d in c.get_all_online_devices()}
    except Exception:
        online = set()
    return HttpResponse(loader.get_template("device_registry_list.html").render(
        {"devices": devices_qs, "online_ids": online}, request))

def device_registry_create(request: HttpRequest):
    zones = models.Zone.objects.all()
    error = None
    if request.method == "POST":
        sn = request.POST.get("serial_number", "").strip()
        if not sn:
            error = "Serial number is required."
        elif models.DeviceRegistry.objects.filter(serial_number=sn).exists():
            error = "A device with this serial number already exists."
        else:
            zone_id = request.POST.get("zone") or None
            models.DeviceRegistry.objects.create(
                serial_number=sn,
                friendly_name=request.POST.get("friendly_name", "").strip(),
                location=request.POST.get("location", "").strip(),
                zone_id=zone_id,
                interlock_enabled=bool(request.POST.get("interlock_enabled")),
                is_active=True,
            )
            return HttpResponseRedirect(reverse("device_registry_list"))
    return HttpResponse(loader.get_template("device_registry_form.html").render(
        {"action": "Add", "zones": zones, "error": error}, request))

def device_registry_edit(request: HttpRequest, device_id: int):
    dev = get_object_or_404(models.DeviceRegistry, pk=device_id)
    zones = models.Zone.objects.all()
    error = None
    if request.method == "POST":
        dev.friendly_name = request.POST.get("friendly_name", "").strip()
        dev.location = request.POST.get("location", "").strip()
        zone_id = request.POST.get("zone") or None
        dev.zone_id = zone_id
        dev.is_active = bool(request.POST.get("is_active"))
        dev.interlock_enabled = bool(request.POST.get("interlock_enabled"))
        dev.save()
        return HttpResponseRedirect(reverse("device_registry_list"))
    return HttpResponse(loader.get_template("device_registry_form.html").render(
        {"action": "Edit", "dev": dev, "zones": zones, "error": error}, request))

def device_registry_delete(request: HttpRequest, device_id: int):
    dev = get_object_or_404(models.DeviceRegistry, pk=device_id)
    if request.method == "POST":
        dev.delete()
        return HttpResponseRedirect(reverse("device_registry_list"))
    return HttpResponse(loader.get_template("device_registry_confirm_delete.html").render({"dev": dev}, request))

def device_connection_logs(request: HttpRequest):
    logs = models.DeviceConnectionLog.objects.all()[:200]
    return HttpResponse(loader.get_template("device_connection_logs.html").render({"logs": logs}, request))


# ─── Device Restart (dedicated) ───────────────────────────────────────────────

def restart_device(request: HttpRequest, connection_id: int):
    from .biz import lock_control as lc
    model = lc.LockControlModel()
    form = forms.LockControlForm({"mode": "Restart"})
    form.is_valid()
    lc.write_lock_control_mode(connection_id, form, model)
    if model.error_msg:
        return JsonResponse({"ok": False, "error": model.error_msg})
    return JsonResponse({"ok": True})


# ─── Sync Users (wired view) ──────────────────────────────────────────────────

def sync_users_view(request: HttpRequest):
    from .biz.sync_users_biz import get_devices_with_status, run_sync, run_sync_bidirectional
    all_devices = []
    try:
        all_devices = get_devices_with_status()
    except Exception:
        pass

    error_msg = None
    success_msg = None
    sync_log = None

    if request.method == "POST":
        mode = request.POST.get("sync_mode", "merge").strip()
        host_id = request.POST.get("host", "").strip()
        target_ids = [t.strip() for t in request.POST.getlist("targets") if t.strip()]

        if mode == "bidirectional":
            all_ids = [t.strip() for t in request.POST.getlist("targets") if t.strip()]
            if len(all_ids) < 2:
                error_msg = "Select at least 2 devices for bidirectional merge."
            else:
                sync_log = run_sync_bidirectional(all_ids)
                success_msg = "Bidirectional merge complete."
        else:
            mirror = (mode == "mirror")
            if not host_id:
                error_msg = "Please select a Host device."
            elif not target_ids:
                error_msg = "Please select at least one Target device."
            else:
                target_ids = [t for t in target_ids if t != host_id]
                if not target_ids:
                    error_msg = "Target must be different from Host."
                else:
                    sync_log = run_sync(host_id, target_ids, mirror=mirror)
                    mode_label = "Mirror" if mirror else "Merge"
                    success_msg = f"{mode_label} sync complete."

    return HttpResponse(loader.get_template("sync_users.html").render({
        "devices":     all_devices,
        "error_msg":   error_msg,
        "success_msg": success_msg,
        "sync_log":    sync_log,
    }, request))


def zone_sync_view(request: HttpRequest, zone_id: int):
    from .biz.sync_users_biz import get_devices_with_status, run_sync_bidirectional
    zone = get_object_or_404(models.Zone, pk=zone_id)
    zone_serials = set(zone.devices.values_list("serial_number", flat=True))
    error_msg = None
    success_msg = None
    sync_log = None

    if request.method == "POST":
        try:
            all_online = get_devices_with_status()
            zone_online_ids = [
                str(getattr(d, "device_id", ""))
                for d in all_online
                if str(getattr(d, "device_id", "")) in zone_serials
            ]
            if len(zone_online_ids) < 2:
                error_msg = "Need at least 2 online devices in this zone to sync."
            else:
                sync_log = run_sync_bidirectional(zone_online_ids)
                success_msg = f"Zone '{zone.name}' sync complete."
        except Exception as ex:
            error_msg = str(ex)

    return HttpResponse(loader.get_template("zone_sync.html").render({
        "zone": zone,
        "zone_serials": zone_serials,
        "error_msg": error_msg,
        "success_msg": success_msg,
        "sync_log": sync_log,
    }, request))


# ─── Employee Management (auto-push to devices) ───────────────────────────────

def employee_list(request: HttpRequest):
    emps = models.Employee.objects.all().order_by("employee_id")
    return HttpResponse(loader.get_template("employee_list.html").render({"employees": emps}, request))

def employee_create(request: HttpRequest):
    error = None
    if request.method == "POST":
        try:
            emp_id = int(request.POST.get("employee_id", 0))
        except ValueError:
            error = "Employee ID must be a number."
            emp_id = 0

        if not error:
            if models.Employee.objects.filter(employee_id=emp_id).exists():
                error = "Employee with this ID already exists."
            else:
                period_start = request.POST.get("period_start") or None
                period_end = request.POST.get("period_end") or None
                emp = models.Employee.objects.create(
                    employee_id=emp_id,
                    name=request.POST.get("name", "").strip(),
                    department=int(request.POST.get("department", 0) or 0),
                    privilege=int(request.POST.get("privilege", 0) or 0),
                    enabled=bool(request.POST.get("enabled")),
                    card=request.POST.get("card", "").strip() or None,
                    password=request.POST.get("password", "").strip() or None,
                    period_start=period_start,
                    period_end=period_end,
                    timeset_1=int(request.POST.get("timeset_1", -1) or -1),
                    timeset_2=int(request.POST.get("timeset_2", -1) or -1),
                    timeset_3=int(request.POST.get("timeset_3", -1) or -1),
                    timeset_4=int(request.POST.get("timeset_4", -1) or -1),
                    timeset_5=int(request.POST.get("timeset_5", -1) or -1),
                )
                _push_employee_to_all_devices(emp)
                return HttpResponseRedirect(reverse("employee_list"))

    return HttpResponse(loader.get_template("employee_form.html").render({"action": "Add", "error": error}, request))

def employee_edit(request: HttpRequest, employee_id: int):
    emp = get_object_or_404(models.Employee, pk=employee_id)
    error = None
    if request.method == "POST":
        emp.name = request.POST.get("name", "").strip()
        emp.department = int(request.POST.get("department", 0) or 0)
        emp.privilege = int(request.POST.get("privilege", 0) or 0)
        emp.enabled = bool(request.POST.get("enabled"))
        emp.card = request.POST.get("card", "").strip() or None
        emp.password = request.POST.get("password", "").strip() or None
        emp.period_start = request.POST.get("period_start") or None
        emp.period_end = request.POST.get("period_end") or None
        emp.timeset_1 = int(request.POST.get("timeset_1", -1) or -1)
        emp.timeset_2 = int(request.POST.get("timeset_2", -1) or -1)
        emp.timeset_3 = int(request.POST.get("timeset_3", -1) or -1)
        emp.timeset_4 = int(request.POST.get("timeset_4", -1) or -1)
        emp.timeset_5 = int(request.POST.get("timeset_5", -1) or -1)
        emp.save()
        _push_employee_to_all_devices(emp)
        return HttpResponseRedirect(reverse("employee_list"))

    return HttpResponse(loader.get_template("employee_form.html").render({"action": "Edit", "emp": emp, "error": error}, request))

def employee_delete(request: HttpRequest, employee_id: int):
    emp = get_object_or_404(models.Employee, pk=employee_id)
    if request.method == "POST":
        _delete_employee_from_all_devices(emp.employee_id)
        emp.delete()
        return HttpResponseRedirect(reverse("employee_list"))
    return HttpResponse(loader.get_template("employee_confirm_delete.html").render({"emp": emp}, request))

def employee_enable_disable(request: HttpRequest, employee_id: int):
    emp = get_object_or_404(models.Employee, pk=employee_id)
    emp.enabled = not emp.enabled
    emp.save()
    _push_employee_to_all_devices(emp)
    return HttpResponseRedirect(reverse("employee_list"))

def _push_employee_to_all_devices(emp: 'models.Employee'):
    from .biz import connection as biz_conn
    from .biz.sync_users_biz import _push_user
    try:
        with biz_conn.open() as c:
            online = c.get_all_online_devices()
            if not online:
                return
            user_dict = {
                "name": emp.name,
                "privilege": "Admin" if emp.privilege >= 1 else "User",
                "enabled": "Yes" if emp.enabled else "No",
                "department": str(emp.department),
                "timeset1": str(emp.timeset_1),
                "timeset2": str(emp.timeset_2),
                "timeset3": str(emp.timeset_3),
                "timeset4": str(emp.timeset_4),
                "timeset5": str(emp.timeset_5),
                "period_used": "Yes" if (emp.period_start and emp.period_end) else "No",
                "period_start": str(emp.period_start) if emp.period_start else "",
                "period_end": str(emp.period_end) if emp.period_end else "",
                "card": emp.card or "",
                "password": emp.password or "",
                "qr": "",
                "fingers": {},
                "face": "",
                "photo": "",
                "photo_size": "",
            }
            for dev in online:
                _push_user(c, dev.connection_id, str(emp.employee_id), user_dict, [])
    except Exception:
        pass

def _delete_employee_from_all_devices(employee_id: int):
    from .biz import connection as biz_conn
    from .biz.sync_users_biz import _build_xml, _send_with_conn
    try:
        with biz_conn.open() as c:
            online = c.get_all_online_devices()
            for dev in online:
                xml = _build_xml({"Request": "SetUserData", "UserID": str(employee_id), "Type": "Delete"})
                _send_with_conn(c, dev.connection_id, xml, f"Delete EMP={employee_id}")
    except Exception:
        pass


# ─── Bulk Log Download (CSV export) ──────────────────────────────────────────

def download_logs_csv(request: HttpRequest):
    from django.db.models import Q
    start_time = request.GET.get("start")
    end_time = request.GET.get("end")
    device_id = request.GET.get("device_id", "")

    query = models.AttendanceLog.objects.defer("photo")
    if device_id:
        query = query.filter(device_id=device_id)
    if start_time:
        query = query.filter(time__gte=start_time)
    if end_time:
        query = query.filter(time__lte=end_time)

    def rows():
        yield ",".join(["ID","Device","LogID","Time","UserID","AttendStatus","Action","AttendOnly","Expired"]) + "\n"
        for log in query.iterator():
            yield ",".join([
                str(log.id),
                str(log.device_id),
                str(log.log_id),
                str(log.time or ""),
                str(log.user_id or ""),
                str(log.attend_status or ""),
                str(log.action or ""),
                "Yes" if log.attend_only else "No",
                "Yes" if log.expired else "No",
            ]) + "\n"

    response = StreamingHttpResponse(rows(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendance_logs.csv"'
    return response

def bulk_download_from_device(request: HttpRequest, connection_id: int):
    """Download all logs from a device for a given date range and save to DB."""
    from .biz import connection as biz_conn
    from devicebroker.device_cmd.m50 import log as L
    import datetime

    error = None
    saved_count = 0

    if request.method == "POST":
        start_str = request.POST.get("start_time", "").strip()
        end_str = request.POST.get("end_time", "").strip()
        try:
            start_dt = datetime.datetime.fromisoformat(start_str) if start_str else None
            end_dt = datetime.datetime.fromisoformat(end_str) if end_str else None
        except ValueError:
            error = "Invalid date format. Use YYYY-MM-DDTHH:MM"
            start_dt = end_dt = None

        if not error:
            try:
                with biz_conn.open() as c:
                    dev = c.get_online_device(connection_id)
                    device_id = dev.device_id if dev else ""

                    resp = L.GetFirstGlogRequest(start_time=start_dt, end_time=end_dt).transact(c, connection_id)
                    while resp.has_succeeded():
                        log = resp.log
                        models.AttendanceLog.objects.get_or_create(
                            device_id=device_id,
                            log_id=log.log_id,
                            defaults={
                                "time": log.time,
                                "user_id": log.user_id,
                                "timezone_offset": log.timezone_offset,
                                "attend_status": str(log.attend_status) if log.attend_status else None,
                                "action": str(log.action) if log.action else None,
                                "job_code": log.job_code,
                                "photo": log.photo,
                                "body_temperature": log.body_temperature,
                                "attend_only": log.attend_only,
                                "expired": log.expired,
                                "latitude": log.latitude,
                                "longitude": log.longitude,
                            }
                        )
                        saved_count += 1
                        next_resp = L.GetNextGlogRequest(log.log_id + 1).transact(c, connection_id)
                        resp = next_resp
            except Exception as ex:
                error = str(ex)

    return HttpResponse(loader.get_template("bulk_download_logs.html").render({
        "connection_id": connection_id,
        "error": error,
        "saved_count": saved_count,
    }, request))


# ─── External REST API ────────────────────────────────────────────────────────

def _require_api_key(request: HttpRequest) -> Optional[models.APIKey]:
    key_str = request.headers.get("X-API-Key", "") or request.GET.get("api_key", "")
    if not key_str:
        return None
    try:
        key = models.APIKey.objects.get(key=key_str, is_active=True)
        key.last_used = timezone.now()
        key.save(update_fields=["last_used"])
        return key
    except models.APIKey.DoesNotExist:
        return None

@csrf_exempt
def api_employees(request: HttpRequest):
    if not _require_api_key(request):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method == "GET":
        emps = list(models.Employee.objects.values())
        return JsonResponse({"employees": emps})

    elif request.method == "POST":
        data = json.loads(request.body)
        try:
            emp_id = int(data["employee_id"])
        except (KeyError, ValueError):
            return JsonResponse({"error": "employee_id required"}, status=400)
        if models.Employee.objects.filter(employee_id=emp_id).exists():
            return JsonResponse({"error": "Employee already exists"}, status=409)
        emp = models.Employee.objects.create(
            employee_id=emp_id,
            name=data.get("name", ""),
            department=int(data.get("department", 0)),
            privilege=int(data.get("privilege", 0)),
            enabled=data.get("enabled", True),
            card=data.get("card") or None,
            password=data.get("password") or None,
            timeset_1=int(data.get("timeset_1", -1)),
            timeset_2=int(data.get("timeset_2", -1)),
            timeset_3=int(data.get("timeset_3", -1)),
            timeset_4=int(data.get("timeset_4", -1)),
            timeset_5=int(data.get("timeset_5", -1)),
        )
        _push_employee_to_all_devices(emp)
        return JsonResponse({"id": emp.pk, "employee_id": emp.employee_id}, status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def api_employee_detail(request: HttpRequest, employee_id: int):
    if not _require_api_key(request):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        emp = models.Employee.objects.get(employee_id=employee_id)
    except models.Employee.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "employee_id": emp.employee_id, "name": emp.name,
            "department": emp.department, "privilege": emp.privilege,
            "enabled": emp.enabled, "card": emp.card,
        })

    elif request.method in ("PUT", "PATCH"):
        data = json.loads(request.body)
        for field in ("name", "department", "privilege", "enabled", "card", "password",
                      "timeset_1", "timeset_2", "timeset_3", "timeset_4", "timeset_5",
                      "period_start", "period_end"):
            if field in data:
                setattr(emp, field, data[field])
        emp.save()
        _push_employee_to_all_devices(emp)
        return JsonResponse({"ok": True})

    elif request.method == "DELETE":
        _delete_employee_from_all_devices(emp.employee_id)
        emp.delete()
        return JsonResponse({"ok": True})

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def api_logs(request: HttpRequest):
    if not _require_api_key(request):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    from django.db.models import Q
    query = models.AttendanceLog.objects.defer("photo")
    if (device_id := request.GET.get("device_id")):
        query = query.filter(device_id=device_id)
    if (user_id := request.GET.get("user_id")):
        query = query.filter(user_id=int(user_id))
    if (start := request.GET.get("start")):
        query = query.filter(time__gte=start)
    if (end := request.GET.get("end")):
        query = query.filter(time__lte=end)

    logs = list(query.order_by("-id")[:500].values(
        "id", "device_id", "log_id", "time", "user_id", "attend_status", "action", "attend_only", "expired"
    ))
    return JsonResponse({"logs": logs})

@csrf_exempt
def api_devices(request: HttpRequest):
    if not _require_api_key(request):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        from .biz import connection as biz_conn
        with biz_conn.open() as c:
            online = c.get_all_online_devices()
        online_list = [{"connection_id": d.connection_id, "device_id": d.device_id,
                        "terminal_type": d.attributes.get("terminal_type"),
                        "product_name": d.attributes.get("product_name")} for d in online]
    except Exception:
        online_list = []
    return JsonResponse({"devices": online_list})

@csrf_exempt
def api_trigger_sync(request: HttpRequest):
    if not _require_api_key(request):
        return JsonResponse({"error": "Unauthorized"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    data = json.loads(request.body)
    host = data.get("host")
    targets = data.get("targets", [])
    mode = data.get("mode", "merge")

    from .biz.sync_users_biz import run_sync, run_sync_bidirectional
    if mode == "bidirectional":
        log = run_sync_bidirectional(targets)
    else:
        log = run_sync(host, targets, mirror=(mode == "mirror"))
    return JsonResponse({"log": log})


# ─── API Key Management UI ────────────────────────────────────────────────────

def api_key_list(request: HttpRequest):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            models.APIKey.objects.create(name=name)
        return HttpResponseRedirect(reverse("api_key_list"))
    keys = models.APIKey.objects.all()
    return HttpResponse(loader.get_template("api_key_list.html").render({"keys": keys}, request))

def api_key_toggle(request: HttpRequest, key_id: int):
    key = get_object_or_404(models.APIKey, pk=key_id)
    key.is_active = not key.is_active
    key.save()
    return HttpResponseRedirect(reverse("api_key_list"))

def api_key_delete(request: HttpRequest, key_id: int):
    key = get_object_or_404(models.APIKey, pk=key_id)
    if request.method == "POST":
        key.delete()
    return HttpResponseRedirect(reverse("api_key_list"))


# ─── Interlock Management UI ──────────────────────────────────────────────────

def interlock_status(request: HttpRequest):
    states = models.InterlockState.objects.all().order_by("-punch_time")[:100]
    devices_qs = models.DeviceRegistry.objects.all()
    return HttpResponse(loader.get_template("interlock_status.html").render(
        {"states": states, "devices": devices_qs}, request))

def interlock_toggle_device(request: HttpRequest, device_id: int):
    dev = get_object_or_404(models.DeviceRegistry, pk=device_id)
    dev.interlock_enabled = not dev.interlock_enabled
    dev.save()
    return HttpResponseRedirect(reverse("interlock_status"))
