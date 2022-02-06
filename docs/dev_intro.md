# Developer's Introduction

## Overview 

ContentDB is a Python Flask webservice, with a PostgreSQL database.

To avoid blocking web requests, background jobs run as
[Celery](https://docs.celeryproject.org/en/stable/getting-started/introduction.html) tasks.


## Locations

### The App

The `app` directory contains the Python Flask application.

* `blueprints` contains all the Python code behind each endpoint. 
    A [blueprint](https://flask.palletsprojects.com/en/2.0.x/blueprints/) is a Flask construct to hold a set of endpoints.
* `templates` contains all the HTML templates used to generate responses. Each directory in here matches a director in blueprints.
* `models` contains all the Database table classes. ContentDB uses [SQLAlchemy](https://docs.sqlalchemy.org/en/14/) to interact with PostgreSQL.
* `flatpages` contains all the markdown user documentation, including `/help`.
* `public` contains files that should be added to the web server unedited. Examples include CSS libraries, images, and JS scripts.
* `scss` contains the stylesheet files, that are compiled into CSS.
* `tasks` contains the background tasks executed by [Celery](https://docs.celeryproject.org/en/stable/getting-started/introduction.html).
* `logic` is a collection of reusable functions. For example, shared code to create a release or edit a package is here.
* `tests` contains the Unit Tests and UI tests.
* `utils` contain generic Python utilities, for example common code to manage Flask requests.

There are also a number of Python files in the `app` directory. The most important one is `querybuilder.py`,
which is used to generate SQLAlachemy queries for packages and topics.

### Supporting directories

* `migrations` contains code to manage database updates.
* `translations` contains user-maintained translations / locales.
* `utils` contains bash scripts to aid development and deployment.


## How to find stuff

Generally, you want to start by finding the endpoint and then seeing the code it calls.

Endpoints are sensibly organised in `app/blueprints`. 

You can also use a file search. For example, to find the package edit endpoint, search for `.route("/packages/<author>/<name>/edit/")`.
