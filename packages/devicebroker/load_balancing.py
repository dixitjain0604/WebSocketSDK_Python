from dataclasses import dataclass
import logging
from multiprocessing.connection import Connection as PipeConnection
from typing import Collection, Dict, List, Optional, Set, Tuple
from websockets.asyncio.server import ServerConnection
import asyncio
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

from . import worker
from . import commands

LOG = logging.getLogger(__name__)

@dataclass
class PendingCommandNode:
    future      : asyncio.Future[str]
    list_obj    : Optional['PendingCommandList'] = None
    prev_node   : Optional['PendingCommandNode'] = None
    next_node   : Optional['PendingCommandNode'] = None

@dataclass
class PendingCommandList:
    first_node  : Optional[PendingCommandNode]
    last_node   : Optional[PendingCommandNode]

    def __init__(self):
        super().__init__()
        self.first_node = None
        self.last_node  = None

    def add_last(self, node : PendingCommandNode):
        assert node.list_obj is None

        node.prev_node  = self.last_node
        node.next_node  = None
        node.list_obj   = self

        if self.last_node is not None:
            self.last_node.next_node = node
        else:
            self.first_node = node
        self.last_node = node

    def remove(self, node : PendingCommandNode):
        assert node.list_obj is self

        prev_node = node.prev_node
        next_node = node.next_node

        if prev_node is not None:
            prev_node.next_node = next_node
        else:
            self.first_node = next_node

        if next_node is not None:
            next_node.prev_node = prev_node
        else:
            self.last_node = prev_node

        node.prev_node  = None
        node.next_node  = None
        node.list_obj   = None


@dataclass
class OnlineDevice:
    client_id           : int
    worker_index        : int
    connection          : ServerConnection
    send_lock           : asyncio.Lock
    device_id           : Optional[str]
    attribs             : dict
    closed              : bool
    pending_commands    : PendingCommandList

