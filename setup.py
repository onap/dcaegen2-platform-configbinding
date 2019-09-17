# ============LICENSE_START=======================================================
# Copyright (c) 2017-2019 AT&T Intellectual Property. All rights reserved.
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

from setuptools import setup, find_packages

setup(
    name="config_binding_service",
    version="2.5.2",
    packages=find_packages(exclude=["tests.*", "tests"]),
    author="Tommy Carpenter",
    author_email="tommy@research.att.com",
    description="Service to fetch and bind configurations",
    url="https://gerrit.onap.org/r/#/admin/projects/dcaegen2/platform/configbinding",
    entry_points={"console_scripts": ["run.py=config_binding_service.run:main"]},
    install_requires=["requests", "Flask", "six", "gevent", "connexion[swagger-ui]"],
    package_data={"config_binding_service": ["openapi.yaml"]},
)