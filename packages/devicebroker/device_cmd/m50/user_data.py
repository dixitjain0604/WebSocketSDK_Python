from dataclasses import dataclass
import datetime
from enum import Enum
from typing import Final, List, Optional, Tuple
from xml.etree import ElementTree

from .. import messages
from . import device_limits

USER_MESSAGE_LEN : Final[int] = 100

class UserPrivilege(Enum):
    STANDARD_USER   = 1
    MANAGER         = 2
    ADMINISTRATOR   = 3

class UserFaceInfo:
    enrolled        : bool              = False
    data            : Optional[bytes]   = None

class UserFingerprintInfo:
    enrolled        : bool              = False
    duress          : bool              = False
    data            : Optional[bytes]   = None

class UserInfo:
    user_id         : int                       = 0
    name            : str                       = ""
    privilege       : UserPrivilege             = UserPrivilege.STANDARD_USER
    enabled         : bool                      = False
    department      : int                       = 0
    timesets        : List[int]                 = [-1] * 5
    period          : Optional[Tuple[datetime.date, datetime.date]] = None
    card            : Optional[int]             = None
    qr              : Optional[int]             = None
    password        : Optional[str]             = None
    face            : UserFaceInfo              = UserFaceInfo()
    fingerprints    : List[UserFingerprintInfo] = [UserFingerprintInfo() for _ in range(0, device_limits.MAX_FINGERS_PER_USER)]

def make_privilege_node(tag : str, value : UserPrivilege):
    match value:
        case UserPrivilege.ADMINISTRATOR:
            priv_str = "Administrator"
        case UserPrivilege.MANAGER:
            priv_str = "Manager"
        case UserPrivilege.STANDARD_USER | _:
            priv_str = "User"
    return messages.make_text_node(tag, priv_str)

def parse_base64_encoded_uint(doc : ElementTree.Element, tag : str) -> Optional[int]:
    bin_data = messages.parse_base64(doc, tag)
    if len(bin_data) == 0:
        return None
    else:
        value = 0
        for i, x in enumerate(bin_data):
            value |= x << (i * 8)
        return value

class GetUserDataResponse(messages.GenericResponse):
    user : Optional[UserInfo]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        if not self.has_succeeded():
            self.user = None
            return

        self.user = UserInfo()
        self.user.user_id       = messages.parse_int(doc, "UserID")
        self.user.name          = messages.parse_base64_string(doc, "Name")

        match messages.parse_str(doc, "Privilege"):
            case "Administrator":
                self.user.privilege = UserPrivilege.ADMINISTRATOR
            case "Manager":
                self.user.privilege = UserPrivilege.MANAGER
            case "User" | _:
                self.user.privilege = UserPrivilege.STANDARD_USER

        self.user.enabled       = messages.parse_bool(doc, "Enabled")
        self.user.department    = messages.parse_int(doc, "Depart")

        for i in range(0, len(self.user.timesets)):
            self.user.timesets[i] = messages.parse_int(doc, f"TimeSet{i+1}", -1)

        self.user.period = None
        if messages.parse_bool(doc, "UserPeriod_Used", False):
            temp = messages.parse_int(doc, "UserPeriod_Start")
            start_date = datetime.date(2000 + (temp >> 16), (temp >> 8) & 0xFF, (temp & 0xFF))

            temp = messages.parse_int(doc, "UserPeriod_End")
            end_date = datetime.date(2000 + (temp >> 16), (temp >> 8) & 0xFF, (temp & 0xFF))

            self.user.period = (start_date, end_date)

        self.user.card      = parse_base64_encoded_uint(doc, "Card")
        self.user.qr        = parse_base64_encoded_uint(doc, "QR")
        self.user.password  = messages.parse_str(doc, "PWD", None)

        self.user.face.enrolled = messages.parse_bool(doc, "FaceEnrolled")
        if self.user.face.enrolled:
            self.user.face.data = messages.parse_base64(doc, "FaceData")
        else:
            self.user.face.data = None

        bitmask = messages.parse_int(doc, "Fingers")
        for i in range(0, device_limits.MAX_FINGERS_PER_USER):
            fp = self.user.fingerprints[i]
            fp.enrolled = ((bitmask >> (i * 2)) & 1) != 0
            fp.duress   = fp.enrolled and ((bitmask >> (i * 2 + 1)) & 1) != 0
            fp.data     = None

