import base64
from dataclasses import dataclass
from typing import List, Tuple
from django import forms
from django.core.exceptions import ValidationError
from django.forms.fields import Field
from django.forms.widgets import Input

from devicebroker.device_cmd.m50.access_control import LockControlMode
from devicebroker.device_cmd.m50.attendance_setting import AttendStatus
from devicebroker.device_cmd.m50.user_data import RemoteEnrollType, UserPrivilege
from devicebroker.device_cmd.m50.device_control import DeviceStatusParamType
from devicebroker.device_cmd.m50.device_info import DeviceInfoParamType
from devicebroker.device_cmd.m50.misc import RtspResolution, RtspBitrate

PRIVILEGE_CHOICES = (
    (UserPrivilege.STANDARD_USER.value, "User"),
    (UserPrivilege.MANAGER.value      , "Manager"),
    (UserPrivilege.ADMINISTRATOR.value, "Administrator")
)

BOOLEAN_CHOICES = (
    ("0", "No" ),
    ("1", "Yes")
)

TRISTATE_CHOICES = (
    ("" , ""   ),
    ("0", "No" ),
    ("1", "Yes")
)

FINGER_NO_CHOICES = (
    ("0", "0"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
)

BELL_VALID_CHOICES = (
    ("0", "No Use"),
    ("1", "Use"),
)

BELL_TYPE_CHOICES = (
    ("0", "1"),
    ("1", "2"),
    ("2", "3"),
    ("3", "4"),
    ("4", "5"),
)

class BinaryInput(Input):
    input_type = "text"
    template_name = "binary_input.html"

class BinaryField(Field):
    widget = BinaryInput

    def prepare_value(self, value):
        if isinstance(value, bytes):
            return base64.b64encode(value).decode('utf-8')
        return value

    def to_python(self, value):
        if value is None or value == "":
            return None

        if isinstance(value, str):
            try:
                value = base64.b64decode(value)
            except:
                raise ValidationError(self.error_messages["invalid"], code="invalid")

        return value

class PictureInput(Input):
    input_type = "text"
    template_name = "picture_input.html"

class PictureField(Field):
    widget = PictureInput

    def prepare_value(self, value):
        if isinstance(value, bytes):
            return base64.b64encode(value).decode('utf-8')
        return value

    def to_python(self, value):
        if value is None or value == "":
            return None

        if isinstance(value, str):
            try:
                value = base64.b64decode(value)
            except:
                raise ValidationError(self.error_messages["invalid"], code="invalid")

        return value

class ReadonlyField(forms.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, disabled = True)

    def bound_data(self, data, initial):
        return data

    def _clean_bound_field(self, bf):
        value = bf.data
        return self.clean(value)

class DynamicChoiceField(forms.ChoiceField):
    def valid_value(self, value):
        return True

class UserManagementForm(forms.Form):
    template_name = "form_snippet.html"

    user_id             = forms.IntegerField(min_value = 1, required = False)
    name                = forms.CharField(required = False)
    privilege           = forms.ChoiceField(choices = PRIVILEGE_CHOICES, required = False)
    enabled             = forms.ChoiceField(choices = BOOLEAN_CHOICES, required = False)
    department          = forms.IntegerField(min_value = 0, required = False)
    timeset_1           = forms.IntegerField(min_value = -1, required = False)
    timeset_2           = forms.IntegerField(min_value = -1, required = False)
    timeset_3           = forms.IntegerField(min_value = -1, required = False)
    timeset_4           = forms.IntegerField(min_value = -1, required = False)
    timeset_5           = forms.IntegerField(min_value = -1, required = False)
    userperiod_start    = forms.DateField(required = False)
    userperiod_end      = forms.DateField(required = False)
    card                = forms.IntegerField(min_value = 0, required = False)
    qr                  = forms.IntegerField(min_value = 0, required = False)
    password            = forms.CharField(required = False)
    face_enrolled       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_1       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_2       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_3       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_4       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_5       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_6       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_7       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_8       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_9       = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)
    fingerprint_10      = forms.ChoiceField(choices = TRISTATE_CHOICES, disabled = True, required = False)

