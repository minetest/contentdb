#!/bin/bash

pybabel extract -F babel.cfg -o translations/messages.pot .
pybabel update -i translations/messages.pot -d translations