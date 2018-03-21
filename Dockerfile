FROM python:3.6
MAINTAINER tommy@research.att.com

ADD . /tmp

RUN pip install --upgrade pip 
WORKDIR /tmp
#do the install
RUN pip install .

EXPOSE 10000

RUN mkdir -p /opt/logs/

CMD run.py
