FROM python:3.9.1-slim-buster

LABEL "maintainer" "Andrew Svetlov <andrew.svetlov@gmail.com>"
LABEL "repository" "https://github.com/aio-libs/get-releasenote"
LABEL "homepage" "https://github.com/aio-libs/get-releasenote"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install -U pip && pip install --user distlib

COPY LICENSE .
COPY get_releasenote.py .

RUN chmod +x get_releasenote.py
ENTRYPOINT ["/app/get_releasenote.py"]
