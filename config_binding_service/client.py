# ============LICENSE_START=======================================================
# org.onap.dcae
# ================================================================================
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

import re
import requests
import copy
import base64
import json
import six
from config_binding_service import get_consul_uri, get_logger
from functools import partial, reduce

_logger = get_logger(__name__)
CONSUL = get_consul_uri()

template_match_rels = re.compile("\{{2}([^\}\{]*)\}{2}")
template_match_dmaap = re.compile("<{2}([^><]*)>{2}")

###
# Cusom Exception
###
class CantGetConfig(Exception):
    def __init__(self, code, response):
        self.code = code
        self.response = response
###
# Private Functions
###
def _consul_get_key(key):
    """
    Try to fetch a key from Consul.
    No error checking here, let caller deal with it
    """
    _logger.info("Fetching {0}".format(key))
    response = requests.get("{0}/v1/kv/{1}".format(CONSUL, key))
    response.raise_for_status()
    D = json.loads(response.text)[0]
    return json.loads(base64.b64decode(D["Value"]).decode("utf-8"))

def _get_config_rels_dmaap(service_component_name):
    try:
        config = _consul_get_key(service_component_name) #not ok if no config
    except requests.exceptions.HTTPError as e:
        #might be a 404, or could be not even able to reach consul (503?), bubble up the requests error
        raise CantGetConfig(e.response.status_code, e.response.text)

    rels = []
    dmaap = {}
    try: #Not all nodes have relationships, so catch the error here and return [] if so
        rels = _consul_get_key("{0}:rel".format(service_component_name))
    except requests.exceptions.HTTPError: #ok if no rels key, might just have dmaap key
        pass
    try:
        dmaap = _consul_get_key("{0}:dmaap".format(service_component_name))
    except requests.exceptions.HTTPError: #ok if no dmaap key
        pass
    return config, rels, dmaap

def _get_connection_info_from_consul(service_component_name):
    """
    Call consul's catalog
    TODO: currently assumes there is only one service

    TODO: WARNING: FIXTHIS: CALLINTHENATIONALARMY:
    This tries to determine that a service_component_name is a cdap application by inspecting service_component_name and name munging. However, this would force all CDAP applications to have cdap_app in their name. A much better way to do this is to do some kind of catalog_lookup here, OR MAYBE change this API so that the component_type is passed in somehow. THis is a gaping TODO.
    """
    _logger.info("Retrieving connection information for {0}".format(service_component_name))
    res = requests.get("{0}/v1/catalog/service/{1}".format(CONSUL, service_component_name))
    res.raise_for_status()
    services = res.json()
    if services == []:
        _logger.info("Warning: config and rels keys were both valid, but there is no component named {0} registered in Consul!".format(service_component_name))
        return None #later will get filtered out
    else:
        ip  = services[0]["ServiceAddress"]
        port = services[0]["ServicePort"]
        if "cdap_app" in service_component_name:
            redirectish_url = "http://{0}:{1}/application/{2}".format(ip, port, service_component_name)
            _logger.info("component is a CDAP application; trying the broker redirect on {0}".format(redirectish_url))
            r = requests.get(redirectish_url)
            r.raise_for_status()
            details = r.json()
            # Pick out the details to expose to the component developers. These keys come from the broker API
            return { key: details[key] for key in ["connectionurl", "serviceendpoints"] }
        else:
            return "{0}:{1}".format(ip, port)

def _replace_rels_template(rels, template_identifier):
    """
    The magic. Replaces a template identifier {{...}} with the entrie(s) from the rels keys
    NOTE: There was a discussion over whether the CBS should treat {{}} as invalid. Mike asked that
    it resolve to the empty list. So, it does resolve it to empty list.
    """
    returnl = []
    for r in rels:
        if template_identifier in r and template_identifier is not "":
            returnl.append(r)
    #returnl now contains a list of DNS names (possible empty), now resolve them (or not if they are not regustered)
    return  list(filter(lambda x: x is not None, map(_get_connection_info_from_consul, returnl)))

