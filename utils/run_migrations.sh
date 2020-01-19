#!/bin/sh

# Run all pending migrations

docker exec contentdb_app_1 sh -c "FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py flask db upgrade"
