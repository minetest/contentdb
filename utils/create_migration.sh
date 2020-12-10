#!/bin/sh

# Create a database migration, and copy it back to the host.

docker exec contentdb_app_1 sh -c "FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py flask db revision"
docker exec -u root contentdb_app_1 sh -c "cp /home/cdb/migrations/versions/* /source/migrations/versions/"

USER=$(whoami)
sudo chown -R $USER:$USER migrations/versions
