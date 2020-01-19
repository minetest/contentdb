#!/bin/sh

# Open SQL console for the database

docker exec -it contentdb_db_1 sh -c "psql contentdb contentdb"