class GetUserDataRequest(messages.GenericRequest):
    response_type = GetUserDataResponse

    def __init__(self, user_id : int):
        super().__init__("GetUserData")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("UserID", str(self.user_id)))
        return result

class GetNextUserDataResponse(GetUserDataResponse):
    has_more : bool

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.has_more = messages.parse_bool(doc, "More")

class GetNextUserDataRequest(messages.GenericRequest):
    response_type = GetNextUserDataResponse

    def __init__(self, user_id : int):
        super().__init__("GetNextUserDataExt")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("UserID", str(self.user_id)))
        return result

class GetFirstUserDataRequest(GetNextUserDataRequest):
    def __init__(self):
        super().__init__(0)

class SetUserDataResponse(messages.GenericResponse):
    user_id : int

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.user_id = messages.parse_int(doc, "UserID")

class SetUserDataRequest(messages.GenericRequest):
    response_type = SetUserDataResponse

    def __init__(self, user : UserInfo):
        super().__init__("SetUserData")
        self.user = user

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user.user_id))
        result.append(messages.make_text_node("Type", "Set"))

        # Encode name
        name = self.user.name
        if name is not None and name != "":
            if len(name) > device_limits.MAX_NAME_LEN//2:
                name = name[: device_limits.MAX_NAME_LEN//2]
            name = name.encode(encoding = "unicodelittleunmarked")
            name = name + (b'\x00' * (device_limits.MAX_NAME_LEN + 2 - len(name)))
            result.append(messages.make_base64_node("Name", name))

        result.append(messages.make_int_node("Depart", self.user.department))
        result.append(make_privilege_node("Privilege", self.user.privilege))
        result.append(messages.make_boolean_node("Enabled", self.user.enabled))

        for i, value in enumerate(self.user.timesets):
            if value >= 0:
                result.append(messages.make_int_node(f"TimeSet{i + 1}", value))

        period_valid = self.user.period is not None
        result.append(messages.make_boolean_node("UserPeriod_Used", period_valid))
        if period_valid:
            period_start, period_end = self.user.period
            result.append(messages.make_int_node("UserPeriod_Start", ((period_start.year - 2000) << 16) | (period_start.month << 8) | period_start.day))
            result.append(messages.make_int_node("UserPeriod_End"  , ((period_end  .year - 2000) << 16) | (period_end  .month << 8) | period_end  .day))
        else:
            result.append(messages.make_int_node("UserPeriod_Start", 0x0101))
            result.append(messages.make_int_node("UserPeriod_End"  , 0x0101))

        if self.user.card is not None:
            if self.user.card < 0 or self.user.card >= (1 << 32):
                raise ValueError("Card number should be an unsigned 4-byte integer.")

            result.append(messages.make_base64_node("Card", bytes([
                self.user.card & 0xff,
                (self.user.card >> 8) & 0xff,
                (self.user.card >> 16) & 0xff,
                (self.user.card >> 24) & 0xff])))

        if self.user.qr is not None:
            if self.user.qr < 0 or self.user.qr >= (1 << 32):
                raise ValueError("QR must be an unsigned 4-byte integer.")

            result.append(messages.make_base64_node("QR", bytes([
                self.user.qr & 0xff,
                (self.user.qr >> 8) & 0xff,
                (self.user.qr >> 16) & 0xff,
                (self.user.qr >> 24) & 0xff])))

        if self.user.password is not None:
            result.append(messages.make_text_node("PWD", self.user.password))

        return result

class DeleteUserRequest(messages.GenericRequest):
    response_type = SetUserDataResponse

    def __init__(self, user_id : int):
        super().__init__("SetUserData")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_text_node("Type", "Delete"))
        return result

class GetFaceDataResponse(messages.GenericResponse):
    user_id : int
    face    : bytes

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id = messages.parse_int(doc, "UserID")
        self.face = messages.parse_base64(doc, "FaceData")

