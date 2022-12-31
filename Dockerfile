# syntax=docker/dockerfile:1.0.0-experimental

FROM alpine

RUN apk add --update \
    python3 \
    python3-dev \
    py3-pip \
    build-base \
    libffi-dev \
    musl-dev \
    gcc \
    libevent-dev \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/*


RUN addgroup -S rooms
RUN adduser -H -D -S rooms

COPY src/ /src/
COPY bin/ /bin/
COPY requirements.txt /

ENV PYTHONPATH=.:/src

RUN pip install -r requirements.txt

EXPOSE 5000

WORKDIR /src
USER rooms:rooms

ENTRYPOINT ["python3", "/app/server.py"]
