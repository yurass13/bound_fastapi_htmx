from datetime import datetime, time
from math import ceil

from fastapi.templating import Jinja2Templates

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
