FROM python:3.6

WORKDIR /home/cdb

COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt
RUN pip install gunicorn
RUN pip install psycopg2

COPY runprodguni.sh ./
COPY rundebug.sh ./
RUN chmod +x runprodguni.sh

COPY setup.py ./setup.py
COPY app app
COPY migrations migrations
COPY config.cfg ./config.cfg
