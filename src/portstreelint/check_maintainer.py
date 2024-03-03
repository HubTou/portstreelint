#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging

from .library import counters, notify_maintainer

####################################################################################################
def check_maintainer(ports):
    """ Cross-checks the maintainer field with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-maintainer
    """
    for name, port in ports.items():
        if "MAINTAINER" in port:
            if '$' in port["MAINTAINER"]:
                continue # don't try to resolve embedded variables. Ignore check

            if port["maintainer"] != port["MAINTAINER"].lower():
                logging.error("Diverging maintainers between Index and Makefile for port %s", name)
                logging.error("... Index:maintainer    '%s'", port["maintainer"])
                logging.error("... Makefile:MAINTAINER '%s'", port["MAINTAINER"])
                counters["Diverging maintainers"] += 1
                notify_maintainer(port["maintainer"], "Diverging maintainers", name)
                notify_maintainer(port["MAINTAINER"], "Diverging maintainers", name)

    logging.info("Found %d ports with diverging maintainers", counters["Diverging maintainers"])
