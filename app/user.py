import logging
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import config
import container
import tasks
from auth import login_required, sign, get_current_user
from limiter import rate_limiter
from models import Response, User, UserOut, Operation, ContainerOut, Container, OperationEnum
from remote_auth import verify_token

user_api = APIRouter(prefix="/api")


class LoginIn(BaseModel):
    token: str


@user_api.post('/login')
async def login(request: Request, login_in: LoginIn):
    if re.match(r"^[A-Za-z0-9-]+$", login_in.token) is None:
        raise HTTPException(400, "invalid token")
    user: User = await User.get_or_none(token=login_in.token)
    if user is None:
        logging.info(f"verify user from registry, ip: {request.client.host}")
        ok, username = await verify_token(login_in.token)
        if ok:
            user = await User.create(username=username, token=login_in.token, admin=False)
        else:
            raise HTTPException(400, "invalid token")
    jwt = sign(user.id, user.admin)
    await Operation.create(user=user, type=OperationEnum.login, ip=request.client.host)
    r = Response.success("success", {"username": user.username})
    r = JSONResponse(r)
    r.set_cookie(key='challenged_session', value=jwt, httponly=True)
    return r


@user_api.get("/info", dependencies=[login_required])
async def info(user=get_current_user):
    return Response.success("success", await UserOut.from_tortoise_orm(user))


@user_api.post("/apply_container", dependencies=[login_required, rate_limiter])
async def apply_container(request: Request, user: User = get_current_user):
    if await container.has_container(user):
        raise HTTPException(400, "container already created")
    await Operation.create(user=user, type=OperationEnum.apply_container, ip=request.client.host)
    c = await container.create_container(user)
    return Response.success("success", ContainerOut.from_orm(c))


class FlagIn(BaseModel):
    flag: str


@user_api.post("/submit_flag", dependencies=[login_required, rate_limiter])
async def submit_flag(request: Request, flag_in: FlagIn, user=get_current_user):
    if re.match(r"^flag\{[A-Za-z0-9-]{24}}$", flag_in.flag) is None:
        raise HTTPException(400, "invalid flag")
    await Operation.create(user=user, type=OperationEnum.submit_flag, ip=request.client.host)
    c = await Container.get_or_none(user=user)
    if c is None:
        raise HTTPException(400, detail="no container created")
    if flag_in.flag == c.flag:
        await tasks.add_background_task(container.remove_container, user)
        return Response.success(config.REAL_FLAG)
    else:
        return Response.success("wrong flag")


@user_api.post("/remove_container", dependencies=[login_required, rate_limiter])
async def remove_container(request: Request, user: User = get_current_user):
    await Operation.create(user=user, type=OperationEnum.remove_container, ip=request.client.host)
    success = await container.remove_container(user)
    if success:
        return Response.success("removed")
    else:
        return Response.success("failed")
