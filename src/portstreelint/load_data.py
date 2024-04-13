#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import datetime
import logging
import os
import re
import sys

import libpnu

from .library import counters, notify_maintainer

####################################################################################################
def load_freebsd_ports_dict(ports_dir):
    """ Returns a dictionary of FreeBSD ports """
    ports = {}

    # Are we running on FreeBSD?
    operating_system = sys.platform
    if not operating_system.startswith("freebsd"):
        raise SystemError

    # On which version?
    os_version = operating_system.replace("freebsd", "")

    # Is the ports index installed?
    ports_index = ports_dir + os.sep + "INDEX-" + os_version
    if not os.path.isfile(ports_index):
        raise FileNotFoundError

    # Loading the ports index:
    with open(ports_index, encoding='utf-8', errors='ignore') as file:
        lines = file.read().splitlines()

    for line in lines:
        # The file format is described at: https://wiki.freebsd.org/Ports/INDEX
        fields = line.split('|')
        if len(fields) != 13:
            logging.error("Ports index line '%s' has %d fields instead of the expected 13. Line ignored", line, len(fields))
        elif fields[0] in ports:
            logging.error("Ports index line '%s' refers to a duplicate distribution-name. Line ignored", line)
        else:
            ports[fields[0]] = \
                {
                    "port-path": fields[1],
                    "installation-prefix": fields[2],
                    "comment": fields[3],
                    "description-file": fields[4],
                    "maintainer": fields[5].lower(),
                    "categories": fields[6],
                    "extract-depends": fields[7],
                    "patch-depends": fields[8],
                    "www-site": fields[9],
                    "fetch-depends": fields[10],
                    "build-depends": fields[11],
                    "run-depends": fields[12],
                }

    counters["FreeBSD ports"] = len(ports)
    logging.info("Loaded %d ports from the FreeBSD Ports INDEX file", len(ports))
    return ports

####################################################################################################
def filter_ports(ports, selected_categories, selected_maintainers, selected_ports):
    """ Filters the list of ports to the specified categories AND maintainers"""
    if selected_categories or selected_maintainers or selected_ports:
        all_ports = " ".join(ports.keys())
        for port in all_ports.split():
            if selected_maintainers:
                if ports[port]["maintainer"] not in selected_maintainers:
                    del ports[port]
                    continue
            if selected_categories:
                match = False
                for category in ports[port]["categories"].split():
                    if category in selected_categories:
                        match = True
                        break
                if not match:
                    del ports[port]
                    continue
            if selected_ports:
                port_id = re.sub(r".*/", "", ports[port]["port-path"])
                if port_id not in selected_ports:
                    del ports[port]

    counters["Selected ports"] = len(ports)
    logging.info("Selected %d ports", len(ports))
    return ports

####################################################################################################
def update_with_makefiles(ports, ports_dir):
    """ Loads selected part of port's Makefiles for cross-checking things """
    for name, port in ports.items():
        # Use the PORTSDIR we have been told to, rather than the system's one
        port_path = port["port-path"].replace("/usr/ports", ports_dir)
        if not os.path.isdir(port_path):
            continue

        port_makefile = port_path + os.sep + 'Makefile'
        if not os.path.isfile(port_makefile):
            logging.error("Nonexistent Makefile for port %s", name)
            counters["Nonexistent Makefile"] += 1
            notify_maintainer(port["maintainer"], "Nonexistent Makefile", name)
        else:
            # Getting the port last modification datetime:
            ports[name]["Last modification"] = datetime.datetime.fromtimestamp(os.path.getmtime(port_makefile)).replace(tzinfo=datetime.timezone.utc)

            lines = libpnu.load_strings_from_file(port_makefile)

            for line in lines:
                group = re.match(r"^([A-Z_]+)=[ 	]*(.*)", line)
                if group is not None: # Makefile variable
                    ports[name][group[1]] = group[2]

    logging.info("Found %d ports with nonexistent Makefile", counters["Nonexistent Makefile"])
    return ports
