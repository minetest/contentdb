#!/bin/sh

# Hot/live reload - only works in debug mode

docker exec contentdb_app_1 sh -c "cp -r /source/* ."
