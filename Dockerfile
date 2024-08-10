FROM python:3.10.11-alpine

RUN addgroup --gid 5123 cdb && \
    adduser --uid 5123 -S cdb -G cdb

WORKDIR /home/cdb

RUN \
	apk add --no-cache postgresql-libs git bash && \
	apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev g++

RUN mkdir /var/cdb
RUN chown -R cdb:cdb /var/cdb

COPY requirements.lock.txt requirements.lock.txt
RUN pip install -r requirements.lock.txt && \
	pip install gunicorn

COPY utils utils
COPY config.cfg config.cfg
COPY migrations migrations
COPY app app
COPY translations translations

RUN pybabel compile -d translations
RUN chown -R cdb:cdb /home/cdb

USER cdb
