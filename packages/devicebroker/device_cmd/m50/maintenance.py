from xml.etree import ElementTree
from .. import messages

class GetFirmwareVersionResponse:
    version         : str
    build_number    : str

    def parse(self, doc : ElementTree.Element):
        self.version = messages.parse_str(doc, "Version")
        self.build_number = messages.parse_str(doc, "BuildNumber")

class GetFirmwareVersionRequest(messages.GenericRequest):
    response_type = GetFirmwareVersionResponse

    def __init__(self):
        super().__init__("GetFirmwareVersion")

class WriteFirmwareRequest(messages.GenericRequest):
    url : str

    def __init__(self, url : str):
        super().__init__("FirmwareUpgradeHttp")
        self.url = url

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        encoded = self.url.encode("utf-8")
        result.append(messages.make_int_node("Size", len(self.url)))
        result.append(messages.make_base64_node("Data", encoded))
        return result
