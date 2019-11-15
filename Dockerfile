FROM python:3.6

RUN groupadd -g 5123 cdb && \
    useradd -r -u 5123 -g cdb cdb

WORKDIR /home/cdb

COPY requirements.txt requirements.txt
RUN pip install -r ./requirements.txt
RUN pip install gunicorn

COPY utils utils
COPY config.cfg ./config.cfg
COPY migrations migrations
COPY app app

RUN mkdir /home/cdb/app/public/uploads/
RUN chown cdb:cdb /home/cdb -R
USER cdb