class LoadBalancer:
    worker_index        : int
    next_client_id      : int
    lock                : asyncio.Lock
    worker_connections  : List[Tuple[PipeConnection, asyncio.Lock]]
    worker_processes    : List[mp.Process]

    clients_map         : Dict[int, OnlineDevice]
    devices_map         : Dict[str, OnlineDevice]

    misc_tasks          : Set[asyncio.Task]

    def __init__(self, pipes : Collection[PipeConnection]):
        super().__init__()

        self.worker_index       = 0
        self.next_client_id     = 0
        self.lock               = asyncio.Lock()
        self.worker_connections = [(conn, asyncio.Lock()) for conn in pipes]

        self.clients_map        = dict()
        self.devices_map        = dict()
        self.misc_tasks         = set()

    async def serve_device(self, sock : ServerConnection):
        looper = asyncio.get_running_loop()

        # Assign a new client ID and select a worker.
        async with self.lock:
            online_device = OnlineDevice(
                client_id           = self.next_client_id,
                worker_index        = self.worker_index,
                connection          = sock,
                send_lock           = asyncio.Lock(),
                device_id           = None,
                attribs             = dict(),
                closed              = False,
                pending_commands    = PendingCommandList())

            self.worker_index = online_device.worker_index + 1 if online_device.worker_index < len(self.worker_connections) - 1 else 0
            self.next_client_id = online_device.client_id + 1
            self.clients_map[online_device.client_id] = online_device

        LOG.info(f"Assigned ID {online_device.client_id} to websocket connection {sock.remote_address}")

        worker_conn, worker_lock = self.worker_connections[online_device.worker_index]

        # Relay messages from device.
        async with worker_lock:
            await looper.run_in_executor(None, worker_conn.send, (commands.CLIENT_CONNECTED, online_device.client_id))
        
        try:
            async for message in sock:
                async with worker_lock:
                    await looper.run_in_executor(None, worker_conn.send, (commands.MESSAGE_FROM_CLIENT, online_device.client_id, message))

        except Exception as ex:
            LOG.warning(f"Exception in client {online_device.client_id} : {ex}")

        finally:
            async with worker_lock:
                await looper.run_in_executor(None, worker_conn.send, (commands.CLIENT_DISCONNECTED, online_device.client_id))
            
            async with self.lock:
                self.clients_map.pop(online_device.client_id, None)
                if online_device.device_id is not None:
                    self.devices_map.pop(online_device.device_id, None)

            async with online_device.send_lock:
                online_device.closed = True
                while (node := online_device.pending_commands.first_node) is not None:
                    online_device.pending_commands.remove(node)
                    try:
                        node.future.set_exception(Exception("Connection to the device was lost."))
                    except:
                        pass
            
            LOG.info(f"Removed client {online_device.client_id}")

    async def serve_application(self, conn : PipeConnection):
        looper = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers = 1) as executor:
            while True:
                try:
                    cmd, *args = await looper.run_in_executor(executor, conn.recv)
                except EOFError:
                    break

                resp = await self.process_message_from_application(looper, cmd, args)

                if resp is None:
                    break

                await looper.run_in_executor(None, conn.send, resp)

    async def process_message_from_application(self, looper : asyncio.AbstractEventLoop, cmd : int, args : tuple) -> Optional[tuple]:
        if cmd == commands.FIND_DEVICE_BY_ID:
            device_id, = args

            async with self.lock:
                online_device = self.devices_map.get(device_id, None)

            if online_device is not None:
                client_id = online_device.client_id
                attribs   = online_device.attribs
            else:
                client_id = None
                attribs   = None

            return client_id, attribs

        elif cmd == commands.GET_ALL_ONLINE_DEVICES:
            async with self.lock:
                devices_list = [(device_id, device.client_id, device.attribs) for device_id, device in self.devices_map.items()]

            return devices_list

        elif cmd == commands.GET_CONNECTION_INFO:
            async with self.lock:
                client_id, = args
                device = self.clients_map.get(client_id, None)

            if device is not None:
                return device.device_id, device.attribs
            else:
                return None, None

        elif cmd == commands.SEND_AND_RECEIVE:
            client_id, request = args

            async with self.lock:
                online_device = self.clients_map.get(client_id, None)

            if online_device is None:
                return False, "Device is offline", None

            node = PendingCommandNode(future = asyncio.Future())

            try:
                async with online_device.send_lock:
                    if online_device.closed:
                        return False, "Device is offline", None

                    online_device.pending_commands.add_last(node)
                    await online_device.connection.send(request)

                response = await asyncio.wait_for(node.future, timeout = 30)
                return True, None, response
            
            except TimeoutError as ex:
                return False, "Timed out", None

            except Exception as ex:
                return False, str(ex), None

            finally:
                if node.list_obj is not None:
                    async with online_device.send_lock:
                        if node.list_obj is not None: # Need to re-check after acquiring the lock
                            online_device.pending_commands.remove(node)

        else:
            return None

    async def receive_messages_from_worker(self, worker_index : int):
        looper = asyncio.get_running_loop()
        pipe, _ = self.worker_connections[worker_index]

        try:
            with ThreadPoolExecutor(max_workers = 1) as executor:
                while True:
                    cmd, *args = await looper.run_in_executor(executor, pipe.recv)
                    await self.process_message_from_worker(worker_index, cmd, args)
        except Exception as ex:
            LOG.error(f"Exception while processing message from worker : {ex}")

    async def process_message_from_worker(self, worker_index : int, cmd : int, args : tuple):
        if cmd == commands.ASSIGN_DEVICE_ID:
            client_id, device_id, device_attribs = args

            existing_device : Optional[OnlineDevice] = None

            async with self.lock:
                online_device = self.clients_map.get(client_id, None)
                if online_device is not None:
                    if online_device.device_id is not None:
                        self.devices_map.pop(online_device.device_id, None)

                    existing_device = self.devices_map.pop(device_id, None)
                    if existing_device is not None:
                        existing_device.device_id = None

                    online_device.device_id = device_id
                    online_device.attribs   = device_attribs

                    if online_device.device_id is not None:
                        self.devices_map[online_device.device_id] = online_device

            if existing_device is not None:
                LOG.warn(f"Disconnecting old client {existing_device.client_id} with assigned device ID {device_id}")
                task : asyncio.Task = asyncio.create_task(existing_device.connection.close())
                self.misc_tasks.add(task)
                task.add_done_callback(self.misc_tasks.discard)

            if online_device is not None:
                LOG.info(f"Assigned device ID {device_id} to client {client_id}")
            else:
                LOG.warn(f"Failed to assign device ID {device_id} to client {client_id} : client not found")

        elif cmd == commands.SEND_MESSAGE_TO_CLIENT:
            client_id, content = args

            async with self.lock:
                online_device = self.clients_map.get(client_id, None)

            if online_device is not None:
                try:
                    async with online_device.send_lock:
                        await online_device.connection.send(content)
                except Exception as ex:
                    LOG.warn(f"Exception while sending to client {client_id} : {ex}")
            else:
                LOG.warn(f"Failed to send message to client {client_id} : client not found")

        elif cmd == commands.RESPONSE_FROM_DEVICE:
            client_id, content = args

            async with self.lock:
                online_device = self.clients_map.get(client_id, None)

            if online_device is not None:
                try:
                    async with online_device.send_lock:
                        node = online_device.pending_commands.first_node
                        if node is None:
                            return
                        online_device.pending_commands.remove(node)

                    node.future.set_result(content)

                except Exception as ex:
                    LOG.warn(f"Exception while processing response from client {client_id} : {ex}")

        else:
            LOG.warn(f"Unrecognized message from worker : {cmd}")
