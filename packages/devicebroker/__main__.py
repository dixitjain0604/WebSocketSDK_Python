import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import multiprocessing as mp
import multiprocessing.connection as mpc
import signal
from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers

from .load_balancing import LoadBalancer
from .worker import WorkerHost

LOG = logging.getLogger(__name__)

async def health_check_handler(websocket, request):
    """Handle HTTP health check requests from Railway or other platforms."""
    # If it's a plain HTTP request with Connection: close (health check)
    if request.headers.get("Connection") == "close":
        # Return a 200 OK HTTP response for health checks
        return Response(200, "OK", Headers([("Connection", "close")]), b"OK")
    # Otherwise, let WebSocket upgrade proceed normally
    return None

async def run_device_server(loadbalancer : LoadBalancer, host : str, port : int, cancellation : asyncio.Future):
    async with serve(
        loadbalancer.serve_device,
        host,
        port,
        process_request=health_check_handler
    ) as server:
        await cancellation

async def run_application_server(loadbalancer : LoadBalancer, sock_name : str):
    loop = asyncio.get_running_loop()

    colon_pos : int = sock_name.rfind(':')
    if colon_pos >= 0:
        address = (sock_name[:colon_pos], int(sock_name[colon_pos + 1:]))
    else:
        address = sock_name

    tasks = set()
    with ThreadPoolExecutor(max_workers = 1) as executor:
        with mpc.Listener(address) as listener:
            while True:
                conn : mpc.Connection = await loop.run_in_executor(executor, listener.accept)
                task : asyncio.Task = asyncio.create_task(loadbalancer.serve_application(conn))
                tasks.add(task)
                task.add_done_callback(tasks.discard)

async def wait_cancellation(cancellation : asyncio.Future):
    await cancellation

async def main(args):
    num_workers : int = args.workers
    if num_workers <= 0:
        num_workers = mp.cpu_count()

    # Create pipes
    host_pipes, worker_pipes = zip(*(mp.Pipe() for _ in range(0, num_workers)))

    # Create load balancer
    loadbalancer = LoadBalancer(host_pipes)

    # Spawn worker processes
    worker_host = WorkerHost(worker_pipes, args.webapp_url)

    for pipe in worker_pipes:
        pipe.close()

    cancellation = asyncio.Future()
    def sigint_handler(signum, frame):
        LOG.info("Cleaning up...")
        cancellation.set_exception(KeyboardInterrupt())
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(wait_cancellation(cancellation))
            tg.create_task(run_device_server(loadbalancer, args.host, args.port, cancellation))
            tg.create_task(run_application_server(loadbalancer, args.sock_name))
            for i in range(0, num_workers):
                tg.create_task(loadbalancer.receive_messages_from_worker(i))

    finally:
        for pipe in host_pipes:
            pipe : mpc.Connection
            pipe.close()
        worker_host.stop()

if __name__ == "__main__":
    import argparse
    from . import defaults

    parser = argparse.ArgumentParser()
    parser.add_argument("--host"        , type = str, default = "localhost")
    parser.add_argument("--port"        , type = int, default = 8001)
    parser.add_argument("--sock-name"   , type = str, default = defaults.DEF_SOCK_NAME)
    parser.add_argument("--workers"     , type = int, default = 0)
    parser.add_argument("--webapp-url"  , type = str, default = "http://localhost:8000")
    args = parser.parse_args()

    logging.basicConfig(level = logging.DEBUG)

    asyncio.run(main(args))
