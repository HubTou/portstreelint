#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import os

from .library import counters, notify_maintainer

####################################################################################################
def check_port_path(ports):
    """ Checks the port-path field existence """
    for name, port in ports.items():
        if not os.path.isdir(port["port-path"]):
            logging.error("Nonexistent port-path '%s' for port %s", port["port-path"], name)
            counters["Nonexistent port-path"] += 1
            notify_maintainer(port["maintainer"], "Nonexistent port-path", name)

    logging.info("Found %d ports with nonexistent port-path", counters["Nonexistent port-path"])
