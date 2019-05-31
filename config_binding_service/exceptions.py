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


class BadHTTPSEnvs(BaseException):
    """
    used for bad http setup
    """

    pass


class CantGetConfig(Exception):
    """
    Represents an exception where a required key in consul isn't there
    """

    def __init__(self, code, response):
        self.code = code
        self.response = response


class BadRequest(Exception):
    """
    Exception to be raised when the user tried to do something they shouldn't
    """

    def __init__(self, response):
        self.code = 400
        self.response = response
