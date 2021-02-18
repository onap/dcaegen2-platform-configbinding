FROM nexus3.onap.org:10001/onap/integration-python:8.0.0
MAINTAINER tommy@research.att.com

EXPOSE 10000

# it is an ONAP requirement to make, and switch to, a non root user
ARG user=onap
ARG group=onap

USER root
RUN mkdir -p /home/$user && \
    chown -R $user:$group /home/$user &&  \
    mkdir -p /var/log/$user && \
    chown -R $user:$group /var/log/$user && \
    mkdir -p /app && \
    chown -R $user:$group /app
WORKDIR /app

COPY . /app

# alpine does not come with GCC like the standard "python" docker base does, which the install needs, see https://wiki.alpinelinux.org/wiki/GCC
RUN apk add build-base libffi-dev && \ 
    pip install --upgrade pip && \
    pip install .

# turn on file based EELF logging
ENV PROD_LOGGING 1

# Run the application
USER $user
CMD run.py
