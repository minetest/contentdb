#!/bin/bash

#
# Call from a docker host to build and start CDB.
#   This is really only for production mode, for debugging it's better to use
#   docker-compose directly:  docker-compose up --build
#

sudo docker-compose up --build -d --scale worker=2
