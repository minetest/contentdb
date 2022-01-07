#!/bin/bash

pybabel extract -F babel.cfg -k lazy_gettext -o translations/messages.pot .
pybabel update -i translations/messages.pot -d translations