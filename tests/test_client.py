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

from config_binding_service import client, exceptions
import pytest


# pytest doesnt support objects in conftest
class FakeReq(object):
    """used to fake the logging params"""

    def __init__(self):
        self.path = "/unittest in {0}".format(__name__)
        self.host = "localhost"
        self.remote_addr = "6.6.6.6"


# pytest doesnt support objects in conftest
class FakeConnexion(object):
    def __init__(self, headers, path, host, remote_addr):
        self.headers = headers
        self.path = path
        self.host = host
        self.remote_addr = remote_addr


def test_consul_get_all_as_transaction(monkeypatch, monkeyed_requests_put):
    """tests _consul_get_all_as_transaction"""
    monkeypatch.setattr("requests.put", monkeyed_requests_put)
    allk = client._consul_get_all_as_transaction(
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org", FakeReq(), "unit test xer"
    )
    assert allk == {
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org": {"my": "amazing config"},
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti": {"my": "dti"},
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dmaap": {"foo": "bar"},
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/event": {
            "action": "gathered",
            "timestamp": "2018-02-19 15:36:44.877380",
            "update_id": "bb73c20a-5ff8-450f-8223-da6720ade267",
            "policies_count": 2,
        },
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_MS_alex_microservice": {
            "policyName": "DCAE_alex.Config_MS_alex_microservice.132.xml",
            "policyConfigMessage": "Config Retrieved! ",
            "responseAttributes": {},
            "policyConfigStatus": "CONFIG_RETRIEVED",
            "matchingConditions": {"ONAPName": "DCAE", "Name": "DCAE", "ConfigName": "alex_config_name"},
            "config": {
                "policyScope": "alex_policy_scope",
                "configName": "alex_config_name",
                "description": "test DCAE policy-handler",
                "service": "alex_service",
                "policyName": "alex_policy_name",
                "riskLevel": "3",
                "key1": "value1",
                "policy_hello": "world!",
                "content": {"foo": "microservice3", "foo_updated": "2018-01-30T13:25:33.222Z"},
                "riskType": "1712_ETE",
                "guard": "False",
                "version": "0.0.1",
                "location": "Central",
                "policy_updated_ts": "2018-02-19T15:09:55.217Z",
                "updated_policy_id": "DCAE_alex.Config_MS_alex_microservice",
                "policy_updated_to_ver": "132",
                "priority": "4",
                "policy_updated_from_ver": "131",
                "templateVersion": "2",
                "uuid": "5e87d7c5-0daf-4b6b-ab92-5365cf5db1ef",
            },
            "property": None,
            "type": "JSON",
            "policyVersion": "132",
        },
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_db_client_policy_id_value": {
            "policyName": "DCAE_alex.Config_db_client_policy_id_value.133.xml",
            "policyConfigMessage": "Config Retrieved! ",
            "responseAttributes": {},
            "policyConfigStatus": "CONFIG_RETRIEVED",
            "matchingConditions": {"ONAPName": "DCAE", "Name": "DCAE", "ConfigName": "alex_config_name"},
            "config": {
                "db_client_ts": "2017-11-21T12:12:13.696Z",
                "db_client": "ipsum",
                "policy_hello": "world!",
                "policy_updated_from_ver": "132",
                "updated_policy_id": "DCAE_alex.Config_db_client_policy_id_value",
                "policy_updated_ts": "2018-02-19T15:09:55.812Z",
                "policy_updated_to_ver": "133",
            },
            "property": None,
            "type": "JSON",
            "policyVersion": "133",
        },
        "test_service_component_name.unknown.unknown.unknown.dcae.onap.org:rels": ["my.amazing.relationship"],
    }

    allk = client._consul_get_all_as_transaction("cbs_test_messed_up", FakeReq(), "unit test xer")
    assert allk == {"cbs_test_messed_up": {"foo": "bar"}, "cbs_test_messed_up:badkey": "INVALID JSON"}


def test_get_config_rels_dmaap(monkeypatch, monkeyed_requests_put):
    monkeypatch.setattr("requests.put", monkeyed_requests_put)
    assert ({"foo3": "bar3"}, ["foo"], {"foo4": "bar4"}) == client._get_config_rels_dmaap(
        "scn_exists", FakeReq(), "unit test xer"
    )
    assert ({"foo5": "bar5"}, [], {}) == client._get_config_rels_dmaap("scn_exists_nord", FakeReq(), "unit test xer")


