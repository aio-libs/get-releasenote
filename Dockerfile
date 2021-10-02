FROM python:3.9.1-slim-buster as installer

RUN python -m pip install -U pip
RUN python -m pip install --user distlib>=0.3.3

FROM python:3.9.1-slim-buster

LABEL "maintainer" "Andrew Svetlov <andrew.svetlov@gmail.com>"
LABEL "repository" "https://github.com/aio-libs/get-releasenote"
LABEL "homepage" "https://github.com/aio-libs/get-releasenote"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY --from=installer /root/.local/ /root/.local/
COPY LICENSE .
COPY get_releasenote.py .

RUN chmod +x get_releasenote.py
ENTRYPOINT ["/app/get_releasenote.py"]
