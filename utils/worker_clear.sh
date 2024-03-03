#!/bin/bash

# Clear worker queue

set -e
. "${BASH_SOURCE%/*}/common.sh"

docker exec -it "$(container app)" sh -c "FLASK_CONFIG=../config.cfg celery -A app.tasks.celery purge -f"
