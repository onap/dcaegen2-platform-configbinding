FROM tiangolo/uwsgi-nginx-flask:python3.6
MAINTAINER tommy@research.att.com

#setup uwsgi+nginx 
# https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
COPY ./app /app

RUN pip install --upgrade pip
RUN pip install /app/app

RUN mkdir -p /opt/logs/

ENV LISTEN_PORT 10000 
