#!/bin/bash

#
# Call from a docker host to rebuild and update running instances of CDB.
#    This is for production use. See reload.sh for debug mode hot/live reloading.
#

sudo docker-compose build app
sudo docker-compose build worker

sudo docker-compose up --no-deps -d app
sudo docker-compose up --no-deps --scale worker=2 -d worker
