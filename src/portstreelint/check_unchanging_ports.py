#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import datetime
import logging

from .library import counters, notify_maintainer

####################################################################################################
def check_unchanging_ports(ports, unchanged_days):
    """ Checks if the port has been unmodified for too long """
    for name, port in ports.items():
        today = datetime.datetime.now(datetime.timezone.utc)
        if "Last modification" in port:
            if port["Last modification"] < today - datetime.timedelta(days=unchanged_days):
                logging.info("No modification since more than %d days for port %s", unchanged_days, name)
                counters["Unchanged for a long time"] += 1
                notify_maintainer(port["maintainer"], "Unchanged for a long time", name)

    logging.info("Found %d ports unchanged for a long time", counters["Unchanged for a long time"])
