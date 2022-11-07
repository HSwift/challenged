import random
import string

SECRET = ''.join(random.sample(string.ascii_letters + string.digits, 16))
DATABASE_DSN = "sqlite://db.sqlite3"  # or use mysql
REAL_FLAG = "flag{test-flag}"
ADMIN_TOKEN = "6d04aa75-35f8-45a5-b75d-bfc28c88904f"  # TODO: must change
MEM_LIMIT = 256 * 1024 * 1024  # reserved memory
PORT_RANGE = [10000, 60000]
CONTAINER_PREFIX = "challenged-C"
ADMIN_URL_PREFIX = "/admin"
CONTAINER_INFO = {
    "image_name": "challenge-image",  # TODO: must change
    "live_span": 5 * 60,  # 5 min
    "exposed_port": 8888,
    "mem_limit": "300m",
    "pids_limit": 256,
}
