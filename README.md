# Content Database
[![Build status](https://gitlab.com/minetest/contentdb/badges/master/pipeline.svg)](https://gitlab.com/minetest/contentdb/pipelines)

Content database for Minetest mods, games, and more.\
Developed by rubenwardy, license GPLv3.0+.

## Getting started (debug/dev)

Docker is the recommended way to develop and deploy ContentDB.

1. Install `docker` and `docker-compose`.

		sudo apt install docker-ce docker-compose

2. Copy `config.example.cfg` to `config.cfg`.

3. (Optional) Set up mail in config.cfg.
   Make sure to set `USER_ENABLE_EMAIL` to True.

4. (Optional) Set up GitHub integration
	1. Make a Github OAuth Client at <https://github.com/settings/developers>:
	2. Homepage URL - `http://localhost:5123/`
	3. Authorization callback URL - `http://localhost:5123/user/github/callback/`
	4. Put client id and client secret in `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in config.cfg.

5. Create config.env:

		POSTGRES_USER=contentdb
		POSTGRES_PASSWORD=password
		POSTGRES_DB=contentdb
		FLASK_DEBUG=1

6. Start docker images:

		docker-compose up --build

7. Setup database:

		./utils/run_migrations.sh

8. Create initial data
	1. `./utils/bash.sh`
	2. Either `python setup.py -t` or `python setup.py -o`:
	  	1. `-o` creates just the admin, and static data like tags, and licenses.
	  	2. `-t` will do `-o` and also create test packages. (Recommended)

9. View at <http://localhost:5123>.
   The admin username is `rubenwardy` and the password is `tuckfrump`.

In the future, starting CDB is as simple as:

	docker-compose up --build

To hot/live update CDB whilst it is running, use:

	./utils/reload.sh

This will only work with python code and templates, it won't update tasks or config.


## How-tos

```sh
# Hot/live reload (only works with FLASK_DEBUG=1)
./utils/reload.sh

# Cold update a running version of CDB with minimal downtime (production)
./utils/update.sh

# Enter docker
./utils/bash.sh

# Run migrations
./utils/run_migrations.sh

# Create new migration
./utils/create_migration.sh
```


### VSCode: Setting up Linting

* (optional) Install the [Docker extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)
* Install the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
	* Click no to installing pylint (we don't want it to be installed outside of a virtual env)
* Set up a virtual env
	* Replace `psycopg2` with `psycopg2_binary` in requirements.txt (because postgresql won't be installed on the system)
	* `python3 -m venv env`
	* Click yes to prompt to select virtual env for workspace
	* Click yes to any prompts about installing pylint
	* `source env/bin/activate`
	* `pip install -r requirements`
	* `pip install pylint` (if a prompt didn't appear)
	* Undo changes to requirements.txt

### VSCode: Material Icon Folder Designations

```json
"material-icon-theme.folders.associations": {
	"packages": "",
	"tasks": "",
	"api": "",
	"meta": "",
	"blueprints": "routes",
	"scss": "sass",
	"flatpages": "markdown",
	"data": "temp",
	"migrations": "archive",
	"textures": "images",
	"sounds": "audio"
}
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
