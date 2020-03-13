FROM python:3.7-alpine

COPY py py
RUN apk update && apk add postgresql-dev gcc musl-dev
RUN pip3 install -r py/requirements.txt
ENTRYPOINT python3 py/main.py

HEALTHCHECK --interval=30s --timeout=1s --retries=2 \
  CMD curl -f http://localhost/api/v1/ping || exit 1