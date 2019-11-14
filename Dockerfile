FROM python:3.6

WORKDIR /home/cdb

COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt
RUN pip install gunicorn

COPY utils utils
COPY app app
COPY migrations migrations
COPY config.cfg ./config.cfg
