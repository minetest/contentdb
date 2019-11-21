#!/bin/bash

#
# Call from a docker host to build and start CDB.
#

sudo docker-compose up --build -d --scale worker=2
