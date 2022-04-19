# syntax=docker/dockerfile:1.0.0-experimental

FROM alpine

RUN apk add --update \
    python3 \
    python3-dev \
    py3-pip \
    build-base \
    git \
    openssh-client \
    libffi-dev \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/*

RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

COPY ./requirements.txt /app/requirements.txt
RUN --mount=type=ssh pip install -r /app/requirements.txt

RUN addgroup -S rooms
RUN adduser -H -D -S rooms
USER rooms:rooms

COPY ./server.py /app/
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY scripts/ /app/scripts/
COPY maps/ /app/maps/

EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["python3", "/app/server.py"]
