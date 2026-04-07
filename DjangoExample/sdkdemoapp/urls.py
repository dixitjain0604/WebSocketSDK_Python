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
]
