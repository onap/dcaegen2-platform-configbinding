# config_binding_service

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
hit `url_of_this/service_component/service_component_name` and you are returned your bound config.

hit `url_of_this/dtievents/service_component_name` and you are returned the dti events for your service_component.

hit `url_of_this/policies/service_component_name` and you are returned the policies  for your service_component.

(Note: there is also a backdoor in the `client` module that allows you to pass in a direct JSON and a direct rels, but this isn't exposed via the HTTP API as of now)

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

# A note about directory structure
This project uses https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
This is a solution that runs a productionalized setup using NGINX+uwsgi+Flask (Flask is not meant to be run as a real webserver per their docs). This project requires the app/app structure. Tox still works from the root due to tox magic.

# Testing
You need tox:
```
pip install tox
```
Then from the root dir, *not in a virtual env*, just run:
```
tox
```
You may have to alter the tox.ini for the python envs you wish to test with.

# Deployment information

## Ports, HTTPS key/cert location

The CBS frontend (NGINX) exposes 10000 and 443. It runs HTTP on 10000 and HTTPS on 443. 80 is also exposed by the parent Dockerfile but nothing is listening there so it can be ignored.

If you wish to use HTTPS, it expects a key to be mounted at `/etc/nginx/ssl/nginx.key` and a cert to be mounted at `/etc/nginx/ssl/nginx.crt`. For example, a snippet from a `docker run` command:

```
... -v /host/path/to/nginx.key:/etc/nginx/ssl/nginx.key -v /host/path/to/nginx.crt:/etc/nginx/ssl/nginx.crt ...
```

These ports can be mapped to whatever extnernally. To keep the legacy behavior of prior ONAP releases of HTTP on 10000, map 10000:10000. Or, you can now make 10000 HTTPS by mapping 10000:443. This is determined by the deployment blueprint.

## Non-K8, Registrator, Consul setup
This section only pertains to a very specific setup of using Registrator and Consul (registrator to register a Consul healthcheck, and relying on Consul health checking). This section does *not* pertain to a Kubernetes deployment that uses K8 "readiness probes" instead of Consul.

There is a combination of issues, rooting from a bug in registrator:
1. https://jira.onap.org/browse/DCAEGEN2-482
2. https://github.com/gliderlabs/registrator/issues/605

That causes the Consul registration to be suffixed with ports, breaking the expected service name (`config_binding_service`), **even if** those ports are not mapped externally. That is, even if only one of the two ports (10000,443) is mapped, due to the above-linked bug, the service name will be wrong in Consul.

The solution is to run the container with a series of ENV variables. If you want the healthchecks to go over HTTPS, you also need to run the latest version on `master` in registrator. The old (3 year old) release of `v7` does not allow for HTTPS healthchecks.  The below example fixes the service name, turns OFF HTTP healthchecks, and turns ON HTTPS healthchecks (only works with latest registrator):

```
ENV SERVICE_10000_IGNORE true
ENV SERVICE_443_NAME config_binding_service
ENV SERVICE_443_CHECK_HTTPS /healthcheck
ENV SERVICE_443_CHECK_INTERVAL 15s
```

E.g., in Docker run terminology:

```
... -e SERVICE_10000_IGNORE=true -e SERVICE_443_NAME=config_binding_service -e SERVICE_443_CHECK_HTTPS=/healthcheck -e SERVICE_443_CHECK_INTERVAL=15s ...
```

If you wish to turn ON HTTP healthchecks and turn OFF HTTPS healthchecks, swith 10000 and 443 above. That will work even with `v7` of registrator (that is, `SERVICE_x_CHECK_HTTP` was already supported)

## Running locally for development (no docker)
It is recommended that you do this step in a virtualenv.
(set -x is Fish notaion, change for Bash etc. accordingly)
```
pip install --ignore-installed .; set -x CONSUL_HOST <YOUR_HOST>; ./main.py
```
