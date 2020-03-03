FROM python:3.7-alpine

COPY py py
RUN apk update && apk add postgresql-dev gcc musl-dev
RUN pip3 install -r py/requirements.txt
ENTRYPOINT python3 py/main.py
