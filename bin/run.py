#!/usr/bin/env python3

import connexion
import sys
from config_binding_service import get_logger

_logger = get_logger(__name__)

if __name__ == '__main__':
    try:
        app = connexion.App(__name__, specification_dir='../config_binding_service/swagger/')
        app.add_api('swagger.yaml', arguments={'title': 'Config Binding Service'})
        app.run(host='0.0.0.0', port=10000, debug=False) 
    except Exception as e:
        _logger.error("Fatal error. Could not start webserver due to: {0}".format(e))
