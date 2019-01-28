#!/bin/bash

gunicorn -w 4 -b :5123 -e FLASK_APP=app/__init__.py -e FLASK_CONFIG=../config.prod.cfg -e FLASK_DEBUG=1 app:app
