import logging

import fastapi


def setup_logger(app: fastapi.FastAPI):
    @app.on_event("startup")
    def setup():
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(levelname)s] %(asctime)s - %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        fh = logging.FileHandler('challenged.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)
