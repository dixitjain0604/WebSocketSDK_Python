import base64
import datetime
from typing import Optional, TypeVar
from xml.etree import ElementTree

from ..client import Client

class GenericResponse:
    result      : str
    fail_reason : Optional[str]

    def parse(self, doc : ElementTree.Element):
        self.result = doc.findtext("Result")
        if not self.result:
            self.result = "OK"

        self.fail_reason = parse_str(doc, "Reason", None)

    def has_succeeded(self) -> bool:
        return self.result == "OK"

_T = TypeVar('T')

def parse_str(node : ElementTree.Element, tag : str, default : _T = "") -> str | _T:
    elem = node.find(tag)
    if elem is None:
        return default
    return elem.text

def parse_int(node : ElementTree.Element, tag : str, default : _T = 0, base : int = 10) -> int | _T:
    elem = node.find(tag)
    if elem is None:
        return default
    try:
        return int(elem.text, base)
    except ValueError:
        return default

def parse_bool(node : ElementTree.Element, tag : str, default : _T = False) -> bool | _T:
    elem = node.find(tag)
    if elem is None:
        return default
    return elem.text == "Yes" or elem.text == "True" or elem.text == "Y" or elem.text == "T"

def parse_base64(node : ElementTree.Element, tag : str) -> bytes:
    elem = node.find(tag)
    if elem is None:
        return b""
    return base64.b64decode(elem.text)

def parse_base64_string(node : ElementTree.Element, tag : str) -> str:
    data = parse_base64(node, tag)
    result = data.decode("utf-16")
    if len(result) > 0 and result[-1] == '\x00':
        result = result[: -1]
    return result

def parse_datetime(node : ElementTree.Element, tag : str, default : _T = None) -> datetime.datetime | _T:
    elem = node.find(tag)
    if elem is None:
        return default

    try:
        val = elem.text
        date_portion_end = val.find("-T")
        if date_portion_end < 0:
            return default

        year, month, day = val[: date_portion_end].split("-")

        val = val[date_portion_end + 2 :]
        if not val.endswith("Z"):
            return default

        hour, minute, second = val[: -1].split(":")

        return datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
    except:
        return default

def make_text_node(tag : str, value : str) -> ElementTree.Element:
    res = ElementTree.Element(tag)
    res.text = value
    return res

def make_base64_node(tag : str, value : bytes) -> ElementTree.Element:
    return make_text_node(tag, base64.b64encode(value).decode("ascii"))

def make_int_node(tag : str, value : int) -> ElementTree.Element:
    return make_text_node(tag, str(value))

def make_boolean_node(tag : str, value : bool) -> ElementTree.Element:
    return make_text_node(tag, "Yes" if value else "No")

def make_datetime_node(tag : str, value : datetime.datetime) -> ElementTree.Element:
    return make_text_node(tag, f"{value.year:04d}-{value.month:02d}-{value.day:02d}-T{value.hour:02d}:{value.minute:02d}:{value.second:02d}Z")


class GenericRequest:
    response_type = GenericResponse

    def __init__(self, cmd : str):
        self.cmd = cmd

    def to_xml(self) -> ElementTree.Element:
        res = ElementTree.Element("Message")
        res.append(make_text_node("Request", self.cmd))
        return res

    def to_str(self) -> str:
        return ElementTree.tostring(self.to_xml(), encoding = "unicode")

    def transact(self, client : Client, connection_id : int) -> GenericResponse:
        xml_resp = ElementTree.fromstring(client.execute_command(connection_id, self.to_str()))
        result = self.response_type()
        result.parse(xml_resp)
        return result
