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
import json
import pytest
import os
import tempfile
from config_binding_service import app


TEST_NAME = "test_service_component_name.unknown.unknown.unknown.dcae.onap.org"


# http://flask.pocoo.org/docs/1.0/testing/
@pytest.fixture
def cbsclient():
    db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    testclient = app.app.test_client()

    yield testclient

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE'])


def test_get(monkeypatch, cbsclient, monkeyed_requests_put):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)

    res = cbsclient.get('/service_component/scn_exists',
                        headers={"x-onap-requestid": 123456789})
    assert(json.loads(res.data) == {"foo3": "bar3"})
    assert(res.status_code == 200)
    assert(res.headers["x-onap-requestid"] == "123456789")

    res = cbsclient.get('/service_component/scn_NOTexists',
                        headers={"x-onap-requestid": 123456789})
    assert(res.status_code == 404)
    assert(res.headers["x-onap-requestid"] == "123456789")

    res = cbsclient.get('/service_component/asdfasdf',
                        headers={"x-onap-requestid": 123456789})
    assert(res.status_code == 500)
    assert(res.headers["x-onap-requestid"] == "123456789")


def test_generic(monkeypatch, cbsclient, monkeyed_requests_get, monkeyed_requests_put):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    monkeypatch.setattr('requests.get', monkeyed_requests_get)

    res = cbsclient.get('/dti/{0}'.format(TEST_NAME))
    assert json.loads(res.data) == {"my": "dti"}
    assert res.json == {"my": "dti"}
    assert res.status_code == 200
    assert "x-onap-requestid" in res.headers

    res = cbsclient.get('/nokeyforyou/{0}'.format(TEST_NAME))
    assert res.status_code == 404
    assert "x-onap-requestid" in res.headers

    res = cbsclient.get('/policies/{0}'.format(TEST_NAME))
    assert res.status_code == 400
    assert "x-onap-requestid" in res.headers


def test_resolve_all(monkeypatch, cbsclient, monkeyed_requests_put, monkeyed_get_connection_info_from_consul, expected_config):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    withstuff = {'config': {'my': 'amazing config'},
                 'dti': {'my': 'dti'},
                 'policies': {'items': [{'policyName': 'DCAE_alex.Config_MS_alex_microservice.132.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'policyScope': 'alex_policy_scope', 'configName': 'alex_config_name', 'description': 'test DCAE policy-handler', 'service': 'alex_service', 'policyName': 'alex_policy_name', 'riskLevel': '3', 'key1': 'value1', 'policy_hello': 'world!', 'content': {'foo': 'microservice3', 'foo_updated': '2018-01-30T13:25:33.222Z'}, 'riskType': '1712_ETE', 'guard': 'False', 'version': '0.0.1', 'location': 'Central', 'policy_updated_ts': '2018-02-19T15:09:55.217Z', 'updated_policy_id': 'DCAE_alex.Config_MS_alex_microservice', 'policy_updated_to_ver': '132', 'priority': '4', 'policy_updated_from_ver': '131', 'templateVersion': '2', 'uuid': '5e87d7c5-0daf-4b6b-ab92-5365cf5db1ef'}, 'property': None, 'type': 'JSON', 'policyVersion': '132'}, {'policyName': 'DCAE_alex.Config_db_client_policy_id_value.133.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'db_client_ts': '2017-11-21T12:12:13.696Z', 'db_client': 'ipsum', 'policy_hello': 'world!', 'policy_updated_from_ver': '132', 'updated_policy_id': 'DCAE_alex.Config_db_client_policy_id_value', 'policy_updated_ts': '2018-02-19T15:09:55.812Z', 'policy_updated_to_ver': '133'}, 'property': None, 'type': 'JSON', 'policyVersion': '133'}], 'event': {'action': 'gathered', 'timestamp': '2018-02-19 15:36:44.877380', 'update_id': 'bb73c20a-5ff8-450f-8223-da6720ade267', 'policies_count': 2}}}

    assert cbsclient.get('service_component_all/{0}'.format(TEST_NAME)).json == withstuff

    assert cbsclient.get('service_component_all/test_resolve_scn').json == {"config": expected_config}

    res = cbsclient.get('/service_component_all/{0}'.format(TEST_NAME))
    assert json.loads(res.data) == withstuff
    assert res.json == withstuff
    assert res.status_code == 200
    assert "x-onap-requestid" in res.headers

    res = cbsclient.get('/service_component_all/test_resolve_scn')
    assert res.status_code == 200
    assert res.json == {"config": expected_config}

    res = cbsclient.get('/service_component_all/scn_NOTexists')
    assert res.status_code == 404
    assert "x-onap-requestid" in res.headers
