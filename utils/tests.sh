#!/bin/bash

set -e
. "${BASH_SOURCE%/*}/common.sh"

docker exec "$(container app)" sh -c "FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py python -m pytest app/tests/ --disable-warnings"
