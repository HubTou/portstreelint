#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging

from .library import counters, notify_maintainer

OFFICIAL_LICENSES = [
    "AGPLv3", "AGPLv3+", "APACHE10", "APACHE11", "APACHE20", "ART10", "ART20", "ARTPERL10", "BSD",
    "BSD0CLAUSE", "BSD2CLAUSE", "BSD3CLAUSE", "BSD4CLAUSE", "BSL", "CC-BY-1.0", "CC-BY-2.0",
    "CC-BY-2.5", "CC-BY-3.0", "CC-BY-4.0", "CC-BY-NC-1.0", "CC-BY-NC-2.0", "CC-BY-NC-2.5",
    "CC-BY-NC-3.0", "CC-BY-NC-4.0", "CC-BY-NC-ND-1.0", "CC-BY-NC-ND-2.0", "CC-BY-NC-ND-2.5",
    "CC-BY-NC-ND-3.0", "CC-BY-NC-ND-4.0", "CC-BY-NC-SA-1.0", "CC-BY-NC-SA-2.0", "CC-BY-NC-SA-2.5",
    "CC-BY-NC-SA-3.0", "CC-BY-NC-SA-4.0", "CC-BY-ND-1.0", "CC-BY-ND-2.0", "CC-BY-ND-2.5",
    "CC-BY-ND-3.0", "CC-BY-ND-4.0", "CC-BY-SA-1.0", "CC-BY-SA-2.0", "CC-BY-SA-2.5", "CC-BY-SA-3.0",
    "CC-BY-SA-4.0", "CC0-1.0", "CDDL", "ClArtistic", "CPAL-1.0", "EPL", "GFDL", "GMGPL", "GPLv1",
    "GPLv1+", "GPLv2", "GPLv2+", "GPLv3", "GPLv3+", "GPLv3RLE", "GPLv3RLE+", "ISCL", "LGPL20",
    "LGPL20+", "LGPL21", "LGPL21+", "LGPL3", "LGPL3+", "LPPL10", "LPPL11", "LPPL12", "LPPL13",
    "LPPL13a", "LPPL13b", "LPPL13c", "MIT", "MPL10", "MPL11", "MPL20", "NCSA", "NONE", "ODbL",
    "OFL10", "OFL11", "OpenSSL", "OWL", "PD", "PHP202", "PHP30", "PHP301", "PostgreSQL", "PSFL",
    "RUBY", "UNLICENSE", "WTFPL", "WTFPL1", "ZLIB", "ZPL21",
]

####################################################################################################
def _debug_license(name, port):
    """ """
    print(f"===== {name} =====")
    for key, value in port.items():
        if key.startswith("LICENSE"):
            print(f"{key}={value}")
    print(f"======{'=' * len(name)}======\n")

####################################################################################################
def check_licenses(ports, excluded_licenses):
    """ Cross-checks the licenses fields with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-categories-definition
    """
    for name, port in ports.items():
        if "PORTNAME" in port:
            if port["PORTNAME"] in excluded_licenses:
                # Let's skip this port...
                continue

        if "LICENSE" not in port:
            logging.error("Missing LICENSE in Makefile for port %s", name)
            counters["Missing LICENSE"] += 1
            notify_maintainer(port["maintainer"], "Missing LICENSE", name)
        else:
            for license_name in port["LICENSE"].split():
                if license_name not in OFFICIAL_LICENSES and '$' not in license_name:
                    logging.warning("Unofficial license '%s' in Makefile for port %s", license_name, name)
                    counters["Unofficial licenses"] += 1
                    notify_maintainer(port["maintainer"], "Unofficial license", name)

            if "LICENSE_COMB" in port:
                if port["LICENSE_COMB"] == "single":
                    logging.warning("Unnecessary LICENSE_COMB=single in Makefile for port %s", name)
                    counters["Unnecessary LICENSE_COMB=single"] += 1
                    notify_maintainer(port["maintainer"], "Unnecessary LICENSE_COMB=single", name)
                elif port["LICENSE_COMB"] not in ("multi", "dual"):
                    logging.error("Unknown LICENSE_COMB value '%s' in Makefile for port %s (not counted)", port["LICENSE_COMB"], name)
                elif len(port["LICENSE"].split()) == 1:
                    for key in port:
                        if key.startswith("LICENSE_NAME_"):
                            # It's OK, there are additional licenses defined with LICENSE_NAME_* entries
                            continue

                    logging.warning("Unnecessary LICENSE_COMB=%s in Makefile for port %s", port["LICENSE_COMB"], name)
                    counters["Unnecessary LICENSE_COMB=multi"] += 1
                    notify_maintainer(port["maintainer"], "Unnecessary LICENSE_COMB=multi", name)

    logging.info("Found %d ports with missing LICENSE", counters["Missing LICENSE"])
    logging.info("Found %d ports with unofficial licenses", counters["Unofficial licenses"])
    logging.info("Found %d ports with unnecessary LICENSE_COMB=single", counters["Unnecessary LICENSE_COMB=single"])
    logging.info("Found %d ports with unnecessary LICENSE_COMB=multi", counters["Unnecessary LICENSE_COMB=multi"])
