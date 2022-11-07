import asyncio
import datetime
import logging
import random
import string

import docker
import fastapi
import psutil
from docker.errors import DockerException, NotFound
from docker.models.containers import Container as SDKContainer
from fastapi_utils.tasks import repeat_every
import iso8601

import config
from config import PORT_RANGE
from models import User, Container
from fastapi import HTTPException

container_config = config.CONTAINER_INFO

client = docker.from_env()
docker_opt_lock = asyncio.Lock()


def gen_flag():
    t = ''.join(random.sample(string.ascii_letters + string.digits, 24))
    return f'flag{{{t}}}'


async def gen_port():
    used_port = await Container.all().values_list('port')
    selected_port = -1
    for _ in range(10):
        selected_port = random.randrange(*PORT_RANGE)
        if selected_port in used_port:
            continue
    if selected_port == -1:
        raise HTTPException(503, detail="try again later")
    return selected_port


def check_memory_usage():
    memory = psutil.virtual_memory()
    if memory.available < config.MEM_LIMIT:
        logging.error(f"insufficient system memory now: {memory.available // 1024}M")
        raise HTTPException(503, detail="no resources available, try again later")


async def has_container(user: User):
    async with docker_opt_lock:
        container = await Container.get_or_none(user=user)
        if container is not None:
            return True
        else:
            return False


async def create_container(user: User):
    check_memory_usage()
    selected_port = await gen_port()
    container = await Container.create(cid="", user=user, running=True, flag=gen_flag(), port=selected_port, ip="")
    container_name = f"{config.CONTAINER_PREFIX}{container.id}"
    try:
        c = client.containers.run(
            image=container_config["image_name"],
            name=container_name,
            detach=True,
            ports={container_config["exposed_port"]: selected_port},
            restart_policy={"Name": "on-failure"},
            oom_kill_disable=True,
            environment={"flag": container.flag},
            mem_limit=container_config["mem_limit"],
            pids_limit=container_config["pids_limit"]
        )
        try:
            ip = c.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
        except KeyError:
            ip = ""
        container.cid = c.id
        container.ip = ip
        logging.info(f"user {user.id} create container {c.id} with address {ip}")
    except Exception as e:
        logging.error("user {user.id} create container failed", e)
        await container.delete()
        raise HTTPException(500, detail="create container failed")
    await container.save(update_fields=['cid'])
    return container


async def remove_container(user: User) -> bool:
    container = await Container.get_or_none(user=user)
    if container is None:
        return True
    cid = container.cid
    if cid == "":
        await container.delete()
    logging.info(f"remove container {cid} by user {user.id}")
    try:
        async with docker_opt_lock:
            c: SDKContainer = client.containers.get(cid)
            c.stop(timeout=0)
            c.remove()
            await container.delete()
            return True
    except NotFound as e:
        logging.error(f"container {cid} not found")
        await container.delete()
        return True
    except DockerException as e:
        logging.error(f"stop container {cid} failed", e)
    return False


async def remove_container_by_instance(c: SDKContainer):
    container = await Container.get_or_none(cid=c.id).prefetch_related("user")
    async with docker_opt_lock:
        c.stop(timeout=0)
        c.remove()
        logging.info(f"[schedule] remove container {c.id} by user {container.user.id}")
        if container is None:
            logging.info(f"container {c.id} has no database record")
        else:
            await container.delete()


async def check_container(c: SDKContainer):
    create_time = c.attrs["Created"]
    create_time = iso8601.parse_date(create_time)
    now = datetime.datetime.now(datetime.timezone.utc)
    if (now - create_time).seconds > container_config["live_span"]:
        try:
            await remove_container_by_instance(c)
        except Exception as e:
            logging.info(f"[schedule] stop container {c.id} failed", e)


def inject_container_monitor(app: fastapi.FastAPI):
    @app.on_event("startup")
    @repeat_every(seconds=60)
    async def container_monitor():
        containers: list[SDKContainer] = client.containers.list()
        memory = psutil.virtual_memory()
        containers = list(filter(lambda x: x.name.startswith(config.CONTAINER_PREFIX), containers))
        # logging.debug(f"[schedule] container count: {len(containers)}, available memory: {memory.available // 1024}M")
        for c in containers:
            await check_container(c)
