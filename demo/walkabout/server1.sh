#!/bin/bash

export ROOMS_NODE_HOSTNAME=app1.$HOSTNAME
export ROOMS_NODE_NAME=alpha
export ROOMS_MONGO_DBNAME=walkabout

./server.py
