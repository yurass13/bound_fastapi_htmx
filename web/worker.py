import os
from datetime import datetime
from random import randint
from time import sleep
import uuid

from celery import Celery
from celery.result import AsyncResult
from redis import from_url
from sqlalchemy import select, update

from .db import ProcessingFile, ProcessingFileStatus, sync_session_factory


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get('REDIS_URL', "redis://redis:6379/0")
celery.conf.result_backend = os.environ.get("REDIS_URL", "redis://redis:6379/0")

client = from_url(os.environ.get('REDIS_URL', "redis://redis:6379/1"))


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

    status = ProcessingFileStatus.ERROR
    size = None
    try:
        if randint(0, 100) == 0:
            raise RuntimeError('Syntetic Error 1%')

        with sync_session_factory() as session:
            file_path = session.execute(select(ProcessingFile).filter_by(id=file_id)).scalar().file_path

        size = os.path.getsize(file_path)
        status = ProcessingFileStatus.OK

    except (RuntimeError, FileNotFoundError):
        pass
    finally:
        update_file(file_id=file_id,
                    status=status,
                    handling_time=handling_time,
                    size=size)


def terminate_task(task_id: uuid.UUID):
    AsyncResult(str(task_id)).revoke(terminate=True)