class FaceDataManagementForm(forms.Form):
    template_name = "form_snippet.html"

    user_id             = forms.IntegerField(min_value = 1, required = False)
    face_data           = BinaryField(required = False)
    check_duplication   = forms.ChoiceField(choices = BOOLEAN_CHOICES, required = False)

class FingerprintManagementForm(forms.Form):
    template_name = "form_snippet.html"

    user_id             = forms.IntegerField(min_value = 1, required = False)
    finger_no           = forms.ChoiceField(choices = FINGER_NO_CHOICES, required = False)
    fingerprint_data    = BinaryField(required = False)
    duress              = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)
    check_duplication   = forms.ChoiceField(choices = BOOLEAN_CHOICES, required = False)

class UserMiscCredForm(forms.Form):
    template_name = "form_snippet.html"

    user_id             = forms.IntegerField(min_value = 1, required = False)

class UserPhotoManagementForm(forms.Form):
    template_name = "form_snippet.html"

    user_id             = forms.IntegerField(min_value = 1, required = False)
    photo               = PictureField(required = False)

class UserAttendOnlyManagementForm(forms.Form):
    template_name = "form_snippet.html"

    user_id             = forms.IntegerField(min_value = 1, required = False)
    attend_only         = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)

class DeviceConfigAndStatusForm(forms.Form):
    template_name = "form_snippet.html"

    device_status_param         = forms.ChoiceField(choices = [("", "")] + [(x.name, x.name) for x in DeviceStatusParamType], required = False)
    device_info_param           = forms.ChoiceField(choices = [("", "")] + [(x.name, x.name) for x in DeviceInfoParamType], required = False)
    device_info_value           = forms.IntegerField(label = "Value", required = False)
    device_info_value_choice    = DynamicChoiceField(label = "Value", required = False)

class NtpServerSettingForm(forms.Form):
    template_name = "form_snippet.html"

    server_address      = forms.CharField(required = False, label = "Server Address (e.g. 'time.nist.gov')")
    timezone            = forms.CharField(required = False, label = "Time zone (e.g. '+05:00', '-02:30')")
    sync_interval       = forms.IntegerField(min_value = 0, required = False, label = "Sync interval (minutes)")

class WebServerUrlSettingForm(forms.Form):
    template_name = "form_snippet.html"

    web_server_url      = forms.CharField(required = False)

class EthernetSettingForm(forms.Form):
    template_name = "form_snippet.html"

    use_dhcp                = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)
    ip_address              = forms.CharField(required = False)
    subnet_mask             = forms.CharField(required = False)
    gateway                 = forms.CharField(required = False)
    port                    = forms.IntegerField(min_value = 0, required = False)
    mac_address             = ReadonlyField(required = False)
    ip_address_from_dhcp    = ReadonlyField(required = False)
    subnet_mask_from_dhcp   = ReadonlyField(required = False)
    gateway_from_dhcp       = ReadonlyField(required = False)

class WifiSettingForm(forms.Form):
    template_name = "form_snippet.html"

    use_wifi                = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)
    ssid                    = forms.CharField(required = False)
    key                     = forms.CharField(required = False)
    use_dhcp                = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)
    ip_address              = forms.CharField(required = False)
    subnet_mask             = forms.CharField(required = False)
    gateway                 = forms.CharField(required = False)
    port                    = forms.IntegerField(min_value = 0, required = False)
    ip_address_from_dhcp    = ReadonlyField(required = False)
    subnet_mask_from_dhcp   = ReadonlyField(required = False)
    gateway_from_dhcp       = ReadonlyField(required = False)

class SetTrIconForm(forms.Form):
    template_name = "form_snippet.html"

    icon_no     = forms.IntegerField(min_value = 1, max_value= 8, required = False)
    icon_status = forms.IntegerField(min_value = 0, max_value= 2, required = False)
    icon_data   = PictureField(required = False, label = "Icon (png)")
    delete      = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)

