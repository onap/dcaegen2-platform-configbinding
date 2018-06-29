FROM tiangolo/uwsgi-nginx-flask:python3.6
MAINTAINER tommy@research.att.com

#setup uwsgi+nginx 
# https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
COPY ./app /app

RUN pip install --upgrade pip
RUN pip install /app/app

RUN mkdir -p /opt/logs/

# create the dir for the ssl certs
RUN mkdir -p /etc/nginx/ssl

COPY nginxhttps.conf /etc/nginx/conf.d/nginxhttps.conf

ENV LISTEN_PORT 10000
EXPOSE 443
EXPOSE 10000

#this is a registrator flag that tells it to ignore 80 from service discovery. Nothing is listening on 80, but the parent Dockerfile here exposes it. This container is internally listening on 10000 and 443. 
ENV SERVICE_80_IGNORE true
