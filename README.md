# config_binding_service

# Interface Diagram 
This repo is the thing in red:

![Alt text](doc/cbs_diagram.png?raw=true)

# Overview 

DCAE has a "templating language" built into components' configurations, as explained further below.
The orchestrator populates one/two keys (depending on the blueprint) into Consul that are used to *bind* component configurations config, a "rels key" and a "dmaap key".
If component A wants to connect to a component of type B, then A's rels key holds what specific service component name of B that A should connect to over direct HTTP. 
Service component name here means the full name that the component of type B is registered under in Consul (there can be multiple components of type B registered in Consul). 
The CBS (config binding service) then pulls down that rels key, fetches the connection information about that B (IP:Port), and replaces it into A's config. 
There is also a "dmaap key", which is the same concept, except what gets injected is a JSON of DMaaP connection information instead of an IP:Port.

# Usage
hit `url_of_this/service_component/service_component_name` and you are returned your bound config.

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

# Tests
Run:
```
set -x CONSUL_HOST "your_consul_dns_name.somedomain.com"; set -x HOSTNAME "config_binding_service"
cd tests/
pytest
```


