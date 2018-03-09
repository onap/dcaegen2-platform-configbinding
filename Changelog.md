# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.1.2]
* Log to a file to be picked up by ELK per DCAEGEN2-387
* Logging not totally finished w.r.t. formats, but this at least logs more and gets them into ELK

## [2.1.1]
* [Shamefully this entry was missing]

## [2.1.0]
* Add a generic API for getting arbitrary keys
* Some PEP8/Pylint compliance
* Fix SONAR complaints

## [2.0.0]
* Remove policy and DTI APIs
* Add new API that returns Config, Policy, DTI, Everything
* Test coverage 82%

## [1.3.1]
* Add more tests (Currently 75%)
* Fix liscenses

## [1.3.0]
* Sync ONAP with Internal CBS
* Add tests (Currently 62%)
* Update docker python version to 3.6
* Move installation of reqs into Docker container

## [1.2.0]
* Remove waterfalled CONSUL_HOST
* Add ONAP liscenses
* Remove references to specific telco and it's IPs in tests
* [Internal version conflict]: Add dti and policies endpoints

## [1.1.0]
* Add a healthcheck endpoint
* Fix a bug where a 404 config not found was being returned as a 500

## [1.0.1]
* Fix {{}} to resolve to [] instead of whatever is in rels key
* Remove all impure tests. All tests are now unit tests.

## [1.0.0]
* GLORIOUS CHANGE! At some point, CASK fixed a bug where if you sent a configuration JSON to CDAP that contained a value that was not a string, it would blow up. This allows me to remove the endpoint specific to CDAP components so the same endpoint is now used for Docker and CDAP.
* Props to Terry Troutman for helping me discover this.
* Removes some impure tests. Still some impurity there

## [0.9.0]
* In addition to the "rels key" a new key was introduced, the "dmaap key". Support replacing dmaap keys assumung the tempalating language "<< >>"

## [0.8.0]
* Start changelog..
* Fix a 500 bug where the CBS would return a 500 when a service was in a rels key but that service was not registered in Consul
* Support a new feature where you can now bind {{x,y,....}} instead of just {{x}}. The return list is all concat together
