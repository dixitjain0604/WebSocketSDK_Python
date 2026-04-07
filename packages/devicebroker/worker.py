from ast import parse
import logging
from typing import Dict, List, Optional
import multiprocessing as mp
import multiprocessing.connection as mpc
from urllib import request
import requests
import secrets
from xml.etree import ElementTree

from . import commands
from . import xml_consts

LOG = logging.getLogger(__name__)

def get_element_value(element : ElementTree.Element, name : str) -> Optional[str]:
    child = element.find(name)
    if child is None:
        return None
    else:
        return child.text

def create_text_element(tag : str, text : str) -> ElementTree.Element:
    result = ElementTree.Element(tag)
    result.text = text
    return result


class Worker:
    connection          : mpc.Connection
    webapp_url          : str
    device_logged_in    : Dict[int, bool]

    def __init__(self, conn : mpc.Connection, webapp_url : str):
        super().__init__()

        self.connection         = conn
        self.webapp_url         = webapp_url
        self.device_logged_in   = dict()

    @classmethod
    def run(cls, conn : mpc.Connection, webapp_url : str):
        self = Worker(conn, webapp_url)

        while True:
            cmd, *args = conn.recv()
            self.process_command(cmd, args)

    def process_command(self, cmd : int, args : tuple):
        if cmd == commands.CLIENT_CONNECTED:
            client_id, = args

        elif cmd == commands.CLIENT_DISCONNECTED:
            client_id, = args
            self.device_logged_in.pop(client_id, None)

        elif cmd == commands.MESSAGE_FROM_CLIENT:
            try:
                client_id, message = args
                parsed_msg = ElementTree.fromstring(message)

                if (request := parsed_msg.find("Request")) is not None:
                    match request.text:
                        case "Register":
                            self.process_register_request(client_id, parsed_msg)
                        case "Login":
                            self.process_login_request(client_id, parsed_msg)
                        case _:
                            pass

                elif (event := parsed_msg.find("Event")) is not None:
                    if self.device_logged_in.get(client_id, False):
                        match event.text:
                            case "AdminLog" | "AdminLog_v2" | "TimeLog" | "TimeLog_v2":
                                self.process_log(client_id, event.text, parsed_msg)

                            case "KeepAlive":
                                self.process_keepalive(client_id, parsed_msg)

                else:
                    self.connection.send((commands.RESPONSE_FROM_DEVICE, client_id, message))

            except Exception as ex:
                LOG.warning(f"Exception : {ex}")

    def process_register_request(self, client_id : int, parsed_msg : ElementTree.Element):
        sn = get_element_value(parsed_msg, xml_consts.TAG_DEVICE_SERIAL_NO)
        if sn is None:
            return

        terminal_type   = get_element_value(parsed_msg, "TerminalType")
        product_name    = get_element_value(parsed_msg, "ProductName")
        cloud_id        = get_element_value(parsed_msg, "CloudId")

        check_res = requests.post(self.webapp_url + "/device/check_registration", json = {
            "sn"            : sn,
            "terminal_type" : terminal_type,
            "product_name"  : product_name,
            "cloud_id"      : cloud_id
        })

        succeeded : bool = False
        token : Optional[str] = None

        if check_res.status_code == requests.codes.ok:
            token = check_res.json().get("token", None)
            if token is not None and token != "":
                succeeded = True

        response = ElementTree.Element(xml_consts.TAG_MESSAGE)
        response.append(create_text_element(xml_consts.TAG_RESPONSE, "Register"))
        response.append(create_text_element(xml_consts.TAG_DEVICE_SERIAL_NO, sn))
        response.append(create_text_element(xml_consts.TAG_TOKEN, token))
        response.append(create_text_element(xml_consts.TAG_RESULT, xml_consts.RESULT_OK if succeeded else xml_consts.RESULT_FAIL))
        self.connection.send((
            commands.SEND_MESSAGE_TO_CLIENT,
            client_id,
            ElementTree.tostring(response, encoding = "unicode") ))

    def process_login_request(self, client_id : int, parsed_msg : ElementTree.Element):
        sn              = get_element_value(parsed_msg, xml_consts.TAG_DEVICE_SERIAL_NO)
        token           = get_element_value(parsed_msg, xml_consts.TAG_TOKEN)
        terminal_type   = get_element_value(parsed_msg, "TerminalType")
        product_name    = get_element_value(parsed_msg, "ProductName")

        check_res = requests.post(self.webapp_url + "/device/check_login", json = {
            "sn"            : sn,
            "token"         : token
        })

        succeeded : bool = False
        result_str : Optional[str] = None
        if check_res.status_code == requests.codes.ok:
            succeeded = True
            result_str = xml_consts.RESULT_OK
        else:
            result_str = check_res.json().get("reason", None)
            if result_str is None or result_str == "":
                result_str = xml_consts.RESULT_FAIL

        response = ElementTree.Element(xml_consts.TAG_MESSAGE)
        response.append(create_text_element(xml_consts.TAG_RESPONSE, "Login"))
        response.append(create_text_element(xml_consts.TAG_DEVICE_SERIAL_NO, sn))
        response.append(create_text_element(xml_consts.TAG_RESULT, result_str))
        self.connection.send((
            commands.SEND_MESSAGE_TO_CLIENT,
            client_id,
            ElementTree.tostring(response, encoding = "unicode") ))

        if succeeded:
            self.device_logged_in[client_id] = True
            self.connection.send((
                commands.ASSIGN_DEVICE_ID,
                client_id,
                sn,
                {
                    "terminal_type" : terminal_type,
                    "product_name"  : product_name,
                } ))

    def process_log(self, client_id : int, log_type : str, parsed_msg : ElementTree.Element):
        data = {}
        for child in parsed_msg:
            data[child.tag] = child.text

        upload_res = requests.post(self.webapp_url + f"/device/upload_log?type={log_type}", json = data)
        succeeded : bool = False
        if upload_res.status_code == requests.codes.ok:
            succeeded = True

        response = ElementTree.Element(xml_consts.TAG_MESSAGE)
        response.append(create_text_element(xml_consts.TAG_RESPONSE, log_type))
        response.append(create_text_element(xml_consts.TAG_RESULT, xml_consts.RESULT_OK if succeeded else xml_consts.RESULT_FAIL))
        if "TransID" in data:
            response.append(create_text_element("TransID", data["TransID"]))

        self.connection.send((
            commands.SEND_MESSAGE_TO_CLIENT,
            client_id,
            ElementTree.tostring(response, encoding = "unicode") ))
    
    def process_keepalive(self, client_id : int, parsed_msg : ElementTree.Element):
        response = ElementTree.Element(xml_consts.TAG_MESSAGE)
        response.append(create_text_element(xml_consts.TAG_RESPONSE, "KeepAlive"))
        response.append(create_text_element(xml_consts.TAG_RESULT, xml_consts.RESULT_OK))

        self.connection.send((
            commands.SEND_MESSAGE_TO_CLIENT,
            client_id,
            ElementTree.tostring(response, encoding = "unicode") ))

class WorkerHost:
    workers : List[mp.Process]

    def __init__(self, pipes : List[mpc.Connection], webapp_url : str):
        super().__init__()

        self.workers = [mp.Process(target = Worker.run, args = (x, webapp_url)) for x in pipes]
        for process in self.workers:
            process.daemon = True
            process.start()

    def stop(self):
        for process in self.workers:
            process.join()
