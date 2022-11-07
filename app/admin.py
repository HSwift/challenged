import datetime
import time

import tortoise
from fastapi import APIRouter, Request
from pydantic import BaseModel

import tasks
from auth import admin_required

import config
from models import User, BannedUser, BannedIP, Operation

admin_api = APIRouter(prefix=config.ADMIN_URL_PREFIX, dependencies=[admin_required])


@admin_api.get('/cache_info')
def cache_info(request: Request):
    cache = request.app.state.cache.cache_storage
    return {"len": len(cache), "cache": cache}


@admin_api.get('/background_tasks_info')
def background_tasks_info():
    return {"len": len(tasks.background_tasks)}


@admin_api.get("/users")
async def list_user(size: int = 10, page: int = 0):
    return await User.all().offset(page).limit(size)


@admin_api.get("/user/:id")
async def get_user(id: int):
    user = await User.get_or_none(id=id).prefetch_related("container", "operations", "banned")
    return {"user": user, "container": user.container, "banned": user.banned}


class BlockUserIn(BaseModel):
    user_id: int
    block_minutes: int


@admin_api.post("/block_user")
async def add_block_user(block_in: BlockUserIn):
    now = datetime.datetime.now(datetime.timezone.utc)
    block_end = now + datetime.timedelta(minutes=block_in.block_minutes)
    bannedUser = await BannedUser.create(user_id=block_in.user_id, end_time=block_end)
    return bannedUser


@admin_api.delete("/block_user")
async def delete_block_user(block_in: BlockUserIn):
    try:
        banned_user = await BannedUser.get(user_id=block_in.user_id)
        await banned_user.delete()
        return "success"
    except tortoise.exceptions.DoesNotExist as e:
        return str(e)


class BlockIPIn(BaseModel):
    ip: str
    block_minutes: int


@admin_api.get("/block_ip")
async def list_block_ip(size: int = 10, page: int = 0):
    return await BannedIP.all().offset(page).limit(size)


@admin_api.post("/block_ip")
async def add_block_ip(block_in: BlockIPIn):
    now = datetime.datetime.now(datetime.timezone.utc)
    block_end = now + datetime.timedelta(minutes=block_in.block_minutes)
    bannedUser = await BannedIP.create(ip=block_in.ip, end_time=block_end)
    return bannedUser


@admin_api.delete("/block_ip")
async def delete_block_ip(block_in: BlockIPIn):
    try:
        banned_user = await BannedIP.get(ip=block_in.ip)
        await banned_user.delete()
        return "success"
    except tortoise.exceptions.DoesNotExist as e:
        return str(e)


@admin_api.get("/operations_ip")
async def get_operations(ip: str, size: int = 10, page: int = 0):
    return await Operation.filter(ip=ip).offset(page).limit(size)


@admin_api.get("/operations_user")
async def get_operations(user_id: int, size: int = 10, page: int = 0):
    return await Operation.filter(user_id=user_id).offset(page).limit(size)
