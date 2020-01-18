#!/bin/bash

# Hot/live reload - only works in debug mode

docker exec -it contentdb_app_1 sh -c "cp -r /source/* ."
