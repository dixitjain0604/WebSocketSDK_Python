from typing import Optional
from xml.etree import ElementTree

from .. import messages

class GetEthernetSettingResponse(messages.GenericResponse):
    use_dhcp                : bool
    ip_address              : str
    subnet_mask             : str
    gateway                 : str
    port                    : Optional[int]
    mac_address             : str
    ip_address_from_dhcp    : str
    subnet_mask_from_dhcp   : str
    gateway_from_dhcp       : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.use_dhcp               = messages.parse_bool(doc, "DHCP")
        self.ip_address             = messages.parse_str(doc, "IP")
        self.subnet_mask            = messages.parse_str(doc, "Subnet")
        self.gateway                = messages.parse_str(doc, "DefaultGateway")
        self.port                   = messages.parse_int(doc, "Port", None)
        self.mac_address            = messages.parse_str(doc, "MacAddress")
        self.ip_address_from_dhcp   = messages.parse_str(doc, "IP_from_dhcp")
        self.subnet_mask_from_dhcp  = messages.parse_str(doc, "Subnet_from_dhcp")
        self.gateway_from_dhcp      = messages.parse_str(doc, "DefaultGateway_from_dhcp")

class GetEthernetSettingRequest(messages.GenericRequest):
    response_type = GetEthernetSettingResponse

    def __init__(self):
        super().__init__("GetEthernetSetting")

class SetEthernetSettingRequest(messages.GenericRequest):
    use_dhcp                : bool
    ip_address              : str
    subnet_mask             : str
    gateway                 : str
    port                    : int
    
    def __init__(self, use_dhcp : bool, ip_address : str, subnet_mask : str, gateway : str, port : int):
        super().__init__("SetEthernet")

        self.use_dhcp       = use_dhcp
        self.ip_address     = ip_address
        self.subnet_mask    = subnet_mask
        self.gateway        = gateway
        self.port           = port

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_boolean_node("DHCP", self.use_dhcp))
        result.append(messages.make_text_node("IP", self.ip_address))
        result.append(messages.make_text_node("Subnet", self.subnet_mask))
        result.append(messages.make_text_node("DefaultGateway", self.gateway))
        result.append(messages.make_int_node("Port", self.port))
        return result

class GetWifiSettingResponse(messages.GenericResponse):
    use_wifi                : bool
    ssid                    : str
    key                     : str
    use_dhcp                : bool
    ip_address              : str
    subnet_mask             : str
    gateway                 : str
    port                    : Optional[int]
    ip_address_from_dhcp    : str
    subnet_mask_from_dhcp   : str
    gateway_from_dhcp       : str

    def parse(self, doc : ElementTree.Element):
        super().parse(doc)

        self.use_wifi               = messages.parse_bool(doc, "Use")
        self.ssid                   = messages.parse_str(doc, "SSID")
        self.key                    = messages.parse_str(doc, "Key")
        self.use_dhcp               = messages.parse_bool(doc, "DHCP")
        self.ip_address             = messages.parse_str(doc, "IP")
        self.subnet_mask            = messages.parse_str(doc, "Subnet")
        self.gateway                = messages.parse_str(doc, "DefaultGateway")
        self.port                   = messages.parse_int(doc, "Port", None)
        self.ip_address_from_dhcp   = messages.parse_str(doc, "IP_from_dhcp")
        self.subnet_mask_from_dhcp  = messages.parse_str(doc, "Subnet_from_dhcp")
        self.gateway_from_dhcp      = messages.parse_str(doc, "DefaultGateway_from_dhcp")

class GetWifiSettingRequest(messages.GenericRequest):
    response_type = GetWifiSettingResponse

    def __init__(self):
        super().__init__("GetWiFiSetting")

class SetWifiSettingRequest(messages.GenericRequest):
    use_wifi                : bool
    ssid                    : str
    key                     : str
    use_dhcp                : bool
    ip_address              : str
    subnet_mask             : str
    gateway                 : str
    port                    : int
    
    def __init__(self, use_wifi : bool, ssid : str, key : str, use_dhcp : bool, ip_address : str, subnet_mask : str, gateway : str, port : int):
        super().__init__("SetWiFi")

        self.use_wifi       = use_wifi
        self.ssid           = ssid
        self.key            = key
        self.use_dhcp       = use_dhcp
        self.ip_address     = ip_address
        self.subnet_mask    = subnet_mask
        self.gateway        = gateway
        self.port           = port

    def to_xml(self) -> ElementTree.Element:
        result = super().to_xml()
        result.append(messages.make_boolean_node("Use", self.use_wifi))
        result.append(messages.make_text_node("SSID", self.ssid))
        result.append(messages.make_text_node("Key", self.key))
        result.append(messages.make_boolean_node("DHCP", self.use_dhcp))
        result.append(messages.make_text_node("IP", self.ip_address))
        result.append(messages.make_text_node("Subnet", self.subnet_mask))
        result.append(messages.make_text_node("DefaultGateway", self.gateway))
        result.append(messages.make_int_node("Port", self.port))
        return result
