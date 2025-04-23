import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

LOGGER = logging.getLogger(__name__)

TASK_QUEUE: asyncio.Queue = asyncio.Queue()


async def worker():
    LOGGER.info("Background worker started.")
    while True:
        try:
            task = await TASK_QUEUE.get()
            if not task:
                LOGGER.info("Worker received sentinel, exiting.")
                break

            LOGGER.info(f"Worker got a new task: {task}")
            await _process_task(task)
        except Exception as exc:
            LOGGER.exception(f"Error in worker: {exc}")
        finally:
            TASK_QUEUE.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.info("App is starting up. Creating background worker...")
    loop = asyncio.get_running_loop()
    loop.create_task(worker())
    yield
    LOGGER.info("App is shutting down. Stopping background worker...")
    TASK_QUEUE.put_nowait(None)


APP = FastAPI(lifespan=lifespan)


@APP.post("/rag/index")
async def rag_index(req: Request):
    # Get the request body as JSON
    body = await req.json()

    LOGGER.info(f"Received request: {body}")
    return {"status": "success"}


@APP.delete("/rag/delete")
async def rag_delete(req: Request):
    # Get the request body as JSON
    body = await req.json()

    LOGGER.info(f"Received request: {body}")
    return {"status": "success"}

@APP.get("/rag/search")
async def rag_search(req: Request):
    # Get the request parameters3
    params = req.query_params

    LOGGER.info(f"Received request: {params}")
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("langconnect.server:APP", host="0.0.0.0", port=8080)
