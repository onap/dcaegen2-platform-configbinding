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
from config_binding_service.logging import utc, metrics
from config_binding_service import exceptions


CONSUL = get_consul_uri()

template_match_rels = re.compile("\{{2}([^\}\{]*)\}{2}")
template_match_dmaap = re.compile("<{2}([^><]*)>{2}")


###
# Private Functions
###


def _consul_get_all_as_transaction(service_component_name, raw_request, xer):
    """
    Use Consul's transaction API to get all keys of the form service_component_name:*
    Return a dict with all the values decoded
    """
    payload = [{"KV": {"Verb": "get-tree", "Key": service_component_name}}]

    bts = utc()
    response = requests.put("{0}/v1/txn".format(CONSUL), json=payload)
    msg = "Retrieving Consul transaction for all keys for {0}".format(service_component_name)
    metrics(raw_request, bts, xer, "Consul", "/v1/txn", response.status_code, __name__, msg=msg)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise exceptions.CantGetConfig(exc.response.status_code, exc.response.text)

    result = json.loads(response.text)["Results"]

    new_res = {}
    for res in result:
        key = res["KV"]["Key"]
        val = base64.b64decode(res["KV"]["Value"]).decode("utf-8")
        try:
            new_res[key] = json.loads(val)
        except json.decoder.JSONDecodeError:
            new_res[key] = "INVALID JSON"  # TODO, should we just include the original value somehow?

    if service_component_name not in new_res:
        raise exceptions.CantGetConfig(404, "")

    return new_res


def _get_config_rels_dmaap(service_component_name, raw_request, xer):
    allk = _consul_get_all_as_transaction(service_component_name, raw_request, xer)
    config = allk[service_component_name]
    rels = allk.get(service_component_name + ":rels", [])
    dmaap = allk.get(service_component_name + ":dmaap", {})
    return config, rels, dmaap


def _get_connection_info_from_consul(service_component_name):
    """
    Call consul's catalog
    TODO: currently assumes there is only one service

    DEPRECATION NOTE:
    This function existed when DCAE was using Consul to resolve service component's connection information.
    This relied on a "rels" key and a Cloudify relationship plugin to set up the magic.
    The consensous is that this feature is no longer used.
    This functionality is very likely deprecated by Kubernetes service discovery mechanism, and DMaaP.

    This function also includes logic related to CDAP, which is also likely deprecated.

    This code shall remain here for now but is at risk of being deleted in a future release.
    """
    # Note: there should be a metrics log here, but see the deprecation note above; this function is due to be deleted.
    res = requests.get("{0}/v1/catalog/service/{1}".format(CONSUL, service_component_name))
    res.raise_for_status()
    services = res.json()
    if services == []:
        return None  # later will get filtered out
    ip_addr = services[0]["ServiceAddress"]
    port = services[0]["ServicePort"]

    if "cdap_app" in service_component_name:
        redirectish_url = "http://{0}:{1}/application/{2}".format(ip_addr, port, service_component_name)
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
        if template_identifier in rel and template_identifier != "":
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


def resolve(service_component_name, raw_request, xer):
    """
    Return the bound config of service_component_name

    raw_request and xer are needed to form the correct metrics log
    """
    config, rels, dmaap = _get_config_rels_dmaap(service_component_name, raw_request, xer)
    return _recurse(config, rels, dmaap)


def resolve_override(config, rels=[], dmaap={}):
    """
    Explicitly take in a config, rels, dmaap and try to resolve it.
    Useful for testing where you dont want to put the test values in consul
    """
    # use deepcopy to make sure that config is not touched
    return _recurse(copy.deepcopy(config), rels, dmaap)


def resolve_all(service_component_name, raw_request, xer):
    """
    Return config,  policies, and any other k such that service_component_name:k exists (other than :dmaap and :rels)

    raw_request and xer are needed to form the correct metrics log
    """
    allk = _consul_get_all_as_transaction(service_component_name, raw_request, xer)
    returnk = {}

    # replace the config with the resolved config
    returnk["config"] = resolve_override(
        allk[service_component_name],
        allk.get("{0}:rels".format(service_component_name), []),
        allk.get("{0}:dmaap".format(service_component_name), {}),
    )

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
            if not (k == service_component_name or k.endswith(":rels") or k.endswith(":dmaap")):
                # this would blow up if you had a key in consul without a : but this shouldnt happen
                suffix = k.split(":")[1]
                returnk[suffix] = allk[k]

    return returnk


def get_key(key, service_component_name, raw_request, xer):
    """
    Try to fetch a key k from Consul of the form service_component_name:k

    raw_request and xer are needed to form the correct metrics log
    """
    if key == "policies":
        raise exceptions.BadRequest(
            ":policies is a complex folder and should be retrieved using the service_component_all API"
        )

    bts = utc()
    path = "v1/kv/{0}:{1}".format(service_component_name, key)
    response = requests.get("{0}/{1}".format(CONSUL, path))
    msg = "Retrieving single Consul key {0} for {1}".format(key, service_component_name)
    metrics(raw_request, bts, xer, "Consul", path, response.status_code, __name__, msg=msg)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise exceptions.CantGetConfig(exc.response.status_code, exc.response.text)
    rest = json.loads(response.text)[0]
    return json.loads(base64.b64decode(rest["Value"]).decode("utf-8"))
