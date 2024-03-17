# syntax=docker/dockerfile:1.0.0-experimental

FROM alpine:3.13

RUN apk add --update \
    python3 \
    python3-dev \
    py3-pip \
    build-base \
    libffi-dev \
    musl-dev \
    gcc \
    libevent-dev

COPY src/ /src/
COPY bin/ /bin/
COPY requirements.txt /

RUN pip install -r requirements.txt

EXPOSE 5000

WORKDIR /src

ENV PYTHONPATH=/src/

RUN addgroup -S rooms
RUN adduser -H -D -S rooms

USER rooms:rooms

ENTRYPOINT ["python3", "server.py"]
