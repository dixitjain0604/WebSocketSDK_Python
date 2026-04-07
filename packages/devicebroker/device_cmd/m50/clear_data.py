from xml.etree import ElementTree

from .. import messages

class ClearAllDataRequest(messages.GenericRequest):
    def __init__(self):
        super().__init__("EmptyAllData")

class ClearUserDataRequest(messages.GenericRequest):
    def __init__(self):
        super().__init__("EmptyUserEnrollmentData")

class TakeOffManagerRequest(messages.GenericRequest):
    def __init__(self):
        super().__init__("TakeOffManager")

class ClearAttendanceLogRequest(messages.GenericRequest):
    def __init__(self):
        super().__init__("EmptyTimeLog")

class ClearManagementLogRequest(messages.GenericRequest):
    def __init__(self):
        super().__init__("EmptyManageLog")
