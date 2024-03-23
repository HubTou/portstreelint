#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import os

from .library import counters, notify_maintainer

####################################################################################################
def check_description_file(ports, ports_dir):
    """ Checks the description-file field consistency and existence """
    for name, port in ports.items():
        # Use the PORTSDIR we have been told to, rather than the system's one
        port_path = port["port-path"].replace("/usr/ports", ports_dir)
        description_file = port["description-file"].replace("/usr/ports", ports_dir)

        nonexistent = False
        if not description_file.startswith(port_path):
            if not os.path.isfile(description_file):
                nonexistent = True
        elif not os.path.isdir(port_path):
            pass # already reported
        elif not os.path.isfile(description_file):
            nonexistent = True

        if nonexistent:
            logging.error("Nonexistent description-file '%s' for port %s", description_file, name)
            counters["Nonexistent description-file"] += 1
            notify_maintainer(port["maintainer"], "Nonexistent description-file", name)
        else:
            try:
                with open(description_file, encoding="utf-8", errors="ignore") as file:
                    lines = file.read().splitlines()
            except:
                lines = []

            if lines:
                if lines[-1].strip().startswith("https://") or lines[-1].strip().startswith("http://"):
                    logging.error("URL '%s' ending description-file for port %s", lines[-1].strip(), name)
                    counters["URL ending description-file"] += 1
                    notify_maintainer(port["maintainer"], "URL ending description-file", name)
                    del lines[-1]

                text = " ".join(lines)
                text = text.strip()
                if port["comment"] == text:
                    logging.error("description-file content is identical to comment for port %s", name)
                    counters["description-file same as comment"] += 1
                    notify_maintainer(port["maintainer"], "description-file same as comment", name)
                elif len(text) <= len(port["comment"]):
                    logging.error("description-file content is no longer than comment for port %s", name)
                    counters["Too short description-file"] += 1
                    notify_maintainer(port["maintainer"], "Too short description-file", name)

    logging.info("Found %d ports with nonexistent description-file", counters["Nonexistent description-file"])
    logging.info("Found %d ports with URL ending description-file", counters["URL ending description-file"])
    logging.info("Found %d ports with description-file identical to comment", counters["description-file same as comment"])
    logging.info("Found %d ports with too short description-file", counters["Too short description-file"])
