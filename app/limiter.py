import logging
import time

import fastapi


class CacheBase:
    def __init__(self, gc_size=50):
        self.cache_storage: dict[any, tuple[any, int]] = {}
        self.gc_size = gc_size

    def set(self, key, data, expire):
        if len(self.cache_storage) > self.gc_size:
            self.gc()
        self.cache_storage[key] = (data, int(expire))

    def get(self, key):
        if len(self.cache_storage) > self.gc_size:
            self.gc()
        try:
            o = self.cache_storage[key]
            if int(time.time()) > o[1]:
                del self.cache_storage[key]
                return None
            else:
                return o[0]
        except KeyError:
            return None

    def gc(self):
        now = int(time.time())
        for i in list(self.cache_storage.keys()):
            try:
                if now > self.cache_storage[i][1]:
                    del self.cache_storage[i]
            except KeyError:
                continue


def _rate_limiter(request: fastapi.Request):
    cache: CacheBase = request.app.state.cache
    uid = request.state.uid
    now = int(time.time())
    if cache.get(uid) is None:
        cache.set(uid, True, now + 10)
        return
    else:
        logging.info(f"user {uid} request too fast")
        raise fastapi.HTTPException(status_code=429, detail="request too fast")


rate_limiter = fastapi.Depends(_rate_limiter)


def inject_rate_limiter(app: fastapi.FastAPI):
    app.state.cache = CacheBase()