class GetFaceDataRequest(messages.GenericRequest):
    response_type = GetFaceDataResponse

    def __init__(self, user_id : int):
        super().__init__("GetFaceData")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class SetFaceDataRequest(messages.GenericRequest):
    user_id             : int
    face_data           : Optional[bytes]
    check_duplication   : bool
    privilege           : Optional[UserPrivilege]

    def __init__(self, user_id : int, face_data : Optional[bytes], check_duplication : bool = False, privilege : Optional[UserPrivilege] = None):
        super().__init__("SetFaceData")

        self.user_id            = user_id
        self.face_data          = face_data
        self.check_duplication  = check_duplication
        self.privilege          = privilege

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        if self.face_data is not None:
            result.append(messages.make_base64_node("FaceData", self.face_data))
        if self.privilege is not None:
            result.append(make_privilege_node("Privilege", self.privilege))
        result.append(messages.make_boolean_node("DuplicationCheck", self.check_duplication))
        return result

class GetFingerprintDataResponse(messages.GenericResponse):
    user_id             : int
    finger_no           : int
    fingerprint_data    : bytes
    is_duress           : bool

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id            = messages.parse_int(doc, "UserID")
        self.finger_no          = messages.parse_int(doc, "FingerNo")
        self.fingerprint_data   = messages.parse_base64(doc, "FingerData")
        self.is_duress          = messages.parse_bool(doc, "Duress")

class GetFingerprintDataRequest(messages.GenericRequest):
    response_type       = GetFingerprintDataResponse

    def __init__(self, user_id : int, finger_no : int):
        super().__init__("GetFingerData")
        self.user_id    = user_id
        self.finger_no  = finger_no

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_int_node("FingerNo", self.finger_no))
        result.append(messages.make_int_node("FingerOnly", 1))
        return result

class SetFingerprintDataRequest(messages.GenericRequest):
    user_id             : int
    finger_no           : int
    fingerprint_data    : Optional[bytes]
    is_duress           : bool
    check_duplication   : bool
    privilege           : Optional[UserPrivilege]

    def __init__(self, user_id : int, finger_no : int, fp_data : Optional[bytes],
                 is_duress : bool = False, check_duplication : bool = False, privilege : Optional[UserPrivilege] = None):
        super().__init__("SetFingerData")

        self.user_id            = user_id
        self.finger_no          = finger_no
        self.fingerprint_data   = fp_data
        self.is_duress          = is_duress
        self.check_duplication  = check_duplication
        self.privilege          = privilege

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_int_node("FingerNo", self.finger_no))
        if self.fingerprint_data is not None:
            result.append(messages.make_base64_node("FingerData", self.fingerprint_data))
        result.append(messages.make_int_node("Duress", int(self.is_duress)))
        result.append(messages.make_int_node("DuplicationCheck", int(self.check_duplication)))
        if self.privilege is not None:
            result.append(make_privilege_node("Privilege", self.privilege))
        return result

class GetUserPasswordResponse(messages.GenericResponse):
    user_id     : int
    password    : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.password   = messages.parse_str(doc, "Password")

class GetUserPasswordRequest(messages.GenericRequest):
    response_type = GetUserPasswordResponse
    user_id     : int

    def __init__(self, user_id : int):
        super().__init__("GetUserPassword")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class GetUserCardResponse(messages.GenericResponse):
    user_id     : int
    card        : Optional[int]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.card       = parse_base64_encoded_uint(doc, "CardNo")
        if self.card == 0:
            self.card = None

class GetUserCardRequest(messages.GenericRequest):
    response_type = GetUserCardResponse
    user_id     : int

    def __init__(self, user_id : int):
        super().__init__("GetUserCardNo")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class GetUserQRResponse(messages.GenericResponse):
    user_id     : int
    qr          : Optional[int]

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.qr         = parse_base64_encoded_uint(doc, "QR")
        if self.qr == 0:
            self.qr = None

class GetUserQRRequest(messages.GenericRequest):
    response_type = GetUserQRResponse
    user_id     : int

    def __init__(self, user_id : int):
        super().__init__("GetUserQR")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class GetUserPhotoResponse(messages.GenericResponse):
    user_id     : int
    photo       : bytes

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.photo      = messages.parse_base64(doc, "PhotoData")

class GetUserPhotoRequest(messages.GenericRequest):
    response_type = GetUserPhotoResponse
    user_id     : int

    def __init__(self, user_id : int):
        super().__init__("GetUserPhoto")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class SetUserPhotoRequest(messages.GenericRequest):
    user_id : int
    photo   : Optional[bytes]

    def __init__(self, user_id : int, photo : Optional[bytes]):
        super().__init__("SetUserPhoto")

        self.user_id = user_id
        self.photo = photo

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))

        if self.photo is not None and len(self.photo) > 0:
            result.append(messages.make_int_node("PhotoSize", len(self.photo)))
            result.append(messages.make_base64_node("PhotoData", self.photo))
        else:
            result.append(messages.make_int_node("PhotoSize", 0))

        return result

class GetUserAttendOnlySettingResponse(messages.GenericResponse):
    user_id     : int
    value       : bool

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.value      = messages.parse_bool(doc, "Value")

class GetUserAttendOnlySettingRequest(messages.GenericRequest):
    response_type = GetUserAttendOnlySettingResponse

    user_id : int

    def __init__(self, user_id : int):
        super().__init__("GetUserAttendOnly")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class SetUserAttendOnlySettingRequest(messages.GenericRequest):
    user_id : int
    value   : bool

    def __init__(self, user_id : int, value : bool):
        super().__init__("SetUserAttendOnly")
        self.user_id = user_id
        self.value = value

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_boolean_node("Value", self.value))
        return result

class GetUserMessageResponse(messages.GenericResponse):
    user_id     : int
    message     : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        message = messages.parse_base64_string(doc, "UserMessage")
        if (index := message.find('\x00')) >= 0:
            message = message[: index]
        self.message    = message

class GetUserMessageRequest(messages.GenericRequest):
    response_type = GetUserMessageResponse

    user_id : int

    def __init__(self, user_id : int):
        super().__init__("GetUserMessage")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class SetUserMessageRequest(messages.GenericRequest):
    user_id : int
    message : str

    def __init__(self, user_id : int, message : str):
        super().__init__("SetUserMessage")
        self.user_id = user_id
        self.message = message

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))

        message = self.message
        if len(message) > USER_MESSAGE_LEN:
            message = message[:USER_MESSAGE_LEN]
        else:
            message = message + "\x00" * (USER_MESSAGE_LEN - len(message))
        result.append(messages.make_base64_node("UserMessage", message.encode(encoding = "unicodelittleunmarked")))
        return result


class GetUserMessageColorResponse(messages.GenericResponse):
    color : int
    bk_color : int

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.color       = messages.parse_int(doc, "MessageColor", default = 0, base = 16) & 0xFFFFFF
        self.bk_color    = messages.parse_int(doc, "MessageBkColor", default = 0, base = 16) & 0xFFFFFF

class GetUserMessageColorRequest(messages.GenericRequest):
    response_type = GetUserMessageColorResponse

    def __init__(self):
        super().__init__("GetUserMessageColor")

class SetUserMessageColorRequest(messages.GenericRequest):
    color : int
    bk_color : int

    def __init__(self, color : int, bk_color : int):
        super().__init__("SetUserMessageColor")
        self.color = color
        self.bk_color = bk_color

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_text_node("MessageColor", f"{self.color:06X}"))
        result.append(messages.make_text_node("MessageBkColor", f"{self.bk_color:06X}"))
        return result

class GetUserBalanceTimeResponse(messages.GenericResponse):
    user_id     : int
    balance_time_in_minutes : int

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.balance_time_in_minutes = messages.parse_int(doc, "BalanceTimeInMinues")

class GetUserBalanceTimeRequest(messages.GenericRequest):
    response_type = GetUserBalanceTimeResponse

    user_id : int

    def __init__(self, user_id : int):
        super().__init__("GetUserBalanceTime")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class SetUserBalanceTimeRequest(messages.GenericRequest):
    user_id : int
    balance_time_in_minutes : int

    def __init__(self, user_id : int, balance_time_in_minutes : int):
        super().__init__("SetUserBalanceTime")
        self.user_id = user_id
        self.balance_time_in_minutes = balance_time_in_minutes

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_int_node("BalanceTimeInMinues", self.balance_time_in_minutes))
        return result

class GetUserHolidaysResponse(messages.GenericResponse):
    user_id     : int
    holidays_in_10 : int

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.user_id    = messages.parse_int(doc, "UserID")
        self.holidays_in_10 = messages.parse_int(doc, "HolidaysInDays10")

class GetUserHolidaysRequest(messages.GenericRequest):
    response_type = GetUserHolidaysResponse

    user_id : int

    def __init__(self, user_id : int):
        super().__init__("GetUserHolidays")
        self.user_id = user_id

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        return result

