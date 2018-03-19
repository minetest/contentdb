# Content Database

## Setup

First create a Python virtual env:

	virtualenv env
	source env/bin/activate

then use pip:

	pip install -r requirements.txt

## Running

You need to enter the virtual environment if you haven't yet in
the current session:

	source env/bin/activate

Reset the database like so:

	python setup.py -d

Then run the server:

	python rundebug.py

Then view in your web browser:

	http://localhost:5000/
