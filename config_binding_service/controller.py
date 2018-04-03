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
from config_binding_service.logging import LOGGER, audit, utc


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
        LOGGER.error(exc)
        response, status_code, mimetype = "Unknown error, please report", 500, "text/plain"
    return response, status_code, mimetype


def _get_or_generate_xer(raw_request):
    """get or generate the transaction id"""
    rid = raw_request.headers.get("x-onap-requestid", None)
    if rid is None:
        # some components are still using the old name
        rid = raw_request.headers.get("x-ecomp-requestid", None)
        if rid is None:
            # the user did NOT supply a request id, generate one
            rid = str(uuid.uuid4())
    return rid


def bind_all(service_component_name):
    """
    Get all the keys in Consul for this SCN, and bind the config
    """
    rid = _get_or_generate_xer(connexion.request)
    bts = utc()
    response, status_code, mimetype = _get_helper(client.resolve_all, service_component_name=service_component_name)
    audit(connexion.request, bts, rid, status_code, __name__)
    # Even though some older components might be using the ecomp name, we return the proper one
    return Response(response=response, status=status_code, mimetype=mimetype, headers={"x-onap-requestid": rid})


def bind_config_for_scn(service_component_name):
    """
    Bind just the config for this SCN
    """
    print(connexion)
    print(connexion.request)
    rid = _get_or_generate_xer(connexion.request)
    bts = utc()
    response, status_code, mimetype = _get_helper(client.resolve, service_component_name=service_component_name)
    audit(connexion.request, bts, rid, status_code, __name__)
    return Response(response=response, status=status_code, mimetype=mimetype, headers={"x-onap-requestid": rid})


def get_key(key, service_component_name):
    """
    Get a single key k of the form service_component_name:k from Consul.
    Should not be used and will return a BAD REQUEST for k=policies because it's a complex object
    """
    rid = _get_or_generate_xer(connexion.request)
    bts = utc()
    response, status_code, mimetype = _get_helper(client.get_key, key=key, service_component_name=service_component_name)
    audit(connexion.request, bts, rid, status_code, __name__)
    return Response(response=response, status=status_code, mimetype=mimetype, headers={"x-onap-requestid": rid})


def healthcheck():
    """
    CBS Healthcheck
    """
    LOGGER.info("healthcheck called")
    res = requests.get(
        "{0}/v1/catalog/service/config_binding_service".format(get_consul_uri()))
    if res.status_code == 200:
        return Response(response="CBS is alive and Consul connection OK",
                        status=200)
    return Response(response="CBS is alive but cannot reach Consul",
                    status=503)
