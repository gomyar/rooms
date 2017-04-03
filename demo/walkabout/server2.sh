#!/bin/bash

export ROOMS_NODE_HOSTNAME=app2.$HOSTNAME
export ROOMS_NODE_NAME=beta
export ROOMS_NODE_PORT=5001
export ROOMS_MONGO_DBNAME=walkabout

./server.py
