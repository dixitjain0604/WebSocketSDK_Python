from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # Device control
    path("online_devices", views.online_devices, name="online_devices"),
    path("control_device/<int:connection_id>", views.control_device, name = "control_device"),

    path("control_device/<int:connection_id>/manage_users", views.manage_users, name = "manage_users"),
    path("control_device/<int:connection_id>/manage_face_data", views.manage_face_data, name = "manage_face_data"),
    path("control_device/<int:connection_id>/manage_fingerprint", views.manage_fingerprint, name = "manage_fingerprint"),
    path("control_device/<int:connection_id>/view_user_misc_cred", views.view_user_misc_cred, name = "view_user_misc_cred"),
    path("control_device/<int:connection_id>/manage_user_photo", views.manage_user_photo, name = "manage_user_photo"),
    path("control_device/<int:connection_id>/manage_user_attend_only", views.manage_user_attend_only, name = "manage_user_attend_only"),
    path("control_device/<int:connection_id>/remote_enroll", views.remote_enroll, name = "remote_enroll"),
    path("control_device/<int:connection_id>/enroll_face_by_photo", views.enroll_face_by_photo, name = "enroll_face_by_photo"),
    path("control_device/<int:connection_id>/manage_user_message", views.manage_user_message, name = "manage_user_message"),
    path("control_device/<int:connection_id>/manage_user_german", views.manage_user_german, name = "manage_user_german"),

    path("control_device/<int:connection_id>/device_config_status", views.device_config_status, name = "device_config_status"),
    path("control_device/<int:connection_id>/manage_ethernet_setting", views.manage_ethernet_setting, name = "manage_ethernet_setting"),
    path("control_device/<int:connection_id>/manage_wifi_setting", views.manage_wifi_setting, name = "manage_wifi_setting"),
    path("control_device/<int:connection_id>/manage_ntp_setting", views.manage_ntp_setting, name = "manage_ntp_setting"),
    path("control_device/<int:connection_id>/manage_webserverurl_setting", views.manage_webserverurl_setting, name = "manage_webserverurl_setting"),
    path("control_device/<int:connection_id>/tr_icon_setting", views.tr_icon_setting, name = "tr_icon_setting"),

    path("control_device/<int:connection_id>/attendance_settings", views.attendance_settings, name = "attendance_settings"),
    path("control_device/<int:connection_id>/manage_departments", views.manage_departments, name = "manage_departments"),
    path("control_device/<int:connection_id>/manage_proxy_departments", views.manage_proxy_departments, name = "manage_proxy_departments"),
    path("control_device/<int:connection_id>/manage_bell_settings", views.manage_bell_settings, name = "manage_bell_settings"),
    path("control_device/<int:connection_id>/manage_auto_attendance_settings", views.manage_auto_attendance_settings, name = "manage_auto_attendance_settings"),

    path("control_device/<int:connection_id>/manage_access_timezone_settings", views.manage_access_timezone_settings, name = "manage_access_timezone_settings"),
    path("control_device/<int:connection_id>/manage_lock_control", views.manage_lock_control, name = "manage_lock_control"),

    path("control_device/<int:connection_id>/view_device_attend_logs", views.view_device_attend_logs, name = "view_device_attend_logs"),
    path("control_device/<int:connection_id>/clear_data", views.clear_data, name = "clear_data"),

    path("control_device/<int:connection_id>/firmware_version", views.firmware_version, name = "firmware_version"),
    path("control_device/<int:connection_id>/write_firmware", views.write_firmware, name = "write_firmware"),

    path("control_device/<int:connection_id>/center_message_setting", views.center_message_setting, name = "center_message_setting"),
    path("control_device/<int:connection_id>/video_streaming_setting", views.video_streaming_setting, name = "video_streaming_setting"),

    # Manage firmware
    path("manage_firmware", views.manage_firmware, name="manage_firmware"),
    path("upload_firmware", views.upload_firmware, name="upload_firmware"),
    path("get_firmware/<str:firmware_name>", views.get_firmware, name="get_firmware"),
    path("delete_firmware/<str:firmware_name>", views.delete_firmware, name="delete_firmware"),

    # Search logs
    path("search_attend_logs", views.search_attend_logs, name = "search_attend_logs"),
    path("search_attend_logs/<str:device_id>", views.search_attend_logs, name = "search_attend_logs"),
    path("attend_log/<int:id>", views.attend_log_details, name = "attend_log_details"),
    path("search_management_logs", views.search_management_logs, name = "search_management_logs"),
    path("search_management_logs/<str:device_id>", views.search_management_logs, name = "search_management_logs"),

    # OEM branding settings
    path("oem_settings", views.oem_settings, name="oem_settings"),

    # These URLs are invoked from API server.
    path("device/check_registration", views.check_device_registration, name = "check_device_registration"),
    path("device/check_login", views.check_device_login, name = "check_device_login"),
    path("device/upload_log", views.upload_device_log, name = "upload_device_log"),
    path("device/connection_event", views.connection_event, name = "connection_event"),

    # Zone management
    path("zones/", views.zone_list, name="zone_list"),
    path("zones/create/", views.zone_create, name="zone_create"),
    path("zones/<int:zone_id>/edit/", views.zone_edit, name="zone_edit"),
    path("zones/<int:zone_id>/delete/", views.zone_delete, name="zone_delete"),
    path("zones/<int:zone_id>/sync/", views.zone_sync_view, name="zone_sync"),

    # Device registry
    path("device_registry/", views.device_registry_list, name="device_registry_list"),
    path("device_registry/create/", views.device_registry_create, name="device_registry_create"),
    path("device_registry/<int:device_id>/edit/", views.device_registry_edit, name="device_registry_edit"),
    path("device_registry/<int:device_id>/delete/", views.device_registry_delete, name="device_registry_delete"),
    path("device_connection_logs/", views.device_connection_logs, name="device_connection_logs"),

    # Per-device: restart & bulk log download
    path("control_device/<int:connection_id>/restart/", views.restart_device, name="restart_device"),
    path("control_device/<int:connection_id>/bulk_download_logs/", views.bulk_download_from_device, name="bulk_download_logs"),

    # Sync users (all devices or zone-wise)
    path("sync_users/", views.sync_users_view, name="sync_users"),

    # Employee management (with auto-push)
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/create/", views.employee_create, name="employee_create"),
    path("employees/<int:employee_id>/edit/", views.employee_edit, name="employee_edit"),
    path("employees/<int:employee_id>/delete/", views.employee_delete, name="employee_delete"),
    path("employees/<int:employee_id>/toggle/", views.employee_enable_disable, name="employee_enable_disable"),

    # Log export
    path("logs/download_csv/", views.download_logs_csv, name="download_logs_csv"),

    # Interlock
    path("interlock/", views.interlock_status, name="interlock_status"),
    path("interlock/<int:device_id>/toggle/", views.interlock_toggle_device, name="interlock_toggle_device"),

    # API key management
    path("api_keys/", views.api_key_list, name="api_key_list"),
    path("api_keys/<int:key_id>/toggle/", views.api_key_toggle, name="api_key_toggle"),
    path("api_keys/<int:key_id>/delete/", views.api_key_delete, name="api_key_delete"),

    # External REST API
    path("api/v1/employees/", views.api_employees, name="api_employees"),
    path("api/v1/employees/<int:employee_id>/", views.api_employee_detail, name="api_employee_detail"),
    path("api/v1/logs/", views.api_logs, name="api_logs"),
    path("api/v1/devices/", views.api_devices, name="api_devices"),
    path("api/v1/sync/", views.api_trigger_sync, name="api_trigger_sync"),
]
