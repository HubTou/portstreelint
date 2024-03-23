#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import os

from .library import counters, notify_maintainer

####################################################################################################
def check_port_path(ports, ports_dir):
    """ Checks the port-path field existence """
    for name, port in ports.items():
        # Use the PORTSDIR we have been told to, rather than the system's one
        port_path = port["port-path"].replace("/usr/ports", ports_dir)
        if not os.path.isdir(port_path):
            logging.error("Nonexistent port-path '%s' for port %s", port_path, name)
            counters["Nonexistent port-path"] += 1
            notify_maintainer(port["maintainer"], "Nonexistent port-path", name)

    logging.info("Found %d ports with nonexistent port-path", counters["Nonexistent port-path"])
