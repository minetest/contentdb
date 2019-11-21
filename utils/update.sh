#!/bin/bash

#
# Call from a docker host to rebuild and update running instances of CDB.
#

sudo docker-compose build app
sudo docker-compose build worker

sudo docker-compose up --no-deps -d app
sudo docker-compose up --no-deps --scale worker=2 -d worker
