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

import pytest
import json
from requests.exceptions import HTTPError
from config_binding_service import get_consul_uri
from config_binding_service import client, controller


#####
# MONKEYPATCHES
#####


def monkeyed_get_connection_info_from_consul(service_component_name):
    #shared monkeypatch. probably somewhat lazy because the function htis patches can be broken up.
    if service_component_name == "cdap":
        return '666.666.666.666:666'
    elif service_component_name == "testing_bravo.somedomain.com":
        return '7.7.7.7:777'
    elif service_component_name == "testing_alpha.somedomain.com":
        return '6.6.6.6:666'
    elif service_component_name == "testing_charlie.somedomain.com":
        return '5.5.5.5:555'
    elif service_component_name == "nonexistent_hope":
        return None #the real function returns None here
    elif service_component_name == "cdap_serv.dcae.ecomp.somedomain.com":
        broker_ip = '1.1.1.1'
        broker_port = 444
        return "http://{0}:{1}/application/{2}".format(broker_ip, broker_port, service_component_name)


class FakeResponse():
    def __init__(self, status_code, text):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(response=FakeResponse(404, ""))


def monkeyed_requests_get(url):
    if url == "{0}/v1/kv/test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti".format(get_consul_uri()):
        return FakeResponse(status_code=200, text='[{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti","Flags":0,"Value":          "eyJteSIgOiAiZHRpIn0=","CreateIndex":4066524,"ModifyIndex":4066524}]')
    else:
        return FakeResponse(status_code=404, text="")


