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


LOGGER = getLogger("defaultlogger")


def _create_logger(name, logfile):
    """
    Create a RotatingFileHandker
    https://docs.python.org/3/library/logging.handlers.html
    what's with the non-pythonic naming in these stdlib methods? Shameful.
    """
    logger = getLogger(name)
    file_handler = RotatingFileHandler(logfile,
                                       maxBytes=10000000, backupCount=2)  # 10 meg with one backup..
    file_formatter = Formatter('%(asctime)s | %(name)s | %(module)s | %(funcName)s | %(lineno)d |  %(levelname)s | %(message)s')  # right now the same, but intending to change
    file_handler.setFormatter(file_formatter)

    stream_handler = StreamHandler()
    stream_formatter = Formatter('%(asctime)s | %(name)s | %(module)s | %(funcName)s | %(lineno)d |  %(levelname)s | %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.setLevel("DEBUG")  # a function is going to wrap this anyway
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
