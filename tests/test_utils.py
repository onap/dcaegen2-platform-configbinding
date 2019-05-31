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
import pytest
from config_binding_service import utils, exceptions
import os


def test_https_flags(monkeypatch):
    """test getting https flags"""
    key_loc, cert_loc = utils.get_https_envs()
    assert key_loc is None and cert_loc is None

    monkeypatch.setenv("USE_HTTPS", "1")
    with pytest.raises(exceptions.BadHTTPSEnvs):
        utils.get_https_envs()

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    monkeypatch.setenv("HTTPS_KEY_PATH", "{0}/fixtures/test_k.key".format(cur_dir))
    monkeypatch.setenv("HTTPS_CERT_PATH", "{0}/fixtures/NONEXISTENT".format(cur_dir))
    with pytest.raises(exceptions.BadHTTPSEnvs):
        utils.get_https_envs()

    monkeypatch.setenv("HTTPS_CERT_PATH", "{0}/fixtures/test_c.crt".format(cur_dir))
    key_loc, cert_loc = utils.get_https_envs()
    assert key_loc is not None
    assert cert_loc is not None