class SetUserHolidaysRequest(messages.GenericRequest):
    user_id : int
    holidays_in_10 : int

    def __init__(self, user_id : int, holidays_in_10 : int):
        super().__init__("SetUserHolidays")
        self.user_id = user_id
        self.holidays_in_10 = holidays_in_10

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_int_node("HolidaysInDays10", self.holidays_in_10))
        return result


class BeginRemoteEnrollResult(Enum):
    Success                     = 0
    InvalidBackup               = 1
    EnrollNumberError           = 2
    DatabaseFull                = 3
    FaceAlreadyEnrolled         = 4
    FPAllEnrolled               = 5
    FPAlreadyEnrolled           = 6
    InvalidFingerNumber         = 7
    CardAlreadyEnrolled         = 8
    QRAlreadyEnrolled           = 9
    MenuProcessing              = 10
    RemoteEnrollAlreadyStarted  = 11
    Unknown                     = 12

class BeginRemoteEnrollResponse:
    result_code : BeginRemoteEnrollResult

    def parse(self, doc : ElementTree.Element):
        val = messages.parse_str(doc, "ResultCode")
        try:
            self.result_code = BeginRemoteEnrollResult[val]
        except:
            self.result_code = BeginRemoteEnrollResult.Unknown

    def has_succeeded(self) -> bool:
        return self.result_code == BeginRemoteEnrollResult.Success

class RemoteEnrollType(Enum):
    Face    = 1
    FP      = 2
    Card    = 3
    QR      = 4

class BeginRemoteEnrollRequest(messages.GenericRequest):
    response_type = BeginRemoteEnrollResponse

    user_id     : int
    enroll_type : RemoteEnrollType
    fp_no       : Optional[int]

    def __init__(self, user_id : int, enroll_type : RemoteEnrollType, fp_no : Optional[int] = None):
        super().__init__("RemoteEnroll")
        self.user_id        = user_id
        self.enroll_type    = enroll_type
        self.fp_no          = fp_no

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_text_node("Backup", "RemoteEnroll" + self.enroll_type.name))
        if self.fp_no is not None:
            result.append(messages.make_text_node("FingerNo", self.fp_no))
        return result

class ExitRemoteEnrollResult(Enum):
    SuccessExitRemoteEnroll = 0
    NotStartedRemoteEnroll  = 1
    Unknown                 = 2

class ExitRemoteEnrollResponse:
    result_code : ExitRemoteEnrollResult

    def parse(self, doc : ElementTree.Element):
        val = messages.parse_str(doc, "ResultCode")
        try:
            self.result_code = ExitRemoteEnrollResult[val]
        except:
            self.result_code = ExitRemoteEnrollResult.Unknown

    def has_succeeded(self) -> bool:
        return self.result_code == ExitRemoteEnrollResult.SuccessExitRemoteEnroll
        
class ExitRemoteEnrollRequest(messages.GenericRequest):
    response_type = ExitRemoteEnrollResponse

    def __init__(self):
        super().__init__("ExitRemoteEnroll")

class RemoteEnrollStatus(Enum):
    RemoteEnrollAlreadyStarted  = 0
    NotStartedRemoteEnroll      = 1
    Unknown                     = 2

class QueryRemoteEnrollStatusResponse:
    result_code : RemoteEnrollStatus

    def parse(self, doc : ElementTree.Element):
        val = messages.parse_str(doc, "ResultCode")
        try:
            self.result_code = RemoteEnrollStatus[val]
        except:
            self.result_code = RemoteEnrollStatus.Unknown

    def has_succeeded(self) -> bool:
        return self.result_code != RemoteEnrollStatus.Unknown

class QueryRemoteEnrollStatusRequest(messages.GenericRequest):
    response_type = QueryRemoteEnrollStatusResponse

    def __init__(self):
        super().__init__("QueryRemoteEnrollStatus")

class EnrollFaceByPhotoRequest(messages.GenericRequest):
    response_type = messages.GenericResponse
    user_id     : int
    photo_data  : bytes

    def __init__(self, user_id : int, photo_data : bytes):
        super().__init__("EnrollFaceByPhoto")
        self.user_id    = user_id
        self.photo_data = photo_data

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("UserID", self.user_id))
        result.append(messages.make_int_node("PhotoSize", len(self.photo_data)))
        result.append(messages.make_base64_node("PhotoData", self.photo_data))
        return result
