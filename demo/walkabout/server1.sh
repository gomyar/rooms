#!/bin/bash

export ROOMS_NODE_HOSTNAME=walkabout1.$HOSTNAME
export ROOMS_NODE_NAME=alpha
export ROOMS_MONGO_DBNAME=walkabout

./server.py
