#!/bin/bash

# Debug
# FLASK_APP=app/__init__.py FLASK_CONFIG=../config.cfg FLASK_DEBUG=1 python3 -m flask run -h 0.0.0.0 -p 5123

if [ -z "$FLASK_DEBUG" ]; then
	echo "FLASK_DEBUG is required in config.env"
	exit 1
fi

gunicorn -w 4 -b :5123 -e FLASK_APP=app/__init__.py -e FLASK_CONFIG=../config.cfg -e FLASK_DEBUG=$FLASK_DEBUG app:app
