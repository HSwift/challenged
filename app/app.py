from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

import config
import container
import logger
from auth import inject_auth_middleware
from limiter import inject_rate_limiter
from models import User
from user import user_api

app = FastAPI(title="challenged", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(user_api)
# app.mount("/", StaticFiles(directory="./html", html=True), "html") # for debug 
register_tortoise(
    app,
    db_url=config.DATABASE_DSN,
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=False
)


@app.on_event('startup')
async def init_database():
    if await User.get_or_none(admin=True) is None:
        await User.create(username='admin', token=config.ADMIN_TOKEN, admin=True)


logger.setup_logger(app)
inject_auth_middleware(app)
inject_rate_limiter(app)
container.inject_container_monitor(app)

# uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers
