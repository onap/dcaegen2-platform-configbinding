# ============LICENSE_START=======================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.

from logging import getLogger, StreamHandler, Formatter
from logging.handlers import RotatingFileHandler
from os import makedirs
import datetime


LOGGER = getLogger("defaultlogger")


def _create_logger(name, logfile):
    """
    Create a RotatingFileHandler and a streamhandler for stdout
    https://docs.python.org/3/library/logging.handlers.html
    what's with the non-pythonic naming in these stdlib methods? Shameful.
    """
    logger = getLogger(name)
    file_handler = RotatingFileHandler(logfile,
                                       maxBytes=10000000, backupCount=2)  # 10 meg with one backup..
    formatter = Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.setLevel("DEBUG")
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def create_logger():
    """
    Public method to set the global logger, launched from Run
    """
    LOGFILE = "/opt/logs/log.log"
    makedirs("/opt/logs", exist_ok=True)
    open(LOGFILE, 'a').close()  # this is like "touch"
    global LOGGER
    LOGGER = _create_logger("config_binding_service", LOGFILE)


def utc():
    """gets current time in utc"""
    return datetime.datetime.utcnow()


def audit(raw_request, bts, xer, rcode, calling_mod, msg="n/a"):
    """
    write an EELF audit record per https://wiki.onap.org/download/attachments/1015849/ONAP%20application%20logging%20guidelines.pdf?api=v2
    %The audit fields implemented:

    1 BeginTimestamp                    Implemented (bts)
    2 EndTimestamp                      Auto Injected when this is called
    3 RequestID                         Implemented (xer)
    7 serviceName                       Implemented (from Req)
    9 StatusCode                        Auto injected based on rcode
    10 ResponseCode                     Implemented (rcode)
    15 Server IP address                Implemented (from Req)
    16 ElapsedTime                      Auto Injected (milliseconds)
    18 ClientIPaddress                  Implemented (from Req)
    19 class name                       Implemented (mod), though docs say OOP, I am using the python  module here
    20 Unused                           ...implemented....
    21-25 Custom                        n/a
    26 detailMessage                    Implemented (msg)
    """
    ets = utc()

    LOGGER.info("{bts}|{ets}|{xer}||||{path}||{status}|{rcode}|||||{servip}|{et}||{clientip}|{calling_mod}|||||||{msg}".format(
        bts=bts.isoformat(),
        ets=ets.isoformat(),
        xer=xer, rcode=rcode,
        path=raw_request.path.split("/")[1],
        status="COMPLETE" if rcode == 200 else "ERROR",
        servip=raw_request.host.split(":")[0],
        et=int((ets - bts).microseconds / 1000),  # supposed to be in milleseconds
        clientip=raw_request.remote_addr,
        calling_mod=calling_mod, msg=msg
    ))
