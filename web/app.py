from datetime import datetime, time
from math import ceil
import os
import shutil
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select, update

from .db import ProcessingFile, init_models, session_factory, ProcessingFileStatus
from .services import emit_file_status_changed, subscribe_file_status_changed
from .worker import process_file


@asynccontextmanager
async def lifespan(app: FastAPI):
    if bool(os.environ.get("DEBUG", True)):
        await init_models()

    os.makedirs('./media/processing_files/', exist_ok=True)

    yield

    shutil.rmtree('./media/processing_files/', ignore_errors=True)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def view_datetime(time_: datetime) -> str:
    if time_ is None:
        return ""

    time_.replace(microsecond=ceil(time_.microsecond / 10_000))
    return time_.strftime('%d.%m.%Y %H:%M:%S')


def view_time(datetime_: time) -> str:
    if datetime_ is None:
        return ""

    return datetime_.strftime('%H:%M:%S')

templates.env.filters["view_datetime"] = view_datetime
templates.env.filters["view_time"] = view_time


@app.get("/", name="homepage")
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/processing_file/")
async def create_processing_file(request: Request, file: UploadFile):
    if file.content_type != "text/csv":
        return templates.TemplateResponse(request=request,
                                          name="primitives/upload/dismiss.html",
                                          context={"filename": file.filename})

    processing_file = ProcessingFile(filename=file.filename)
    file_id = None
    async with session_factory() as session:
        session.add(processing_file)

        await session.flush()
        file_id = processing_file.id

        await session.commit()
    await emit_file_status_changed(file_id=file_id)

    with open(f"./media/processing_files/{file_id}", 'wb') as writer:
        writer.write(file.file.read())

    process_file.delay(file_id)

    return templates.TemplateResponse(request=request,
                                      name="primitives/upload/success.html",
                                      context={"filename": file.filename})


@app.get("/processing_file/{file_id: int}/detail/")
async def get_processing_file(request: Request, file_id: str):
    async with session_factory() as session:
        result = await session.execute(select(ProcessingFile).filter_by(id=file_id))
        processing_file = result.scalar()

        with open(processing_file.file_path, 'r') as file:
            rows = file.readlines(10)

        return templates.TemplateResponse(request=request,
                                        name="processing_files/detail.html",
                                        context={"file": processing_file,
                                                "data": rows})


@app.delete("/processing_file/{file_id: int}/")
async def cancel_or_delete_processing_file(file_id: int):
    async with session_factory() as session:
        result = await session.execute(select(ProcessingFile).filter_by(id=file_id))
        processing_file = result.scalar()

        if processing_file is None:
            raise ValueError()

        if processing_file.status == ProcessingFileStatus.OK:
            status = ProcessingFileStatus.REMOVED
            if os.path.exists(processing_file.file_path):
                os.remove(processing_file.file_path)

        else:
            status = ProcessingFileStatus.CANCELED
        stmt = (
            update(ProcessingFile)
                .values(status=status)
                    .filter_by(id=file_id))

        await session.execute(stmt)
        await session.commit()

    await emit_file_status_changed(file_id=file_id)


@app.get("/processing_file/listen-updates/")
async def listen_handling_status(request: Request):
    return StreamingResponse(get_files_on_status_changed(request), media_type="text/event-stream")


async def get_files_on_status_changed(request: Request) -> AsyncGenerator[str, None]:
    while True:
        async with session_factory() as session:
            result = await session.execute(select(ProcessingFile).order_by(desc(ProcessingFile.created_at)))
            files = result.scalars()
            template = templates.TemplateResponse("processing_files/list.html", 
                                                  context={"request": request,
                                                           "files": files}
                                                  )
        content = template.body.decode("utf-8").replace("\n", "")

        yield f"event: handlingStatusChanged\ndata: {content}\n\n"

        await subscribe_file_status_changed()
