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
import requests
import connexion
import uuid
from flask import Response
from config_binding_service import client, get_consul_uri
from config_binding_service.logging import audit, utc, error


def _get_helper(json_expecting_func, **kwargs):
    """
    Helper function used by several functions below
    """
    try:
        payload = json_expecting_func(**kwargs)
        response, status_code, mimetype = json.dumps(payload), 200, "application/json"
    except client.BadRequest as exc:
        response, status_code, mimetype = exc.response, exc.code, "text/plain"
    except client.CantGetConfig as exc:
        response, status_code, mimetype = exc.response, exc.code, "text/plain"
    except Exception as exc:
        response, status_code, mimetype = "Unknown error", 500, "text/plain"
    return response, status_code, mimetype


def _get_or_generate_xer(raw_request):
    """get or generate the transaction id"""
    xer = raw_request.headers.get("x-onap-requestid", None)
    if xer is None:
        # some components are still using the old name
        xer = raw_request.headers.get("x-ecomp-requestid", None)
        if xer is None:
            # the user did NOT supply a request id, generate one
            xer = str(uuid.uuid4())
    return xer


def bind_all(service_component_name):
    """
    Get all the keys in Consul for this SCN, and bind the config
    """
    xer = _get_or_generate_xer(connexion.request)
    bts = utc()
    response, status_code, mimetype = _get_helper(client.resolve_all, service_component_name=service_component_name)
    audit(connexion.request, bts, xer, status_code, __name__, "called for component {0}".format(service_component_name))
    # Even though some older components might be using the ecomp name, we return the proper one
    return Response(response=response, status=status_code, mimetype=mimetype, headers={"x-onap-requestid": xer})


def bind_config_for_scn(service_component_name):
    """
    Bind just the config for this SCN
    """
    xer = _get_or_generate_xer(connexion.request)
    bts = utc()
    response, status_code, mimetype = _get_helper(client.resolve, service_component_name=service_component_name)
    audit(connexion.request, bts, xer, status_code, __name__, "called for component {0}".format(service_component_name))
    return Response(response=response, status=status_code, mimetype=mimetype, headers={"x-onap-requestid": xer})


def get_key(key, service_component_name):
    """
    Get a single key k of the form service_component_name:k from Consul.
    Should not be used and will return a BAD REQUEST for k=policies because it's a complex object
    """
    xer = _get_or_generate_xer(connexion.request)
    bts = utc()
    response, status_code, mimetype = _get_helper(client.get_key, key=key, service_component_name=service_component_name)
    audit(connexion.request, bts, xer, status_code, __name__, "called for component {0}".format(service_component_name))
    return Response(response=response, status=status_code, mimetype=mimetype, headers={"x-onap-requestid": xer})


def healthcheck():
    """
    CBS Healthcheck
    """
    xer = _get_or_generate_xer(connexion.request)
    bts = utc()
    res = requests.get("{0}/v1/catalog/service/config_binding_service".format(get_consul_uri()))
    status = res.status_code
    if status == 200:
        response = "CBS is alive and Consul connection OK"
    else:
        response = "CBS is alive but cannot reach Consul"
        # treating this as a WARN because this could be a temporary network glitch. Also per EELF guidelines this is a 200 ecode (availability)
        error(connexion.request, xer, "WARN", 200, tgt_entity="Consul", tgt_path="/v1/catalog/service/config_binding_service", msg=response)
    audit(connexion.request, bts, xer, status, __name__, msg=response)
    return Response(response=response, status=status)
