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

#443 is https, 10000 is http
# in the future, hopefully http can go away completely
ENV LISTEN_PORT 10000
EXPOSE 443
EXPOSE 10000

# Mount a self signed certificate that should be overwritten upon Run
RUN apt-get update && \
    apt-get install -y openssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt -subj "/C=US/ST=NJ/L=foo/O=ONAP/OU=ONAP/CN=configbinding"

#this is a registrator flag that tells it to ignore 80 from service discovery. Nothing is listening on 80, but the parent Dockerfile here exposes it. This container is internally listening on 10000 and 443. 
ENV SERVICE_80_IGNORE true
