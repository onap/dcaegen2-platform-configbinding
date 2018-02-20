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

from config_binding_service import client, controller
import pytest
import json
from requests.exceptions import HTTPError, RequestException
from requests import Response

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

def monkeyed_consul_get(k):
    if k == "dti_exists_test:dti":
        return {"foo" : "bar"}
    elif k == "dti_NOTexists_test:dti":
        raise HTTPError(response = FakeResponse(text= "", status_code = 404))
    elif k == "policies_exists_test:policies":
        return {"foo2" : "bar2"}
    elif k == "policies_NOTexists_test:policies":
        raise HTTPError(response = FakeResponse(text= "", status_code = 404))
    else:
        raise Exception("BLOW UP IN FIRE")

def monkeyed_resolve(k):
    if k == "scn_NOTexists":
        raise client.CantGetConfig(code = 404, response = "")
    elif k == "scn_exists":
        return {"foo3" : "bar3"}
    elif k == "scn_exists:rel":
        return ["foo"]
    elif k == "scn_exists:dmaap":
        return {"foo4" : "bar4"}

    elif k == "scn_exists_nord":
        return {"foo5" : "bar5"}
    elif k == "scn_exists_nord:rel":
        raise HTTPError(response = FakeResponse(text= "", status_code = 404))
    elif k == "scn_exists_nord:dmaap":
        raise HTTPError(response = FakeResponse(text= "", status_code = 404))

    else:
        raise Exception("BLOW UP IN FIRE")

#######
# TESTS
#######

def test_get_config_rels_dmaap(monkeypatch):
    monkeypatch.setattr('config_binding_service.client._consul_get_key', monkeyed_resolve)
    assert ({"foo3" : "bar3"}, ["foo"], {"foo4" : "bar4"}) == client._get_config_rels_dmaap("scn_exists")
    assert ({"foo5" : "bar5"}, [], {}) == client._get_config_rels_dmaap("scn_exists_nord")

def test_dti(monkeypatch):
    monkeypatch.setattr('config_binding_service.client._consul_get_key', monkeyed_consul_get)

    assert client.resolve_DTI("dti_exists_test") == {"foo" : "bar"}
    with pytest.raises(client.CantGetConfig):
        client.resolve_DTI("dti_NOTexists_test")

    R = controller.dtievents("dti_exists_test")
    assert(json.loads(R.data) == {"foo" : "bar"})
    assert(R.status_code == 200)

    R = controller.dtievents("dti_NOTexists_test")
    assert(R.status_code == 404)

    R = controller.dtievents("asdfasdf")
    assert(R.status_code == 500)


def test_policies(monkeypatch):
    monkeypatch.setattr('config_binding_service.client._consul_get_key', monkeyed_consul_get)

    assert client.resolve_policies("policies_exists_test") == {"foo2" : "bar2"}
    with pytest.raises(client.CantGetConfig):
        client.resolve_policies("policies_NOTexists_test")

    R = controller.policies("policies_exists_test")
    assert(json.loads(R.data) == {"foo2" : "bar2"})
    assert(R.status_code == 200)

    R = controller.policies("policies_NOTexists_test")
    assert(R.status_code == 404)

    R = controller.policies("asdfasdf")
    assert(R.status_code == 500)

def test_bind_config_for_scn(monkeypatch):
    monkeypatch.setattr('config_binding_service.client.resolve', monkeyed_resolve)

    assert(client.resolve("scn_exists") == {"foo3" : "bar3"})
    with pytest.raises(client.CantGetConfig):
        client.resolve("scn_NOTexists")

    R = controller.bind_config_for_scn("scn_exists")
    assert(json.loads(R.data) == {"foo3" : "bar3"})
    assert(R.status_code == 200)

    R = controller.bind_config_for_scn("scn_NOTexists")
    assert(R.status_code == 404)

    R = controller.bind_config_for_scn("asdfasdf")
    assert(R.status_code == 500)

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
    expected_config = {
                "deep" : {
                    "ALL YOUR SERVICE BELONG TO US" : ['6.6.6.6:666', '7.7.7.7:777', '5.5.5.5:555', '5.5.5.5:555']},
                "doubledeep" :  {
                    "sodeep" : {"hello" : "darkness"}}
             }
    assert(test_bind_1 == expected_config)

