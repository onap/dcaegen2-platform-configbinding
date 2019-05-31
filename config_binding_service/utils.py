# ============LICENSE_START=======================================================
# Copyright (c) 2017-2019 AT&T Intellectual Property. All rights reserved.
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
from config_binding_service import exceptions


def get_https_envs():
    if "USE_HTTPS" in os.environ and os.environ["USE_HTTPS"] == "1":
        try:
            key_loc = os.environ["HTTPS_KEY_PATH"]
            cert_loc = os.environ["HTTPS_CERT_PATH"]
            # We check whether both these files exist. Future fail fast optimization: check that they're valid too
            if not (os.path.isfile(key_loc) and os.path.isfile(cert_loc)):
                raise exceptions.BadHTTPSEnvs()
            return key_loc, cert_loc
        except KeyError:
            raise exceptions.BadHTTPSEnvs()
    return None, None
