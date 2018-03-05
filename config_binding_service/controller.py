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

import requests
from flask import Response
import json
from config_binding_service import client, get_consul_uri, get_logger

_logger = get_logger(__name__)


def bind_all(service_component_name):
    try:
        allk = client.resolve_all(service_component_name)
        return Response(response=json.dumps(allk),
                        status=200,
                        mimetype="application/json")
    except client.CantGetConfig as e:
        return Response(status=e.code,
                        response=e.response)
    except Exception as e:
        _logger.error(e)
        return Response(response="Unknown error:  please report",
                        status=500)


def bind_config_for_scn(service_component_name):
    try:
        bound = client.resolve(service_component_name)
        return Response(response=json.dumps(bound),
                        status=200,
                        mimetype="application/json")
    except client.CantGetConfig as e:
        return Response(status=e.code,
                        response=e.response)
    except Exception as e:  # should never happen...
        _logger.error(e)
        return Response(response="Please report this error",
                        status=500)


def get_key(key, service_component_name):
    try:
        bound = client.get_key(key, service_component_name)
        return Response(response=json.dumps(bound),
                        status=200,
                        mimetype="application/json")
    except client.CantGetConfig as e:
        return Response(status=e.code,
                        response=e.response)
    except client.BadRequest as exc:
        return Response(status=exc.code,
                        response=exc.response,
                        mimetype="text/plain")
    except Exception as e:  # should never happen...
        _logger.error(e)
        return Response(response="Please report this error",
                        status=500)


def healthcheck():
    # got this far, I must be alive... check my connection to Consul by checking myself
    CONSUL = get_consul_uri()
    res = requests.get(
        "{0}/v1/catalog/service/config_binding_service".format(CONSUL))
    if res.status_code == 200:
        return Response(response="CBS is alive and Consul connection OK",
                        status=200)
    else:
        return Response(response="CBS is alive but cannot reach Consul",
                        status=503)
