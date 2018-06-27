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

import json
import pytest
from config_binding_service import client, controller


# pytest doesnt support objects in conftest yet
class FakeConnexion(object):
    def __init__(self, headers, path, host, remote_addr):
        self.headers = headers
        self.path = path
        self.host = host
        self.remote_addr = remote_addr


def test_bind_config_for_scn(monkeypatch, monkeyed_requests_put):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    monkeypatch.setattr('connexion.request', FakeConnexion({"x-onap-requestid": 123456789}, "/service_component", "mytestingmachine", "myremoteclient"))

    assert(client.resolve("scn_exists") == {"foo3": "bar3"})
    with pytest.raises(client.CantGetConfig):
        client.resolve("scn_NOTexists")

    R = controller.bind_config_for_scn("scn_exists")
    assert(json.loads(R.data) == {"foo3": "bar3"})
    assert(R.status_code == 200)
    assert(R.headers["x-onap-requestid"] == "123456789")

    R = controller.bind_config_for_scn("scn_NOTexists")
    assert(R.status_code == 404)
    assert(R.headers["x-onap-requestid"] == "123456789")

    R = controller.bind_config_for_scn("asdfasdf")
    assert(R.status_code == 500)
    assert(R.headers["x-onap-requestid"] == "123456789")


def test_generic(monkeypatch, monkeyed_requests_get, monkeyed_requests_put):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    monkeypatch.setattr('requests.get', monkeyed_requests_get)
    assert client.get_key("dti", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org") == json.loads('{"my": "dti"}')
    with pytest.raises(client.CantGetConfig):
        client.get_key(
            "nokeyforyou", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")

    monkeypatch.setattr('connexion.request', FakeConnexion({}, "/get_key", "mytestingmachine", "myremoteclient"))

    R = controller.get_key(
        "dti", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(json.loads(R.data) == {"my": "dti"})
    assert(R.status_code == 200)
    assert "x-onap-requestid" in R.headers

    R = controller.get_key(
        "nokeyforyou", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(R.status_code == 404)
    assert "x-onap-requestid" in R.headers

    R = controller.get_key(
        "policies", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(R.status_code == 400)
    assert "x-onap-requestid" in R.headers


def test_resolve_all(monkeypatch, monkeyed_requests_put, monkeyed_get_connection_info_from_consul, expected_config):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    allk = client.resolve_all(
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    withstuff = {'config': {'my': 'amazing config'},
                 'dti': {'my': 'dti'},
                 'policies': {'items': [{'policyName': 'DCAE_alex.Config_MS_alex_microservice.132.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'policyScope': 'alex_policy_scope', 'configName': 'alex_config_name', 'description': 'test DCAE policy-handler', 'service': 'alex_service', 'policyName': 'alex_policy_name', 'riskLevel': '3', 'key1': 'value1', 'policy_hello': 'world!', 'content': {'foo': 'microservice3', 'foo_updated': '2018-01-30T13:25:33.222Z'}, 'riskType': '1712_ETE', 'guard': 'False', 'version': '0.0.1', 'location': 'Central', 'policy_updated_ts': '2018-02-19T15:09:55.217Z', 'updated_policy_id': 'DCAE_alex.Config_MS_alex_microservice', 'policy_updated_to_ver': '132', 'priority': '4', 'policy_updated_from_ver': '131', 'templateVersion': '2', 'uuid': '5e87d7c5-0daf-4b6b-ab92-5365cf5db1ef'}, 'property': None, 'type': 'JSON', 'policyVersion': '132'}, {'policyName': 'DCAE_alex.Config_db_client_policy_id_value.133.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'db_client_ts': '2017-11-21T12:12:13.696Z', 'db_client': 'ipsum', 'policy_hello': 'world!', 'policy_updated_from_ver': '132', 'updated_policy_id': 'DCAE_alex.Config_db_client_policy_id_value', 'policy_updated_ts': '2018-02-19T15:09:55.812Z', 'policy_updated_to_ver': '133'}, 'property': None, 'type': 'JSON', 'policyVersion': '133'}], 'event': {'action': 'gathered', 'timestamp': '2018-02-19 15:36:44.877380', 'update_id': 'bb73c20a-5ff8-450f-8223-da6720ade267', 'policies_count': 2}}}
    assert allk == withstuff

    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul',
                        monkeyed_get_connection_info_from_consul)
    allk = client.resolve_all("test_resolve_scn")
    assert allk == {"config": expected_config}

    monkeypatch.setattr('connexion.request', FakeConnexion({}, "/service_component_all", "mytestingmachine", "myremoteclient"))

    R = controller.bind_all(
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(json.loads(R.data) == withstuff)
    assert(R.status_code == 200)
    assert "x-onap-requestid" in R.headers

    R = controller.bind_all("test_resolve_scn")
    assert(json.loads(R.data) == {"config": expected_config})
    assert(R.status_code == 200)

    R = controller.bind_all("scn_NOTexists")
    assert(R.status_code == 404)
    assert "x-onap-requestid" in R.headers

    R = controller.bind_all("asdfasdf")
    assert(R.status_code == 500)