def test_bad_config_http():
    test_config = {"yeahhhhh": "{{}}"}
    test_rels = ["testing_bravo.somedomain.com"]
    assert {"yeahhhhh": []} == client.resolve_override(test_config, test_rels)


def test_bad_config_dmaap():
    test_config = {"darkness": "<<>>"}
    test_dmaap = {"WHO?": "darkness"}
    assert {"darkness": {}} == client.resolve_override(test_config, test_dmaap)


def test_config_with_list(monkeypatch, monkeyed_get_connection_info_from_consul):
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )
    test_config_1 = {
        "dcae_target_type": ["vhss-ems", "pcrf-oam"],
        "downstream-laika": "{{ laika }}",
        "some-param": "Lorem ipsum dolor sit amet",
    }
    test_rels_1 = ["3df5292249ae4a949f173063617cea8d_docker-snmp-polling-firstnet-m"]
    test_bind_1 = client.resolve_override(test_config_1, test_rels_1, {})
    assert test_bind_1 == {
        "dcae_target_type": ["vhss-ems", "pcrf-oam"],
        "downstream-laika": [],
        "some-param": "Lorem ipsum dolor sit amet",
    }

    test_config_2 = {"foo": ["{{cdap}}", "notouching", "<<yo>>"]}
    test_rels_2 = ["cdap"]
    test_dmaap_2 = {"yo": "im here"}
    test_bind_2 = client.resolve_override(test_config_2, test_rels_2, test_dmaap_2)
    assert test_bind_2 == {"foo": [["666.666.666.666:666"], "notouching", "im here"]}


def test_cdap(monkeypatch, monkeyed_get_connection_info_from_consul):
    # user override to test CDAP functionality
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )
    test_rels = [
        "testing_alpha.somedomain.com",
        "testing_bravo.somedomain.com",
        "testing_charlie.somedomain.com",
        "testing_charlie.somedomain.com",
        "cdap",
    ]
    test_config = {
        "streams_publishes": "{{alpha}}",
        # should be dumped
        "services_calls": [{"somekey": "{{charlie}}"}],
        "cdap_to_manage": {"some_nested_thing": "{{cdap}}"},
    }  # no dumps
    test_bind_1 = client.resolve_override(test_config, test_rels)
    assert test_bind_1 == {
        "services_calls": [{"somekey": ["5.5.5.5:555", "5.5.5.5:555"]}],
        "streams_publishes": ["6.6.6.6:666"],
        "cdap_to_manage": {"some_nested_thing": ["666.666.666.666:666"]},
    }
    assert test_bind_1["services_calls"] == [{"somekey": ["5.5.5.5:555", "5.5.5.5:555"]}]
    assert test_bind_1["streams_publishes"] == ["6.6.6.6:666"]


def test_multiple_service_types(monkeypatch, monkeyed_get_connection_info_from_consul):
    # test {{x,y,z}}
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )

    # test 1: they all resovle
    test_rels = [
        "testing_alpha.somedomain.com",
        "testing_bravo.somedomain.com",
        "testing_charlie.somedomain.com",
        "testing_charlie.somedomain.com",
    ]
    config = {"ALL YOUR SERVICE BELONG TO US": "{{alpha,bravo,charlie}}"}
    test_bind_1 = client.resolve_override(config, test_rels)
    assert test_bind_1 == {"ALL YOUR SERVICE BELONG TO US": ["6.6.6.6:666", "7.7.7.7:777", "5.5.5.5:555", "5.5.5.5:555"]}

    # test 2: two resolve, one is missing from rels key
    config2 = {"two there one not exist": "{{alpha,bravo,notexist}}"}
    test_bind_2 = client.resolve_override(config2, test_rels)
    assert test_bind_2 == {"two there one not exist": ["6.6.6.6:666", "7.7.7.7:777"]}

    # test 3: two resolve, one is in rels key but not registered
    config3 = {"two there one unregistered": "{{alpha,bravo,unregistered}}"}
    test_rels3 = ["testing_alpha.somedomain.com", "testing_bravo.somedomain.com", "unregistered.somedomain.com"]
    test_bind_3 = client.resolve_override(config3, test_rels3)
    assert test_bind_3 == {"two there one unregistered": ["6.6.6.6:666", "7.7.7.7:777"]}


