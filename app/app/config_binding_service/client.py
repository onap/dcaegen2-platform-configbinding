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

import re
from functools import partial, reduce
import base64
import copy
import json
import requests
import six
from config_binding_service import get_consul_uri
from config_binding_service.logging import LOGGER


CONSUL = get_consul_uri()

template_match_rels = re.compile("\{{2}([^\}\{]*)\}{2}")
template_match_dmaap = re.compile("<{2}([^><]*)>{2}")

###
# Cusom Exception
###


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


###
# Private Functions
###


def _consul_get_all_as_transaction(service_component_name):
    """
    Use Consul's transaction API to get all keys of the form service_component_name:*
    Return a dict with all the values decoded
    """
    payload = [
        {
            "KV": {
                "Verb": "get-tree",
                "Key": service_component_name,
            }
        }]

    response = requests.put("{0}/v1/txn".format(CONSUL), json=payload)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise CantGetConfig(exc.response.status_code, exc.response.text)

    result = json.loads(response.text)['Results']

    new_res = {}
    for res in result:
        key = res["KV"]["Key"]
        val = base64.b64decode(res["KV"]["Value"]).decode("utf-8")
        try:
            new_res[key] = json.loads(val)
        except json.decoder.JSONDecodeError:
            new_res[key] = "INVALID JSON"  # TODO, should we just include the original value somehow?

    if service_component_name not in new_res:
        raise CantGetConfig(404, "")

    return new_res


def _get_config_rels_dmaap(service_component_name):
    allk = _consul_get_all_as_transaction(service_component_name)
    config = allk[service_component_name]
    rels = allk.get(service_component_name + ":rels", [])
    dmaap = allk.get(service_component_name + ":dmaap", {})
    return config, rels, dmaap


def _get_connection_info_from_consul(service_component_name):
    """
    Call consul's catalog
    TODO: currently assumes there is only one service

    TODO: WARNING: FIXTHIS: CALLINTHENATIONALARMY:
    This tries to determine that a service_component_name is a cdap application by inspecting service_component_name and name munging. However, this would force all CDAP applications to have cdap_app in their name. A much better way to do this is to do some kind of catalog_lookup here, OR MAYBE change this API so that the component_type is passed in somehow. THis is a gaping TODO.
    """
    LOGGER.info("Retrieving connection information for %s", service_component_name)
    res = requests.get(
        "{0}/v1/catalog/service/{1}".format(CONSUL, service_component_name))
    res.raise_for_status()
    services = res.json()
    if services == []:
        LOGGER.info("Warning: config and rels keys were both valid, but there is no component named %s registered in Consul!", service_component_name)
        return None  # later will get filtered out
    ip_addr = services[0]["ServiceAddress"]
    port = services[0]["ServicePort"]
    if "cdap_app" in service_component_name:
        redirectish_url = "http://{0}:{1}/application/{2}".format(
            ip_addr, port, service_component_name)
        LOGGER.info("component is a CDAP application; trying the broker redirect on %s", redirectish_url)
        res = requests.get(redirectish_url)
        res.raise_for_status()
        details = res.json()
        # Pick out the details to expose to the component developers. These keys come from the broker API
        return {key: details[key] for key in ["connectionurl", "serviceendpoints"]}
    return "{0}:{1}".format(ip_addr, port)


def _replace_rels_template(rels, template_identifier):
    """
    The magic. Replaces a template identifier {{...}} with the entrie(s) from the rels keys
    NOTE: There was a discussion over whether the CBS should treat {{}} as invalid. Mike asked that
    it resolve to the empty list. So, it does resolve it to empty list.
    """
    returnl = []
    for rel in rels:
        if template_identifier in rel and template_identifier is not "":
            returnl.append(rel)
    # returnl now contains a list of DNS names (possible empty), now resolve them (or not if they are not regustered)
    return list(filter(lambda x: x is not None, map(_get_connection_info_from_consul, returnl)))


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
    if isinstance(v, six.string_types):  # do not try to replace anything that is not a string
        match_on_rels = re.match(template_match_rels, v)
        if match_on_rels:
            # now holds just x,.. of {{x,...}}
            template_identifier = match_on_rels.groups()[0].strip()
            rtpartial = partial(_replace_rels_template, rels)
            return reduce(lambda a, b: a + b, map(rtpartial, template_identifier.split(",")), [])
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
    return v  # was not a match or was not a string, return value as is


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
    if isinstance(config, dict):
        for key in config:
            config[key] = _recurse(config[key], rels, dmaap)
        return config
    if isinstance(config, six.string_types):
        return _replace_value(config, rels, dmaap)
    # not a dict, not a list, not a string, nothing to do.
    return config


#########
# PUBLIC API
#########


def resolve(service_component_name):
    """
    Return the bound config of service_component_name
    """
    config, rels, dmaap = _get_config_rels_dmaap(service_component_name)
    return _recurse(config, rels, dmaap)


def resolve_override(config, rels=[], dmaap={}):
    """
    Explicitly take in a config, rels, dmaap and try to resolve it.
    Useful for testing where you dont want to put the test values in consul
    """
    # use deepcopy to make sure that config is not touched
    return _recurse(copy.deepcopy(config), rels, dmaap)


def resolve_all(service_component_name):
    """
    Return config,  policies, and any other k such that service_component_name:k exists (other than :dmaap and :rels)
    """
    allk = _consul_get_all_as_transaction(service_component_name)
    returnk = {}

    # replace the config with the resolved config
    returnk["config"] = resolve(service_component_name)

    # concatenate the items
    for k in allk:
        if "policies" in k:
            if "policies" not in returnk:
                returnk["policies"] = {}
                returnk["policies"]["event"] = {}
                returnk["policies"]["items"] = []

            if k.endswith(":policies/event"):
                returnk["policies"]["event"] = allk[k]
            elif ":policies/items" in k:
                returnk["policies"]["items"].append(allk[k])
        else:
            if not(k == service_component_name or k.endswith(":rels") or k.endswith(":dmaap")):
                # this would blow up if you had a key in consul without a : but this shouldnt happen
                suffix = k.split(":")[1]
                returnk[suffix] = allk[k]

    return returnk


def get_key(key, service_component_name):
    """
    Try to fetch a key k from Consul of the form service_component_name:k
    """
    if key == "policies":
        raise BadRequest(
            ":policies is a complex folder and should be retrieved using the service_component_all API")
    response = requests.get(
        "{0}/v1/kv/{1}:{2}".format(CONSUL, service_component_name, key))
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise CantGetConfig(exc.response.status_code, exc.response.text)
    rest = json.loads(response.text)[0]
    return json.loads(base64.b64decode(rest["Value"]).decode("utf-8"))
