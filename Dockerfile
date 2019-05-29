FROM python:3.6
MAINTAINER tommy@research.att.com

COPY . /tmp
WORKDIR /tmp

RUN pip install --upgrade pip
RUN pip install . 
RUN mkdir -p /opt/logs/
EXPOSE 10000

ENV PROD_LOGGING 1

CMD run.py
