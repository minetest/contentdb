# Content Database

## Setup

First create a Python virtual env:

	virtualenv env
	source env/bin/activate

then use pip:

	pip3 install -r requirements.txt

## Running

You need to enter the virtual environment if you haven't yet in
the current session:

	source env/bin/activate

Reset the database like so:

	python3 setup.py -d

Then run the server:

	python3 rundebug.py

Then view in your web browser: http://localhost:5000/
