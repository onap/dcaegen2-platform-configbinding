# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.2.5] - 2/7/2019
* Fix issue caused by a flake8 update

## [2.2.4] - 10/25/2018
* Fix issues caused by a flake8 update

## [2.2.3] - 7/25/2018
* By request, include a self signed cert so the image always comes up.

## [2.2.2] - 7/9/2018
* Add EELF metrics log and logging statements
* Fixed a redundant Consul call where client.resolve_all did not need to call the transaction API twice
* Fix some comments / add deprecation warnings

## [2.2.1] - 7/5/2018
* Fix bug where healthcheck call was not in the audit log
* Add service_component_name into the audit record message field on audit calls
* Rename "log.log" to "audit.log"
* Add EELF compliant "error.log"

## [2.2.0] - 6/26/2018
* Productionalize by moving to NGINX+UWSGI. Flask was not meant to be run as a production server
* This is towards HTTPS support, which will now be done via NGINX reverse proxying instead of in the application code itself
* The app structure has changed due to the project I am now using for this. See https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/

## [2.1.5] - 4/10/2018
* Fix a key where an invalid JSON in Consul blows up the CBS
* Refactor the tests into smaller files

## [2.1.4] - 4/3/2018
* Adhere to EELF metrics log for the log file

## [2.1.3]
* Small cleanups; move swagger, remove bin, do proper install in Dockerfile

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
* Fix licenses

## [1.3.0]
* Sync ONAP with Internal CBS
* Add tests (Currently 62%)
* Update docker python version to 3.6
* Move installation of reqs into Docker container

## [1.2.0]
* Remove waterfalled CONSUL_HOST
* Add ONAP licenses
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
* In addition to the "rels key" a new key was introduced, the "dmaap key". Support replacing dmaap keys assuming the templating language "<< >>"

## [0.8.0]
* Start changelog..
* Fix a 500 bug where the CBS would return a 500 when a service was in a rels key but that service was not registered in Consul
* Support a new feature where you can now bind {{x,y,....}} instead of just {{x}}. The return list is all concat together
