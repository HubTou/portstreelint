#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import os

from .library import counters, notify_maintainer

####################################################################################################
def check_plist(ports, plist_abuse, ports_dir):
    """ Checks the package list existence and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/book/#porting-pkg-plist
    """
    for name, port in ports.items():
        # Use the PORTSDIR we have been told to, rather than the system's one
        port_path = port["port-path"].replace("/usr/ports", ports_dir)

        if os.path.isdir(port_path):
            if not os.path.isfile(port_path + os.sep + "pkg-plist"):
                if not "PLIST_FILES" in port:
                    if "AP_GENPLIST" in port:
                        continue

                    if "USES" in port:
                        items = port["USES"].split()

                        found = False
                        for item in items:
                            if item in ("pear", "horde", "gem"):
                                found = True
                                break

                            if item.startswith("pear:") \
                            or item.startswith("horde:") \
                            or item.startswith("gem:"):
                                found = True
                                break

                            if item.startswith("cran:"):
                                if "auto-plist" in item.split(':')[1].split(','):
                                    found = True
                                    break

                        if found:
                            continue

                    if "USE_PYTHON" in port:
                        if "autoplist" in port["USE_PYTHON"].split():
                            continue

                    if "RUBYGEM_AUTOPLIST" in port or "RUBYGEM_AUTOPLIST_ALT" in port:
                        continue

                    if not "PLIST" in port and not "PLIST_SUB" in port:
                        logging.debug("Nonexistent pkg-plist/PLIST_FILES/PLIST/PLIST_SUB for port %s", name)
                        counters["Nonexistent pkg-plist"] += 1
                        # Don't notify maintainers because there are too many cases I don't understand!
                else:
                    plist_entries = len(port["PLIST_FILES"].split())
                    if plist_entries >= plist_abuse:
                        logging.warning("PLIST_FILES abuse at %d entries for port %s", plist_entries, name)
                        counters["PLIST_FILES abuse"] += 1
                        notify_maintainer(port["maintainer"], "PLIST_FILES abuse", name)

    logging.info("Found %d ports with nonexistent pkg-plist (use --debug to list them)", counters["Nonexistent pkg-plist"])
    logging.info("Found %d ports with PLIST_FILES abuse", counters["PLIST_FILES abuse"])