def monkeyed_requests_put(url, json):
    if url == "{0}/v1/txn".format(get_consul_uri()):
        key = json[0]["KV"]["Key"]
        if key == "test_service_component_name.unknown.unknown.unknown.dcae.onap.org":
            return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org","Flags":0,"Value":"eyJteSIgOiAiYW1hemluZyBjb25maWcifQ==","CreateIndex":4051555,"ModifyIndex":4051555}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dmaap","Flags":0,"Value":"eyJmb28iIDogImJhciJ9","CreateIndex":4051571,"ModifyIndex":4051571}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti","Flags":0,"Value":"eyJteSIgOiAiZHRpIn0=","CreateIndex":4066524,"ModifyIndex":4066524}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/event","Flags":0,"Value":"eyJhY3Rpb24iOiAiZ2F0aGVyZWQiLCAidGltZXN0YW1wIjogIjIwMTgtMDItMTkgMTU6MzY6NDQuODc3MzgwIiwgInVwZGF0ZV9pZCI6ICJiYjczYzIwYS01ZmY4LTQ1MGYtODIyMy1kYTY3MjBhZGUyNjciLCAicG9saWNpZXNfY291bnQiOiAyfQ==","CreateIndex":4048564,"ModifyIndex":4048564}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_MS_alex_microservice","Flags":0,"Value":"eyJwb2xpY3lOYW1lIjogIkRDQUVfYWxleC5Db25maWdfTVNfYWxleF9taWNyb3NlcnZpY2UuMTMyLnhtbCIsICJwb2xpY3lDb25maWdNZXNzYWdlIjogIkNvbmZpZyBSZXRyaWV2ZWQhICIsICJyZXNwb25zZUF0dHJpYnV0ZXMiOiB7fSwgInBvbGljeUNvbmZpZ1N0YXR1cyI6ICJDT05GSUdfUkVUUklFVkVEIiwgIm1hdGNoaW5nQ29uZGl0aW9ucyI6IHsiT05BUE5hbWUiOiAiRENBRSIsICJOYW1lIjogIkRDQUUiLCAiQ29uZmlnTmFtZSI6ICJhbGV4X2NvbmZpZ19uYW1lIn0sICJjb25maWciOiB7InBvbGljeVNjb3BlIjogImFsZXhfcG9saWN5X3Njb3BlIiwgImNvbmZpZ05hbWUiOiAiYWxleF9jb25maWdfbmFtZSIsICJkZXNjcmlwdGlvbiI6ICJ0ZXN0IERDQUUgcG9saWN5LWhhbmRsZXIiLCAic2VydmljZSI6ICJhbGV4X3NlcnZpY2UiLCAicG9saWN5TmFtZSI6ICJhbGV4X3BvbGljeV9uYW1lIiwgInJpc2tMZXZlbCI6ICIzIiwgImtleTEiOiAidmFsdWUxIiwgInBvbGljeV9oZWxsbyI6ICJ3b3JsZCEiLCAiY29udGVudCI6IHsiZm9vIjogIm1pY3Jvc2VydmljZTMiLCAiZm9vX3VwZGF0ZWQiOiAiMjAxOC0wMS0zMFQxMzoyNTozMy4yMjJaIn0sICJyaXNrVHlwZSI6ICIxNzEyX0VURSIsICJndWFyZCI6ICJGYWxzZSIsICJ2ZXJzaW9uIjogIjAuMC4xIiwgImxvY2F0aW9uIjogIkNlbnRyYWwiLCAicG9saWN5X3VwZGF0ZWRfdHMiOiAiMjAxOC0wMi0xOVQxNTowOTo1NS4yMTdaIiwgInVwZGF0ZWRfcG9saWN5X2lkIjogIkRDQUVfYWxleC5Db25maWdfTVNfYWxleF9taWNyb3NlcnZpY2UiLCAicG9saWN5X3VwZGF0ZWRfdG9fdmVyIjogIjEzMiIsICJwcmlvcml0eSI6ICI0IiwgInBvbGljeV91cGRhdGVkX2Zyb21fdmVyIjogIjEzMSIsICJ0ZW1wbGF0ZVZlcnNpb24iOiAiMiIsICJ1dWlkIjogIjVlODdkN2M1LTBkYWYtNGI2Yi1hYjkyLTUzNjVjZjVkYjFlZiJ9LCAicHJvcGVydHkiOiBudWxsLCAidHlwZSI6ICJKU09OIiwgInBvbGljeVZlcnNpb24iOiAiMTMyIn0=","CreateIndex":4048564,"ModifyIndex":4065574}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_db_client_policy_id_value","Flags":0,"Value":"eyJwb2xpY3lOYW1lIjogIkRDQUVfYWxleC5Db25maWdfZGJfY2xpZW50X3BvbGljeV9pZF92YWx1ZS4xMzMueG1sIiwgInBvbGljeUNvbmZpZ01lc3NhZ2UiOiAiQ29uZmlnIFJldHJpZXZlZCEgIiwgInJlc3BvbnNlQXR0cmlidXRlcyI6IHt9LCAicG9saWN5Q29uZmlnU3RhdHVzIjogIkNPTkZJR19SRVRSSUVWRUQiLCAibWF0Y2hpbmdDb25kaXRpb25zIjogeyJPTkFQTmFtZSI6ICJEQ0FFIiwgIk5hbWUiOiAiRENBRSIsICJDb25maWdOYW1lIjogImFsZXhfY29uZmlnX25hbWUifSwgImNvbmZpZyI6IHsiZGJfY2xpZW50X3RzIjogIjIwMTctMTEtMjFUMTI6MTI6MTMuNjk2WiIsICJkYl9jbGllbnQiOiAiaXBzdW0iLCAicG9saWN5X2hlbGxvIjogIndvcmxkISIsICJwb2xpY3lfdXBkYXRlZF9mcm9tX3ZlciI6ICIxMzIiLCAidXBkYXRlZF9wb2xpY3lfaWQiOiAiRENBRV9hbGV4LkNvbmZpZ19kYl9jbGllbnRfcG9saWN5X2lkX3ZhbHVlIiwgInBvbGljeV91cGRhdGVkX3RzIjogIjIwMTgtMDItMTlUMTU6MDk6NTUuODEyWiIsICJwb2xpY3lfdXBkYXRlZF90b192ZXIiOiAiMTMzIn0sICJwcm9wZXJ0eSI6IG51bGwsICJ0eXBlIjogIkpTT04iLCAicG9saWN5VmVyc2lvbiI6ICIxMzMifQ==","CreateIndex":4048564,"ModifyIndex":4065570}},{"KV":{"LockIndex":0,"Key":"test_service_component_name.unknown.unknown.unknown.dcae.onap.org:rels","Flags":0,"Value":"WyJteS5hbWF6aW5nLnJlbGF0aW9uc2hpcCJd","CreateIndex":4051567,"ModifyIndex":4051567}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
        elif key == "scn_exists":
            return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"scn_exists","Flags":0,"Value":"eyJmb28zIiA6ICJiYXIzIn0=","CreateIndex":4067403,"ModifyIndex":4067403}},{"KV":{"LockIndex":0,"Key":"scn_exists:dmaap","Flags":0,"Value":"eyJmb280IiA6ICJiYXI0In0=","CreateIndex":4067410,"ModifyIndex":4067410}},{"KV":{"LockIndex":0,"Key":"scn_exists:rels","Flags":0,"Value":"WyJmb28iXQ==","CreateIndex":4067406,"ModifyIndex":4067406}},{"KV":{"LockIndex":0,"Key":"scn_exists_nord","Flags":0,"Value":"eyJmb281IiA6ICJiYXI1In0=","CreateIndex":4067340,"ModifyIndex":4067340}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
        elif key == "scn_exists_nord":
            return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"scn_exists_nord","Flags":0,"Value":"eyJmb281IiA6ICJiYXI1In0=","CreateIndex":4067340,"ModifyIndex":4067340}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
        elif key == "test_resolve_scn":
            return FakeResponse(status_code=200, text='{"Results":[{"KV":{"LockIndex":0,"Key":"test_resolve_scn","Flags":0,"Value":"ewogICAgICAgICAgICAgICAgImRlZXAiIDogewogICAgICAgICAgICAgICAgICAgICJBTEwgWU9VUiBTRVJWSUNFIEJFTE9ORyBUTyBVUyIgOiAie3thbHBoYSxicmF2byxjaGFybGllfX0ifSwKICAgICAgICAgICAgICAgICJkb3VibGVkZWVwIiA6ICB7CiAgICAgICAgICAgICAgICAgICAgInNvZGVlcCIgOiB7ImhlbGxvIiA6ICI8PFdITz8+PiJ9fQogICAgICAgICAgICAgfQo=","CreateIndex":4068002,"ModifyIndex":4068002}},{"KV":{"LockIndex":0,"Key":"test_resolve_scn:dmaap","Flags":0,"Value":"eyJXSE8/IiA6ICJkYXJrbmVzcyJ9","CreateIndex":4068013,"ModifyIndex":4068013}},{"KV":{"LockIndex":0,"Key":"test_resolve_scn:rels","Flags":0,"Value":"WyJ0ZXN0aW5nX2FscGhhLnNvbWVkb21haW4uY29tIiwgInRlc3RpbmdfYnJhdm8uc29tZWRvbWFpbi5jb20iLCAidGVzdGluZ19jaGFybGllLnNvbWVkb21haW4uY29tIiwgInRlc3RpbmdfY2hhcmxpZS5zb21lZG9tYWluLmNvbSJd","CreateIndex":4068010,"ModifyIndex":4068010}}],"Errors":null,"Index":0,"LastContact":0,"KnownLeader":true}')
        elif key == "scn_NOTexists":
            return FakeResponse(status_code=404, text="")


