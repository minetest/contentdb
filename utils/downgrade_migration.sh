#!/bin/sh

# Create a database migration, and copy it back to the host.

docker exec contentdb_app_1 sh -c "FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py flask db downgrade"
