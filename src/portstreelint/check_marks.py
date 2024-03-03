#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import datetime
import logging

from .library import counters, notify_maintainer

####################################################################################################
def check_marks(ports, limits):
    """ Checks the existence of special marks variables (ie. BROKEN, etc.) in Makefiles """
    for name, port in ports.items():
        today = datetime.datetime.now(datetime.timezone.utc)

        if "BROKEN" in port:
            if port["Last modification"] < today - datetime.timedelta(days=limits["BROKEN since"]):
                logging.warning("BROKEN mark '%s' for port %s", port["BROKEN"], name)
                counters["Marked as BROKEN for too long"] += 1
                notify_maintainer(port["maintainer"], "Marked as BROKEN for too long", name)
            else:
                logging.info("BROKEN mark '%s' for port %s", port["BROKEN"], name)
                counters["Marked as BROKEN"] += 1
                notify_maintainer(port["maintainer"], "Marked as BROKEN", name)

        if "DEPRECATED" in port:
            if port["Last modification"] < today - datetime.timedelta(days=limits["DEPRECATED since"]):
                logging.warning("DEPRECATED mark '%s' for port %s", port["DEPRECATED"], name)
                counters["Marked as DEPRECATED for too long"] += 1
                notify_maintainer(port["maintainer"], "Marked as DEPRECATED for too long", name)
            else:
                logging.info("DEPRECATED mark '%s' for port %s", port["DEPRECATED"], name)
                counters["Marked as DEPRECATED"] += 1
                notify_maintainer(port["maintainer"], "Marked as DEPRECATED", name)

        if "FORBIDDEN" in port:
            if port["Last modification"] < today - datetime.timedelta(days=limits["FORBIDDEN since"]):
                logging.warning("FORBIDDEN mark '%s' for port %s", port["FORBIDDEN"], name)
                counters["Marked as FORBIDDEN for too long"] += 1
                notify_maintainer(port["maintainer"], "Marked as FORBIDDEN for too long", name)
            else:
                logging.info("FORBIDDEN mark '%s' for port %s", port["FORBIDDEN"], name)
                counters["Marked as FORBIDDEN"] += 1
                notify_maintainer(port["maintainer"], "Marked as FORBIDDEN", name)

        if "IGNORE" in port:
            logging.info("IGNORE mark '%s' for port %s", port["IGNORE"], name)
            counters["Marked as IGNORE"] += 1
            notify_maintainer(port["maintainer"], "Containing an IGNORE mark", name)

        if "RESTRICTED" in port:
            logging.info("RESTRICTED mark '%s' for port %s", port["RESTRICTED"], name)
            counters["Marked as RESTRICTED"] += 1
            notify_maintainer(port["maintainer"], "Marked as RESTRICTED", name)

        if "EXPIRATION_DATE" in port:
            logging.warning("EXPIRATION_DATE mark '%s' for port %s", port["EXPIRATION_DATE"], name)
            counters["Marked with EXPIRATION_DATE"] += 1
            notify_maintainer(port["maintainer"], "Marked with EXPIRATION_DATE", name)

    logging.info("Found %d ports marked as BROKEN", counters["Marked as BROKEN"])
    logging.info("Found %d ports marked as BROKEN for too long", counters["Marked as BROKEN for too long"])
    logging.info("Found %d ports marked as DEPRECATED", counters["Marked as DEPRECATED"])
    logging.info("Found %d ports marked as DEPRECATED for too long", counters["Marked as DEPRECATED for too long"])
    logging.info("Found %d ports marked as FORBIDDEN", counters["Marked as FORBIDDEN"])
    logging.info("Found %d ports marked as FORBIDDEN for too long", counters["Marked as FORBIDDEN for too long"])
    logging.info("Found %d ports marked as IGNORE", counters["Marked as IGNORE"])
    logging.info("Found %d ports marked as RESTRICTED", counters["Marked as RESTRICTED"])
    logging.info("Found %d ports marked with EXPIRATION_DATE", counters["Marked with EXPIRATION_DATE"])
