import os
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .db import init_models
from .processing_file import processing_file_router
from .templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    if bool(os.environ.get("DEBUG", True)):
        await init_models()

    os.makedirs('./media/processing_files/', exist_ok=True)

    yield

    shutil.rmtree('./media/processing_files/', ignore_errors=True)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(processing_file_router, prefix="/processing_file", tags=["processing_file"])


@app.get("/", name="homepage")
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