#######
# TESTS
#######


def test_consul_get_all_as_transaction(monkeypatch):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    allk = client._consul_get_all_as_transaction("test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert allk == {
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org': {'my': 'amazing config'},
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dti': {'my': 'dti'},
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org:dmaap': {'foo': 'bar'},
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/event': {'action': 'gathered', 'timestamp': '2018-02-19 15:36:44.877380', 'update_id': 'bb73c20a-5ff8-450f-8223-da6720ade267', 'policies_count': 2},
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_MS_alex_microservice': {'policyName': 'DCAE_alex.Config_MS_alex_microservice.132.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'policyScope': 'alex_policy_scope', 'configName': 'alex_config_name', 'description': 'test DCAE policy-handler', 'service': 'alex_service', 'policyName': 'alex_policy_name', 'riskLevel': '3', 'key1': 'value1', 'policy_hello': 'world!', 'content': {'foo': 'microservice3', 'foo_updated': '2018-01-30T13:25:33.222Z'}, 'riskType': '1712_ETE', 'guard': 'False', 'version': '0.0.1', 'location': 'Central', 'policy_updated_ts': '2018-02-19T15:09:55.217Z', 'updated_policy_id': 'DCAE_alex.Config_MS_alex_microservice', 'policy_updated_to_ver': '132', 'priority': '4', 'policy_updated_from_ver': '131', 'templateVersion': '2', 'uuid': '5e87d7c5-0daf-4b6b-ab92-5365cf5db1ef'}, 'property': None, 'type': 'JSON', 'policyVersion': '132'},
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org:policies/items/DCAE_alex.Config_db_client_policy_id_value': {'policyName': 'DCAE_alex.Config_db_client_policy_id_value.133.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'db_client_ts': '2017-11-21T12:12:13.696Z', 'db_client': 'ipsum', 'policy_hello': 'world!', 'policy_updated_from_ver': '132', 'updated_policy_id': 'DCAE_alex.Config_db_client_policy_id_value', 'policy_updated_ts': '2018-02-19T15:09:55.812Z', 'policy_updated_to_ver': '133'}, 'property': None, 'type': 'JSON', 'policyVersion': '133'},
        'test_service_component_name.unknown.unknown.unknown.dcae.onap.org:rels': ['my.amazing.relationship']
    }