class DepartmentSettingsForm(forms.Form):
    template_name = "form_snippet.html"

    depart_no               = forms.IntegerField()
    depart_name             = forms.CharField(required = False)

class ProxyDepartmentSettingsForm(forms.Form):
    template_name = "form_snippet.html"

    depart_no               = forms.IntegerField()
    depart_name             = forms.CharField(required = False)

@dataclass
class BellRow:
    index       : int
    valid       : forms.BoundField
    bell_type   : forms.BoundField
    hour        : forms.BoundField
    minute      : forms.BoundField

class BellSettingsForm(forms.Form):
    template_name = "form_bell_settings.html"
    num_rows = 24
    ring_times = forms.IntegerField(required = False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for i in range(0, self.num_rows):
            self.fields[f"valid_{i+1}" ] = forms.ChoiceField(choices = BELL_VALID_CHOICES, required = False)
            self.fields[f"type_{i+1}"  ] = forms.ChoiceField(choices = BELL_TYPE_CHOICES, required = False)
            self.fields[f"hour_{i+1}"  ] = forms.IntegerField(min_value = 0, max_value = 23, required = False)
            self.fields[f"minute_{i+1}"] = forms.IntegerField(min_value = 0, max_value = 59, required = False)

    def rows(self) -> List[BellRow]:
        return [BellRow(
            index       = i + 1,
            valid       = self[f"valid_{i+1}" ],
            bell_type   = self[f"type_{i+1}"  ],
            hour        = self[f"hour_{i+1}"  ],
            minute      = self[f"minute_{i+1}"],
            ) for i in range(0, self.num_rows)]

@dataclass
class AutoAttendanceRow:
    index   : int
    start   : forms.BoundField
    end     : forms.BoundField
    status  : forms.BoundField

class AutoAttendanceSettingsForm(forms.Form):
    template_name = "form_auto_attendance.html"
    num_rows = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for i in range(0, self.num_rows):
            self.fields[f"start_{i+1}"  ] = forms.CharField(required = False)
            self.fields[f"end_{i+1}"    ] = forms.CharField(required = False)
            self.fields[f"status_{i+1}" ] = forms.ChoiceField(choices = [(x.name, x.name) for x in AttendStatus], required = False)

    def rows(self) -> List[AutoAttendanceRow]:
        return [AutoAttendanceRow(
            index   = i + 1,
            start   = self[f"start_{i+1}" ],
            end     = self[f"end_{i+1}"   ],
            status  = self[f"status_{i+1}"],
            ) for i in range(0, self.num_rows)]

@dataclass
class AccessTimezoneRow:
    weekday : str
    start   : forms.BoundField
    end     : forms.BoundField

class AccessTimezoneSettingsForm(forms.Form):
    template_name = "form_access_timezone.html"
    num_rows = 7

    timezone_no = forms.IntegerField(min_value = 0, required = False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for i in range(0, self.num_rows):
            self.fields[f"start_{i+1}"] = forms.CharField(required = False)
            self.fields[f"end_{i+1}"  ] = forms.CharField(required = False)

    def rows(self) -> List[AccessTimezoneRow]:
        return [AccessTimezoneRow(
            weekday = weekday,
            start   = self[f"start_{i+1}"],
            end     = self[f"end_{i+1}"],
            ) for i, weekday in enumerate([
                "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
            ])]

class LockControlForm(forms.Form):
    template_name = "form_snippet.html"

    mode = forms.ChoiceField(choices = [("", "")] + [(x.name, x.name) for x in LockControlMode], required = False)

class AttendLogsForm(forms.Form):
    template_name = "form_snippet.html"

    user_id     = forms.IntegerField(min_value = 1, required = False)
    start_time  = forms.DateTimeField(required = False)
    end_time    = forms.DateTimeField(required = False)
    next_log_id = forms.IntegerField(required = False)

class RemoteEnrollForm(forms.Form):
    template_name = "form_snippet.html"

    user_id     = forms.IntegerField(min_value = 1, required = False)
    enroll_type = forms.ChoiceField(choices = [(x.name, x.name) for x in RemoteEnrollType], required = False)
    finger_no   = forms.ChoiceField(choices = FINGER_NO_CHOICES, required = False)

class EnrollFaceByPhotoForm(forms.Form):
    template_name = "form_snippet.html"

    user_id     = forms.IntegerField(min_value = 1, required = False)
    photo       = PictureField(required = False, label = "Photo (jpg)")

class ClearDataForm(forms.Form):
    template_name = "form_snippet.html"

class UploadFirmwareForm(forms.Form):
    template_name = "form_snippet.html"

    firmware_name   = forms.CharField(required = False)
    firmware_data   = BinaryField(required = False)

class WriteFirmwareForm(forms.Form):
    template_name = "form_snippet.html"

    def __init__(self, *args, name_choices : List[str], public_url : str, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["firmware_name"]    = forms.ChoiceField(choices = name_choices, required = False)
        self.fields["public_url"]       = forms.CharField(required = False, initial = public_url, label = "Public URL")

class AttendLogFilterForm(forms.Form):
    template_name = "form_snippet.html"

    def __init__(self, *args, show_device_id : bool, **kwargs):
        super().__init__(*args, **kwargs)

        if show_device_id:
            self.fields["device_id"] = forms.CharField(required = False)
        self.fields["user_id"     ] = forms.IntegerField(min_value = 1, required = False)
        self.fields["start_time"  ] = forms.DateTimeField(required = False)
        self.fields["end_time"    ] = forms.DateTimeField(required = False)

class ManagementLogFilterForm(forms.Form):
    template_name = "form_snippet.html"

    def __init__(self, *args, show_device_id : bool, **kwargs):
        super().__init__(*args, **kwargs)

        if show_device_id:
            self.fields["device_id"] = forms.CharField(required = False)
        self.fields["start_time"  ] = forms.DateTimeField(required = False)
        self.fields["end_time"    ] = forms.DateTimeField(required = False)

class CenterMessageSettingForm(forms.Form):
    template_name = "form_snippet.html"

    message         = forms.CharField(required = False)
    color           = forms.CharField(required = False)
    border_color    = forms.CharField(required = False)
    disable_verify  = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)

def remove_leading_underscore(x : str) -> str:
    if x.startswith("_"):
        return x[1:]
    else:
        return x

class VideoStreamingSettingForm(forms.Form):
    template_name = "form_snippet.html"

    enabled         = forms.ChoiceField(choices = TRISTATE_CHOICES, required = False)
    resolution      = forms.ChoiceField(choices = [("", "")] + [(str(x.value), remove_leading_underscore(x.name)) for x in RtspResolution], required = False)
    bitrate         = forms.ChoiceField(choices = [("", "")] + [(str(x.value), remove_leading_underscore(x.name)) for x in RtspBitrate], required = False, label = "Bitrate (Mbps)")

class UserMessageManagementForm(forms.Form):
    template_name = "form_snippet.html"

    user_id         = forms.IntegerField(min_value = 1, required = False)
    message         = forms.CharField(required = False, widget=forms.Textarea(attrs={'rows': 4}))
    color           = forms.CharField(required = False)
    bk_color        = forms.CharField(required = False)

class UserManagementGermanForm(forms.Form):
    template_name = "form_snippet.html"

    user_id         = forms.IntegerField(min_value = 1, required = False)
    message         = forms.CharField(required = False, widget=forms.Textarea(attrs={'rows': 4}))
    balance_hour    = forms.IntegerField(min_value = 0, max_value = 1092, required = False)
    balance_minute  = forms.IntegerField(min_value = 0, max_value = 59, required = False)
    holidays        = forms.CharField(required = False)
