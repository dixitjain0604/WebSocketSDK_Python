from dataclasses import dataclass
import multiprocessing.connection as mpc
from typing import List, Optional

from . import commands

@dataclass
class Device:
    connection_id   : int
    attributes      : dict
    device_id       : str

class Client:
    def __init__(self, address : str):
        super().__init__()

        colon_pos : int = address.rfind(':')
        if colon_pos >= 0:
            address = (address[: colon_pos], int(address[colon_pos+1 :]))

        self.connection = mpc.Client(address)

    def close(self) -> None:
        self.connection.close()

    def find_device(self, device_id : str) -> Optional[Device]:
        self.connection.send(( commands.FIND_DEVICE_BY_ID, device_id ))
        client_id, attribs = self.connection.recv()
        if client_id is None:
            return None
        else:
            return Device(connection_id = client_id, attributes = attribs, device_id = device_id)

    def get_all_online_devices(self) -> List[Device]:
        self.connection.send(( commands.GET_ALL_ONLINE_DEVICES, ))
        dev_list = self.connection.recv()
        return [Device(connection_id = client_id, device_id = device_id, attributes = attribs) for device_id, client_id, attribs in dev_list]

    def get_online_device(self, connection_id : int) -> Optional[Device]:
        self.connection.send(( commands.GET_CONNECTION_INFO, connection_id ))
        device_id, attribs = self.connection.recv()
        if device_id is None:
            return None
        else:
            return Device(connection_id = connection_id, attributes = attribs, device_id = device_id)

    def execute_command(self, connection_id : int, request : str) -> str:
        self.connection.send(( commands.SEND_AND_RECEIVE, connection_id, request ))
        succeeded, error_msg, response = self.connection.recv()
        if not succeeded:
            raise Exception(error_msg)
        
        return response

    def __enter__(self) -> 'Client':
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
