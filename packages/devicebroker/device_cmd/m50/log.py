import datetime
from typing import Optional
from xml.etree import ElementTree

from .. import messages

class TimeLog:
    log_id              : int
    timezone_offset     : Optional[int]
    time                : datetime.datetime
    user_id             : Optional[int]
    attend_status       : str
    action              : str
    jobcode             : int
    photo               : Optional[bytes]
    body_temperature    : Optional[float]
    attend_only         : bool
    expired             : bool
    latitude            : Optional[str]
    longitude           : Optional[str]

class GetGlogResponse(messages.GenericResponse):
    log : TimeLog

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.log = TimeLog()
        self.log.log_id             = messages.parse_int(doc, "LogID")
        self.log.timezone_offset    = messages.parse_int(doc, "UtcTimezoneMinutes", None)
        self.log.time               = messages.parse_datetime(doc, "Time")
        self.log.user_id            = messages.parse_int(doc, "UserID", None)
        self.log.attend_status      = messages.parse_str(doc, "AttendStat")
        self.log.action             = messages.parse_str(doc, "Action")
        self.log.jobcode            = messages.parse_int(doc, "JobCode")
        
        if messages.parse_bool(doc, "Photo"):
            self.log.photo = messages.parse_base64(doc, "LogImage")
        else:
            self.log.photo = None

        if (body_temp := messages.parse_int(doc, "BodyTemperature100", None)) is not None:
            self.log.body_temperature = body_temp / 100
        else:
            self.log.body_temperature = None

        self.log.attend_only        = messages.parse_bool(doc, "AttendOnly")
        self.log.expired            = messages.parse_bool(doc, "Expired")
        self.log.latitude           = messages.parse_str(doc, "Latitude", None)
        self.log.longitude          = messages.parse_str(doc, "Longitude", None)

class GetFirstGlogRequest(messages.GenericRequest):
    response_type = GetGlogResponse

    user_id     : Optional[int]
    start_time  : Optional[datetime.datetime]
    end_time    : Optional[datetime.datetime]

    def __init__(self, user_id : Optional[int] = None, start_time : Optional[datetime.datetime] = None, end_time : Optional[datetime.datetime] = None):
        super().__init__("GetFirstGlog")

        self.user_id    = user_id
        self.start_time = start_time
        self.end_time   = end_time

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("BeginLogPos", 0))
        if self.user_id is not None:
            result.append(messages.make_int_node("UserID", self.user_id))
        if self.start_time is not None:
            result.append(messages.make_datetime_node("StartTime", self.start_time))
        if self.end_time is not None:
            result.append(messages.make_datetime_node("EndTime", self.end_time))
        return result

class GetNextGlogRequest(messages.GenericRequest):
    response_type = GetGlogResponse
    pos_begin : int

    def __init__(self, pos_begin : int):
        super().__init__("GetNextGlog")
        self.pos_begin = pos_begin

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("BeginLogPos", self.pos_begin))
        return result

class GetGlogPosInfoResponse(messages.GenericResponse):
    log_count   : int
    max_count   : int
    start_pos   : int

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)
        self.log_count  = messages.parse_int(doc, "LogCount")
        self.max_count  = messages.parse_int(doc, "MaxCount")
        self.start_pos  = messages.parse_int(doc, "StartPos")

class GetGlogPosInfoRequest(messages.GenericRequest):
    response_type = GetGlogPosInfoResponse

    def __init__(self):
        super().__init__("GetGlogPosInfo")

class DeleteGlogWithPosRequest(messages.GenericRequest):
    end_pos : int

    def __init__(self, end_pos : int):
        super().__init__("DeleteGlogWithPos")
        self.end_pos = end_pos

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_int_node("EndPos", self.end_pos))
        return result
