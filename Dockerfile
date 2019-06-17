FROM python:3.6-alpine
MAINTAINER tommy@research.att.com

COPY . /tmp
WORKDIR /tmp

EXPOSE 10000

# it is an ONAP requirement to make, and switch to, a non root user
ENV CBSUSER cbs
RUN addgroup -S $CBSUSER && adduser -S -G $CBSUSER $CBSUSER 

# create logs dir and install
# alpine does not come with GCC like the standard "python" docker base does, which the install needs, see https://wiki.alpinelinux.org/wiki/GCC
RUN apk add build-base && \ 
    mkdir -p /opt/logs/ && \
    chown $CBSUSER:$CBSUSER /opt/logs && \
    pip install --upgrade pip && \
    pip install .

# turn on file based EELF logging
ENV PROD_LOGGING 1

# Run the application
USER $CBSUSER
CMD run.py
