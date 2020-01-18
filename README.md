# Content Database

Content database for Minetest mods, games, and more.

Developed by rubenwardy, license GPLv3.0+.

## How-tos

Note: you should first read one of the guides on the [Github repo wiki](https://github.com/minetest/contentdb/wiki)

```sh
# Run celery worker
FLASK_CONFIG=../config.cfg celery -A app.tasks.celery worker

# if sqlite
python utils/setup.py -t
rm db.sqlite && python setup.py -t && FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py flask db stamp head

# Create migration
FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py flask db migrate
# Run migration
FLASK_CONFIG=../config.cfg FLASK_APP=app/__init__.py flask db upgrade

# Enter docker
docker exec -it contentdb_app_1 bash

# Hot/live reload (only works with FLASK_DEBUG=1)
./utils/reload.sh

# Cold update a running version of CDB with minimal downtime
./utils/update.sh
```

## Database


```mermaid
classDiagram

User "1" --> "*" Package
User --> UserEmailVerification
User "1" --> "*" Notification
Package "1" --> "*" Release
Package "1" --> "*" Dependency
Package "1" --> "*" Tag
Package "1" --> "*" MetaPackage : provides
Release --> MinetestVersion
Package --> License
Dependency --> Package
Dependency --> MetaPackage
MetaPackage "1" --> "*" Package
Package "1" --> "*" Screenshot
Package "1" --> "*" Thread
Thread "1" --> "*" Reply
Thread "1" --> "*" User : watchers
User "1" --> "*" Thread
User "1" --> "*" Reply
User "1" --> "*" ForumTopic

User --> "0..1" EmailPreferences
User "1" --> "*" APIToken
APIToken --> Package
```
