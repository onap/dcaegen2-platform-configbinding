# config_binding_service

 ============LICENSE_START=======================================================
 Copyright (c) 2017-2019 AT&T Intellectual Property. All rights reserved.
 ================================================================================
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 ============LICENSE_END=========================================================

 ECOMP is a trademark and service mark of AT&T Intellectual Property.


# Changelog
All changes are logged in Changelog.md

# Overview

DCAE has a "templating language" built into components' configurations, as explained further below.
The orchestrator populates one/two keys (depending on the blueprint) into Consul that are used to *bind* component configurations config, a "rels key" and a "dmaap key".
If component A wants to connect to a component of type B, then A's rels key holds what specific service component name of B that A should connect to over direct HTTP.
Service component name here means the full name that the component of type B is registered under in Consul (there can be multiple components of type B registered in Consul).
The CBS (config binding service) then pulls down that rels key, fetches the connection information about that B (IP:Port), and replaces it into A's config.
There is also a "dmaap key", which is the same concept, except what gets injected is a JSON of DMaaP connection information instead of an IP:Port.

In addition, this service provides the capability to retrieve either the DTI events (not history) or the policies for a given service_component.

# Usage
See the OpenAPI spec in `config_binding_service/openapi.yaml`. You can also see a "pretty" version of this by running the container and going to `/ui`.

# Assumptions
1. `CONSUL_HOST` is set as an environmental variable where this binding service is run. If it is not, it defaults to the Rework Consul which is probably not what you want.
2. `service_component_name` is in consul as a key and holds the config
3. `service_component_name:rel` is in consul as a key *if* you are expecting a direct HTTP resolution, and holds the service component names of connections.
4. `service_component_name:dmaap` is in consul *if* you are expecting a DMaaP resolution, and holds the components DMaaP information.

# Templating Language
The CBS tries to resolve a component's configuration with a templating language. We have two templating languages embedded in our component's configuration (`{{...}}` and `<<...>>`). There are two because the CBS has to be able to distinguish between a rels-key-resolve and a dmaap-key-resolve. That is, if component X is trying to bind their component, and they want to talk to Y, someone has to tell the CBS whether they are trying to talk via IP:port or a feed.

Specifically, if the CBS sees:

```
X's configuration:
{
    ...
    config_key : << F >> // will try to resolve via X:dmaap and look for F
    config_key : {{ F }} // will try to resolve via X:rels and look for F
}
```

# Development
## Version changes
Development changes require a version bump in several places. They are:
1. Changelod.md
2. version.properties
3. pom.xml
4. setup.py
Additionally, if the development leads to an API change,
5. config_binding_service/openapi.yaml

## Unit esting
You need `tox`; then just run:

    tox

# Deployment

## HTTPS
Details coming soon

## Docker

    sudo docker run -dt -p 10000:10000 -e CONSUL_HOST=<YOUR_HOST>cbs:X.Y.Z

If you wish to turn ON HTTP healthchecks and turn OFF HTTPS healthchecks, swith 10000 and 443 above. That will work even with `v7` of registrator (that is, `SERVICE_x_CHECK_HTTP` was already supported)

## Locally for development (no docker)
It is recommended that you do this step in a virtualenv.
(set -x is Fish notaion, change for Bash etc. accordingly)

    pip install --ignore-installed .; set -x CONSUL_HOST <YOUR_HOST>; ./run.py