def _replace_dmaap_template(dmaap, template_identifier):
    """
    This one liner could have been just put inline in the caller but maybe this will get more complex in future
    Talked to Mike, default value if key is not found in dmaap key should be {}
    """
    return {} if (template_identifier not in dmaap or template_identifier == "<<>>") else dmaap[template_identifier]

def _replace_value(v, rels, dmaap):
    """
    Takes a value v that was some value in the templatized configuration, determines whether it needs replacement (either {{}} or <<>>), and if so, replaces it.
    Otherwise just returns v

    implementation notes:
    - the split below sees if we have v = x,y,z... so we can support {{x,y,z,....}}
    - the lambda is because we can't fold operators in Python, wanted fold(+, L) where + when applied to lists in python is list concatenation
    """
    if isinstance(v, six.string_types): #do not try to replace anything that is not a string
        match_on_rels = re.match(template_match_rels, v)
        if match_on_rels:
            template_identifier = match_on_rels.groups()[0].strip() #now holds just x,.. of {{x,...}}
            rtpartial = partial(_replace_rels_template, rels)
            return reduce(lambda a,b: a+b, map(rtpartial, template_identifier.split(",")), [])
        match_on_dmaap = re.match(template_match_dmaap, v)
        if match_on_dmaap:
            template_identifier = match_on_dmaap.groups()[0].strip()
            """
            Here is what Mike said:
                1) want simple replacement of "<< >>" with dmaap key value
                2) never need to support <<f1,f2>> whereas we do support {{sct1,sct2}}
                The consequence is that if you give the CBS a dmaap key like {"foo" : {...}} you are going to get back {...}, but rels always returns [...].
                So now component developers have to possible handle dicts and [], and we have to communicate that to them
            """
            return _replace_dmaap_template(dmaap, template_identifier)
    return v #was not a match or was not a string, return value as is

def _recurse(config, rels, dmaap):
    """
    Recurse throug a configuration, or recursively a sub elemebt of it.
    If it's a dict: recurse over all the values
    If it's a list: recurse over all the values
    If it's a string: return the replacement
    If none of the above, just return the item.
    """
    if isinstance(config, list):
        return [_recurse(item, rels, dmaap) for item in config]
    elif isinstance(config,dict):
        for key in config:
            config[key] = _recurse(config[key], rels, dmaap)
        return config
    elif isinstance(config, six.string_types):
        return _replace_value(config, rels, dmaap)
    else:
        #not a dict, not a list, not a string, nothing to do.
        return config

#########
# PUBLIC API
#########
def resolve(service_component_name):
    """
    Return the bound config of service_component_name
    """
    config, rels, dmaap = _get_config_rels_dmaap(service_component_name)
    _logger.info("Fetching {0}: config={1}, rels={2}".format(service_component_name, json.dumps(config), rels))
    return _recurse(config, rels, dmaap)

def resolve_override(config, rels=[], dmaap={}):
    """
    Explicitly take in a config, rels, dmaap and try to resolve it.
    Useful for testing where you dont want to put the test values in consul
    """
    #use deepcopy to make sure that config is not touched
    return _recurse(copy.deepcopy(config), rels, dmaap)

def resolve_DTI(service_component_name):
    try:
        config = _consul_get_key("{}:dti".format(service_component_name))
    except requests.exceptions.HTTPError as e:
        #might be a 404, or could be not even able to reach consul (503?), bubble up the requests error
        raise CantGetConfig(e.response.status_code, e.response.text)
    return config

def resolve_policies(service_component_name):
    try:
        config = _consul_get_key("{}:policies".format(service_component_name))
    except requests.exceptions.HTTPError as e:
        #might be a 404, or could be not even able to reach consul (503?), bubble up the requests error
        raise CantGetConfig(e.response.status_code, e.response.text)
    return config
