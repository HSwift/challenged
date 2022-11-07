import datetime
from time import time

import fastapi
import jwt

from config import SECRET
from models import User, BannedUser, BannedIP


def sign(uid: int, admin: False, expire_time: int = 172800):
    return jwt.encode({
        'uid': uid,
        'admin': admin,
        'expire': int(time() + expire_time)
    }, SECRET, algorithm='HS256')


def verify(token: str) -> tuple[int, bool]:
    try:
        decoded = jwt.decode(token, SECRET, algorithms=['HS256'])
        if decoded['expire'] > int(time()):
            return decoded['uid'], decoded['admin']
        else:
            return -1, False
    except:
        return -1, False


def _login_required(request: fastapi.Request):
    if request.state.auth:
        return
    else:
        raise fastapi.HTTPException(status_code=403, detail="login required")


login_required = fastapi.Depends(_login_required)


def _admin_required(request: fastapi.Request):
    if request.state.auth and request.state.admin:
        return
    else:
        raise fastapi.HTTPException(status_code=403, detail="admin required")


admin_required = fastapi.Depends(_admin_required)


async def _get_current_user(request: fastapi.Request):
    user = await User.get_or_none(id=request.state.uid)
    baned_user = await BannedUser.get_or_none(user=user)
    if baned_user is not None:
        if baned_user.end_time > datetime.datetime.now(datetime.timezone.utc):
            raise fastapi.HTTPException(status_code=403, detail="your account has been blocked")
        else:
            await baned_user.delete()
    baned_ip = await BannedIP.get_or_none(ip=request.client.host)
    if baned_ip is not None:
        if baned_ip.end_time > datetime.datetime.now(datetime.timezone.utc):
            raise fastapi.HTTPException(status_code=403, detail="your ip address has been blocked")
        else:
            await baned_ip.delete()
    if user is not None:
        return user
    else:
        raise fastapi.HTTPException(status_code=500, detail="user does not exist")


get_current_user = fastapi.Depends(_get_current_user)


def inject_auth_middleware(app: fastapi.FastAPI):
    @app.middleware("http")
    async def jwt_auth_middleware(request: fastapi.Request, call_next):
        request.state.auth = False
        request.state.uid = -1
        request.state.admin = False
        session = request.cookies.get("challenged_session")
        if session is not None:
            uid, admin = verify(session)
            if uid != -1:
                request.state.auth = True
                request.state.uid = uid
                request.state.admin = admin
        return await call_next(request)
