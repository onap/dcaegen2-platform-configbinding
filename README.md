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

# Running

## Locally (no docker)
It is recommended that you do this step in a virtualenv.
(set -x is Fish notaion, change for Bash etc. accordingly)
```
pip install --ignore-installed .; set -x CONSUL_HOST <YOUR_HOST>; ./main.py
```

## Docker
## building
```
docker build -t config_binding_service:myversion .
```
## running
```
docker run -dt -p myextport:80 config_binding_service:myversion
```

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

