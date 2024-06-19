FROM python:3.12.4-alpine3.20

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY static ./static
COPY templates ./templates
COPY web ./web
