from dataclasses import dataclass
from typing import List, Optional

from . import connection
from devicebroker.client import Device

def get_all() -> List[Device]:
    with connection.open() as c:
        all_devices = c.get_all_online_devices()

    return all_devices

def get(connection_id : int) -> Optional[Device]:
    try:
        with connection.open() as c:
            return c.get_online_device(connection_id)
    except:
        return None
