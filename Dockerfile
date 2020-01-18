FROM python:3.6

RUN groupadd -g 5123 cdb && \
    useradd -r -u 5123 -g cdb cdb

WORKDIR /home/cdb

RUN mkdir /var/cdb
RUN chown -R cdb:cdb /var/cdb

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY utils utils
COPY config.cfg config.cfg
COPY migrations migrations
COPY app app

RUN chown -R cdb:cdb /home/cdb

USER cdb
