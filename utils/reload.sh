#!/bin/bash

# Hot/live reload - only works in debug mode

set -e
. "${BASH_SOURCE%/*}/common.sh"

docker exec "$(container app)" sh -c "cp -r /source/* ."
