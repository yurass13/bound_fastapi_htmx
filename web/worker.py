import os
import asyncio
from datetime import datetime
from random import randint
from time import sleep

from celery import Celery
from redis import from_url
from sqlalchemy import select, update

from .db import ProcessingFile, ProcessingFileStatus, sync_session_factory


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get('CELERY_BROKEN_URL', "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

client = from_url(os.environ.get('CELERY_BROKEN_URL', "redis://redis:6379"))


def update_file(file_id: int, **kwargs):
    with sync_session_factory() as session:
        session.execute(update(ProcessingFile)
                                .values(**kwargs)
                                    .filter_by(id=file_id))
        session.commit()

    client.publish(channel='file_status_changed', message=file_id)


@celery.task(name="process_file")
def process_file(file_id: int):
    """Emulate file processing

    Args:
        file_id (int): ProcessingFile.id

    Raises:
        RuntimeError: sample of error handling
    """
    if not isinstance(file_id, int):
        raise TypeError(f"file_id is not Integer {file_id = } {type(file_id) = }")

    try:
        update_file(file_id=file_id,
                    status=ProcessingFileStatus.PROCESSING)
    except Exception as ex:
        raise ValueError(f"ObjectNotFound {file_id = }\n {ex}")

    start_time = datetime.now()
    sleep(randint(2, 20))
    handling_time = (datetime.min + (datetime.now() - start_time)).time()

    try:
        if randint(0, 100) == 0:
            raise RuntimeError('Syntetic Error 1%')

        with sync_session_factory() as session:
            file_path = session.execute(select(ProcessingFile).filter_by(id=file_id)).scalar().file_path

        size = os.path.getsize(file_path)
        status = ProcessingFileStatus.OK

    except (RuntimeError, ValueError):
        status = ProcessingFileStatus.ERROR
        size = None
    finally:
        update_file(file_id=file_id,
                    status=status,
                    handling_time=handling_time,
                    size=size)
