#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging

from .library import counters, notify_maintainer

####################################################################################################
def check_installation_prefix(ports):
    """ Checks the installation-prefix field usualness """
    for name, port in ports.items():
        if port["installation-prefix"] == "/usr/local":
            pass
        elif port["installation-prefix"] == "/compat/linux" and name.startswith("linux"):
            pass
        elif port["installation-prefix"] == "/usr/local/FreeBSD_ARM64" and "-aarch64-" in name:
            pass
        elif port["installation-prefix"].startswith("/usr/local/android") and "droid" in name:
            pass
        elif port["installation-prefix"] == "/var/qmail" and "qmail" in name or name.startswith("queue-fix"):
            pass
        elif port["installation-prefix"] == "/usr" and name.startswith("global-tz-") or name.startswith("zoneinfo-"):
            pass
        else:
            logging.warning("Unusual installation-prefix '%s' for port %s", port["installation-prefix"], name)
            counters["Unusual installation-prefix"] += 1
            notify_maintainer(port["maintainer"], "Unusual installation-prefix", name)

    logging.info("Found %d ports with unusual installation-prefix", counters["Unusual installation-prefix"])
