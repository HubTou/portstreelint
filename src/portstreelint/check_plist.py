#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import os

from .library import counters, notify_maintainer

####################################################################################################
def check_plist(ports, plist_abuse):
    """ Checks the package list existence and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/book/#porting-pkg-plist
    """
    for name, port in ports.items():
        if os.path.isdir(port["port-path"]):
            if not os.path.isfile(port["port-path"] + os.sep + "pkg-plist"):
                if not "PLIST_FILES" in port:
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
