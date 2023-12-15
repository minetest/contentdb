#!/bin/bash

# Open SQL console for the database

set -e
. "${BASH_SOURCE%/*}/common.sh"

docker exec -it "$(container db)" psql contentdb contentdb
