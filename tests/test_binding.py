# ============LICENSE_START=======================================================
# org.onap.dcae
# ================================================================================
# Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
from config_binding_service import client
import pytest
import json

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


