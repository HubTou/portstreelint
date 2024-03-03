#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging

from .library import counters, notify_maintainer

####################################################################################################
def check_comment(ports):
    """ Cross-checks the comment field with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-comment
    """
    for name, port in ports.items():
        if len(port["comment"]) > 70:
            logging.warning("Over 70 characters comment for port %s", name)
            counters["Too long comments"] += 1
            notify_maintainer(port["maintainer"], "Too long comments", name)

        if 'a' <= port["comment"][0] <= 'z':
            logging.error("Uncapitalized comment for port %s", name)
            counters["Uncapitalized comments"] += 1
            notify_maintainer(port["maintainer"], "Uncapitalized comments", name)

        if port["comment"].endswith('.'):
            logging.error("Dot-ended comment for port %s", name)
            counters["Dot-ended comments"] += 1
            notify_maintainer(port["maintainer"], "Dot-ended comments", name)

        if "COMMENT" in port:
            if '$' in port["COMMENT"]:
                continue # don't try to resolve embedded variables. Ignore check

            # Do not take into escaping backslashes which are used inconsistently
            # in both fields
            if port["comment"].replace("\\", "") != port["COMMENT"].replace("\\", ""):
                logging.error("Diverging comments between Index and Makefile for port %s", name)
                logging.error("... Index:comment    '%s'", port["comment"])
                logging.error("... Makefile:COMMENT '%s'", port["COMMENT"])
                counters["Diverging comments"] += 1
                notify_maintainer(port["maintainer"], "Diverging comments", name)

    logging.info("Found %d ports with too long comments", counters["Too long comments"])
    logging.info("Found %d ports with uncapitalized comments", counters["Uncapitalized comments"])
    logging.info("Found %d ports with dot-ended comments", counters["Dot-ended comments"])
    logging.info("Found %d ports with diverging comments", counters["Diverging comments"])
