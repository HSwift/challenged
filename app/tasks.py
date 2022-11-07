import asyncio
import logging

background_tasks = set()


async def task_wrapper(func: callable, *args, **kwargs):
    try:
        await func(*args, **kwargs)
    except Exception as e:
        logging.error("run background_task failed", e)


async def add_background_task(func: callable, *args, **kwargs):
    task = asyncio.create_task(task_wrapper(func, *args, **kwargs))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