def test_dmaap(monkeypatch):
    # test resolving dmaap key
    config = {"TODAY IS YOUR LUCKY DAY": "<<XXX>>"}
    # does not match
    test_bind = client.resolve_override(config, dmaap={"XX": "ABSOLVEME"})  # XX != XXX
    assert test_bind == {"TODAY IS YOUR LUCKY DAY": {}}
    # matches
    test_bind_2 = client.resolve_override(config, dmaap={"XXX": "ABSOLVEME"})
    assert test_bind_2 == {"TODAY IS YOUR LUCKY DAY": "ABSOLVEME"}


def test_config(monkeypatch, monkeyed_get_connection_info_from_consul):
    # test config override
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )
    test_config = {
        "autoderegisterafter": "10m",
        "cdap_to_manage": {"some_nested_thing": "{{cdap}}"},
        "bindingttw": 5,
        "hcinterval": "5s",
    }
    test_rels = ["cdap"]
    test_bind_1 = client.resolve_override(test_config, test_rels)
    assert test_bind_1 == {
        "autoderegisterafter": "10m",
        "cdap_to_manage": {"some_nested_thing": ["666.666.666.666:666"]},
        "bindingttw": 5,
        "hcinterval": "5s",
    }


def test_non_existent(monkeypatch, monkeyed_get_connection_info_from_consul):
    # test a valid config-rels but the key is not in Consul
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )
    test_config = {"you shall not be fufilled": "{{nonexistent_hope}}"}
    # hopefully not registered in Consul..
    test_rels = ["nonexistent_hope.rework-central.ecomp.somedomain.com"]
    test_bind_1 = client.resolve_override(test_config, test_rels, {})
    assert test_bind_1 == {"you shall not be fufilled": []}


def test_broker_redirect(monkeypatch, monkeyed_get_connection_info_from_consul):
    # test the broker redirect
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )
    test_config = {"gimmie_dat_cdap": "{{cdap_serv}}"}
    test_rels = ["cdap_serv.dcae.ecomp.somedomain.com"]
    assert {
        "gimmie_dat_cdap": ["http://1.1.1.1:444/application/cdap_serv.dcae.ecomp.somedomain.com"]
    } == client.resolve_override(test_config, test_rels)


def test_both(monkeypatch, monkeyed_get_connection_info_from_consul, expected_config):
    # test rels and http
    monkeypatch.setattr(
        "config_binding_service.client._get_connection_info_from_consul", monkeyed_get_connection_info_from_consul
    )
    test_rels = [
        "testing_alpha.somedomain.com",
        "testing_bravo.somedomain.com",
        "testing_charlie.somedomain.com",
        "testing_charlie.somedomain.com",
    ]
    test_dmaap = {"WHO?": "darkness"}
    config = {
        "deep": {"ALL YOUR SERVICE BELONG TO US": "{{alpha,bravo,charlie}}"},
        "doubledeep": {"sodeep": {"hello": "<<WHO?>>"}},
    }
    test_bind_1 = client.resolve_override(config, test_rels, test_dmaap)
    assert test_bind_1 == expected_config


def test_failures(monkeypatch, monkeyed_requests_put, monkeyed_requests_get):
    monkeypatch.setattr("requests.put", monkeyed_requests_put)
    monkeypatch.setattr("requests.get", monkeyed_requests_get)
    monkeypatch.setattr(
        "connexion.request",
        FakeConnexion({"x-onap-requestid": 123456789}, "/service_component", "mytestingmachine", "myremoteclient"),
    )
    assert client.resolve("scn_exists", FakeReq(), "unit test xer") == {"foo3": "bar3"}
    with pytest.raises(exceptions.CantGetConfig):
        client.resolve("scn_NOTexists", FakeReq(), "unit test xer")
        with pytest.raises(exceptions.CantGetConfig):
            client.get_key(
                "nokeyforyou",
                "test_service_component_name.unknown.unknown.unknown.dcae.onap.org",
                FakeReq(),
                "unit test xer",
            )
