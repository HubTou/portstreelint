#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging

from .library import counters, notify_maintainer

OFFICIAL_CATEGORIES = [
    "accessibility", "afterstep", "arabic", "archivers", "astro", "audio", "benchmarks", "biology",
    "cad", "chinese", "comms", "converters", "databases", "deskutils", "devel", "dns", "docs",
    "editors", "education", "elisp", "emulators", "enlightenment", "finance", "french", "ftp",
    "games", "geography", "german", "gnome", "gnustep", "graphics", "hamradio", "haskell", "hebrew",
    "hungarian", "irc", "japanese", "java", "kde", "kde-applications", "kde-frameworks",
    "kde-plasma", "kld", "korean", "lang", "linux", "lisp", "mail", "mate", "math", "mbone", "misc",
    "multimedia", "net", "net-im", "net-mgmt", "net-p2p", "net-vpn", "news", "parallel", "pear",
    "perl5", "plan9", "polish", "ports-mgmt", "portuguese", "print", "python", "ruby", "rubygems",
    "russian", "scheme", "science", "security", "shells", "spanish", "sysutils", "tcl", "textproc",
    "tk", "ukrainian", "vietnamese", "wayland", "windowmaker", "www", "x11", "x11-clocks",
    "x11-drivers", "x11-fm", "x11-fonts", "x11-servers", "x11-themes", "x11-toolkits", "x11-wm",
    "xfce", "zope",
]

####################################################################################################
def check_categories(ports):
    """ Cross-checks the categories field with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-categories-definition
    """
    for name, port in ports.items():
        for category in port["categories"].split():
            if category not in OFFICIAL_CATEGORIES:
                logging.warning("Unofficial category '%s' in Index for port %s", category, name)
                counters["Unofficial categories"] += 1
                notify_maintainer(port["maintainer"], "Unofficial category", name)

        if "CATEGORIES" in port:
            if '$' in port["CATEGORIES"]:
                continue # don't try to resolve embedded variables. Ignore check

            if port["categories"] != port["CATEGORIES"]:
                logging.error("Diverging categories between Index and Makefile for port %s", name)
                logging.error("... Index:categories    '%s'", port["categories"])
                logging.error("... Makefile:CATEGORIES '%s'", port["CATEGORIES"])
                counters["Diverging categories"] += 1
                notify_maintainer(port["maintainer"], "Diverging categories", name)

            for category in port["CATEGORIES"].split():
                if category not in OFFICIAL_CATEGORIES:
                    logging.warning("Unofficial category '%s' in Makefile for port %s", category, name)
                    counters["Unofficial categories"] += 1
                    notify_maintainer(port["maintainer"], "Unofficial category", name)

    logging.info("Found %d ports with unofficial categories", counters["Unofficial categories"])
    logging.info("Found %d ports with diverging categories", counters["Diverging categories"])
