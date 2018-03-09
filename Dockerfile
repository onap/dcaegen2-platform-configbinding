FROM python:3.6
MAINTAINER tommy@research.att.com

ADD . /tmp

#need pip > 8 to have internal pypi repo in requirements.txt
RUN pip install --upgrade pip 
#do the install
WORKDIR /tmp
RUN pip install -e .

EXPOSE 10000

RUN mkdir -p /opt/logs/

CMD run.py
