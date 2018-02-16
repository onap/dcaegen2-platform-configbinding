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

import os
import logging

'''Configures the module root logger'''
root = logging.getLogger()
if root.handlers:
    root.handlers.clear()
formatter = logging.Formatter('%(asctime)s | %(name)s | %(module)s | %(funcName)s | %(lineno)d |  %(levelname)s | %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
root.addHandler(handler)
root.setLevel("DEBUG")

class BadEnviornmentENVNotFound(Exception):
    pass

def get_logger(module=None):
    '''Returns a module-specific logger or global logger if the module is None'''
    return root if module is None else root.getChild(module)

def get_consul_uri():
    """
    This method waterfalls reads an envioronmental variable called CONSUL_HOST
    If that doesn't work, it raises an Exception
    """
    if "CONSUL_HOST" in os.environ:
        # WARNING! TODO! Currently the env file does not include the port.
        # But some other people think that the port should be a part of that.
        # For now, I'm hardcoding 8500 until this gets resolved.
        return "http://{0}:{1}".format(os.environ["CONSUL_HOST"], 8500)
    else:
        raise BadEnviornmentENVNotFound("CONSUL_HOST")


