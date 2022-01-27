FROM python:3.10-slim

COPY get_releasenote.py /get_releasenote.py
RUN pip install packaging==21.3

ENTRYPOINT ["/get_releasenote.py"]
