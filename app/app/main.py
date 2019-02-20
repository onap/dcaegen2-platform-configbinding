#!/usr/bin/env python3

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
from config_binding_service.logging import create_loggers
from config_binding_service import app

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', port=10000, debug=True)
else:
    # Entrypoint in UWSGI
    create_loggers()
