#!/bin/bash

export FLASK_SESSION_COOKIE_DOMAIN=$HOSTNAME
export ROOMS_NODE_HOSTNAME=walkabout1.$HOSTNAME
export ROOMS_NODE_NAME=alpha
export ROOMS_MONGO_DBNAME=walkabout

./server.py
