#!/bin/bash

# Open SSH to app instance

set -e
. "${BASH_SOURCE%/*}/common.sh"

docker exec -it "$(container app)" bash