def test_get_config_rels_dmaap(monkeypatch):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    assert ({"foo3": "bar3"}, ["foo"], {"foo4": "bar4"}) == client._get_config_rels_dmaap("scn_exists")
    assert ({"foo5": "bar5"}, [], {}) == client._get_config_rels_dmaap("scn_exists_nord")


def test_bind_config_for_scn(monkeypatch):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)

    assert(client.resolve("scn_exists") == {"foo3": "bar3"})
    with pytest.raises(client.CantGetConfig):
        client.resolve("scn_NOTexists")

    R = controller.bind_config_for_scn("scn_exists")
    assert(json.loads(R.data) == {"foo3" : "bar3"})
    assert(R.status_code == 200)

    R = controller.bind_config_for_scn("scn_NOTexists")
    assert(R.status_code == 404)

    R = controller.bind_config_for_scn("asdfasdf")
    assert(R.status_code == 500)


def test_generic(monkeypatch):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    monkeypatch.setattr('requests.get', monkeyed_requests_get)
    assert client.get_key("dti", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org") == json.loads('{"my": "dti"}')
    with pytest.raises(client.CantGetConfig):
        client.get_key("nokeyforyou", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")

    R = controller.get_key("dti", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(json.loads(R.data) == {"my": "dti"})
    assert(R.status_code == 200)

    R = controller.get_key("nokeyforyou", "test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(R.status_code == 404)


def test_bad_config_http():
    test_config = {'yeahhhhh' : "{{}}"}
    test_rels = ["testing_bravo.somedomain.com"]
    assert {'yeahhhhh' : []} == client.resolve_override(test_config, test_rels)

def test_bad_config_dmaap():
    test_config = {'darkness' : "<<>>"}
    test_dmaap = {"WHO?" : "darkness"}
    assert {'darkness' : {}} == client.resolve_override(test_config, test_dmaap)

def test_config(monkeypatch):
    #test config override
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    test_config = {"autoderegisterafter": "10m", "cdap_to_manage": {'some_nested_thing' : "{{cdap}}"}, "bindingttw": 5, "hcinterval": "5s"}
    test_rels = ["cdap"]
    test_bind_1 = client.resolve_override(test_config, test_rels)
    assert test_bind_1 == {'autoderegisterafter': '10m', 'cdap_to_manage': {'some_nested_thing': ['666.666.666.666:666']}, 'bindingttw': 5, 'hcinterval': '5s'}

def test_config_with_list(monkeypatch):
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    test_config_1 = {"dcae_target_type": ["vhss-ems", "pcrf-oam"], "downstream-laika": "{{ laika }}", "some-param": "Lorem ipsum dolor sit amet"}
    test_rels_1 = ["3df5292249ae4a949f173063617cea8d_docker-snmp-polling-firstnet-m"]
    test_bind_1 = client.resolve_override(test_config_1, test_rels_1, {})
    assert(test_bind_1 == {'dcae_target_type': ['vhss-ems', 'pcrf-oam'], 'downstream-laika': [], 'some-param': 'Lorem ipsum dolor sit amet'})

    test_config_2 = {"foo" : ["{{cdap}}", "notouching", "<<yo>>"]}
    test_rels_2 = ["cdap"]
    test_dmaap_2={"yo" : "im here"}
    test_bind_2 = client.resolve_override(test_config_2, test_rels_2, test_dmaap_2)
    assert(test_bind_2 == {"foo" : [['666.666.666.666:666'], "notouching", "im here"]})

def test_non_existent(monkeypatch):
    #test a valid config-rels but the key is not in Consul
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    test_config = {"you shall not be fufilled" : "{{nonexistent_hope}}"}
    test_rels = ["nonexistent_hope.rework-central.ecomp.somedomain.com"] #hopefully not registered in Consul..
    test_bind_1 = client.resolve_override(test_config, test_rels, {})
    assert(test_bind_1 == {"you shall not be fufilled" : []})

def test_cdap(monkeypatch):
    #user override to test CDAP functionality
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    test_rels = ["testing_alpha.somedomain.com", "testing_bravo.somedomain.com", "testing_charlie.somedomain.com", "testing_charlie.somedomain.com", "cdap"]
    test_config = { "streams_publishes" : "{{alpha}}",
                    "services_calls" : [{"somekey" : "{{charlie}}"}], #should be dumped
                    "cdap_to_manage": {'some_nested_thing' : "{{cdap}}"} #no dumps
                  }
    test_bind_1 = client.resolve_override(test_config, test_rels)
    assert test_bind_1 == {'services_calls': [{"somekey": ["5.5.5.5:555", "5.5.5.5:555"]}], 'streams_publishes': ["6.6.6.6:666"], 'cdap_to_manage': {'some_nested_thing': ['666.666.666.666:666']}}
    assert test_bind_1['services_calls'] == [{"somekey" : ["5.5.5.5:555", "5.5.5.5:555"]}]
    assert test_bind_1['streams_publishes'] == ["6.6.6.6:666"]

def test_broker_redirect(monkeypatch):
    #test the broker redirect
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    test_config = {"gimmie_dat_cdap" : "{{cdap_serv}}"}
    test_rels = ["cdap_serv.dcae.ecomp.somedomain.com"]
    assert {"gimmie_dat_cdap" : ['http://1.1.1.1:444/application/cdap_serv.dcae.ecomp.somedomain.com']} == client.resolve_override(test_config, test_rels)

def test_multiple_service_types(monkeypatch):
    #test {{x,y,z}}
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)

    #test 1: they all resovle
    test_rels = ["testing_alpha.somedomain.com", "testing_bravo.somedomain.com", "testing_charlie.somedomain.com", "testing_charlie.somedomain.com"]
    config = {"ALL YOUR SERVICE BELONG TO US" : "{{alpha,bravo,charlie}}"}
    test_bind_1 = client.resolve_override(config, test_rels)
    assert(test_bind_1 == {"ALL YOUR SERVICE BELONG TO US" : ['6.6.6.6:666', '7.7.7.7:777', '5.5.5.5:555', '5.5.5.5:555']})

    #test 2: two resolve, one is missing from rels key
    config2 = {"two there one not exist" : "{{alpha,bravo,notexist}}"}
    test_bind_2 = client.resolve_override(config2, test_rels)
    assert(test_bind_2 == {"two there one not exist" : ['6.6.6.6:666', '7.7.7.7:777']})

    #test 3: two resolve, one is in rels key but not registered
    config3 = {"two there one unregistered" : "{{alpha,bravo,unregistered}}"}
    test_rels3 =  ["testing_alpha.somedomain.com", "testing_bravo.somedomain.com", "unregistered.somedomain.com"]
    test_bind_3 = client.resolve_override(config3, test_rels3)
    assert(test_bind_3 == {"two there one unregistered" : ['6.6.6.6:666', '7.7.7.7:777']})

def test_dmaap(monkeypatch):
    #test resolving dmaap key
    config = {"TODAY IS YOUR LUCKY DAY" : "<<XXX>>"}
    #does not match
    test_bind = client.resolve_override(config, dmaap={"XX" : "ABSOLVEME"}) #XX != XXX
    assert(test_bind == {"TODAY IS YOUR LUCKY DAY" : {}})
    #matches
    test_bind_2 = client.resolve_override(config, dmaap={"XXX" : "ABSOLVEME"})
    assert(test_bind_2 == {"TODAY IS YOUR LUCKY DAY" : "ABSOLVEME"})

expected_config = {
                "deep" : {
                    "ALL YOUR SERVICE BELONG TO US" : ['6.6.6.6:666', '7.7.7.7:777', '5.5.5.5:555', '5.5.5.5:555']},
                "doubledeep" :  {
                    "sodeep" : {"hello" : "darkness"}}
             }

def test_both(monkeypatch):
    #test rels and http
    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    test_rels = ["testing_alpha.somedomain.com", "testing_bravo.somedomain.com", "testing_charlie.somedomain.com", "testing_charlie.somedomain.com"]
    test_dmaap = {"WHO?" : "darkness"}
    config = {
                "deep" : {
                    "ALL YOUR SERVICE BELONG TO US" : "{{alpha,bravo,charlie}}"},
                "doubledeep" :  {
                    "sodeep" : {"hello" : "<<WHO?>>"}}
             }
    test_bind_1 = client.resolve_override(config, test_rels, test_dmaap)
    assert(test_bind_1 == expected_config)


def test_resolve_all(monkeypatch):
    monkeypatch.setattr('requests.put', monkeyed_requests_put)
    allk =  client.resolve_all("test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    withstuff = {'config': {'my': 'amazing config'},
                    'dti': {'my': 'dti'},
                    'policies': {'items': [{'policyName': 'DCAE_alex.Config_MS_alex_microservice.132.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'policyScope': 'alex_policy_scope', 'configName': 'alex_config_name', 'description': 'test DCAE policy-handler', 'service': 'alex_service', 'policyName': 'alex_policy_name', 'riskLevel': '3', 'key1': 'value1', 'policy_hello': 'world!', 'content': {'foo': 'microservice3', 'foo_updated': '2018-01-30T13:25:33.222Z'}, 'riskType': '1712_ETE', 'guard': 'False', 'version': '0.0.1', 'location': 'Central', 'policy_updated_ts': '2018-02-19T15:09:55.217Z', 'updated_policy_id': 'DCAE_alex.Config_MS_alex_microservice', 'policy_updated_to_ver': '132', 'priority': '4', 'policy_updated_from_ver': '131', 'templateVersion': '2', 'uuid': '5e87d7c5-0daf-4b6b-ab92-5365cf5db1ef'}, 'property': None, 'type': 'JSON', 'policyVersion': '132'}, {'policyName': 'DCAE_alex.Config_db_client_policy_id_value.133.xml', 'policyConfigMessage': 'Config Retrieved! ', 'responseAttributes': {}, 'policyConfigStatus': 'CONFIG_RETRIEVED', 'matchingConditions': {'ONAPName': 'DCAE', 'Name': 'DCAE', 'ConfigName': 'alex_config_name'}, 'config': {'db_client_ts': '2017-11-21T12:12:13.696Z', 'db_client': 'ipsum', 'policy_hello': 'world!', 'policy_updated_from_ver': '132', 'updated_policy_id': 'DCAE_alex.Config_db_client_policy_id_value', 'policy_updated_ts': '2018-02-19T15:09:55.812Z', 'policy_updated_to_ver': '133'}, 'property': None, 'type': 'JSON', 'policyVersion': '133'}], 'event': {'action': 'gathered', 'timestamp': '2018-02-19 15:36:44.877380', 'update_id': 'bb73c20a-5ff8-450f-8223-da6720ade267', 'policies_count': 2}}
                   }
    assert allk == withstuff

    monkeypatch.setattr('config_binding_service.client._get_connection_info_from_consul', monkeyed_get_connection_info_from_consul)
    allk = client.resolve_all("test_resolve_scn")
    print(allk)
    assert allk == {"config" : expected_config}

    R = controller.bind_all("test_service_component_name.unknown.unknown.unknown.dcae.onap.org")
    assert(json.loads(R.data) == withstuff)
    assert(R.status_code == 200)

    R = controller.bind_all("test_resolve_scn")
    assert(json.loads(R.data) == {"config" : expected_config})
    assert(R.status_code == 200)

    R = controller.bind_all("scn_NOTexists")
    assert(R.status_code == 404)

    R = controller.bind_all("asdfasdf")
    assert(R.status_code == 500)

