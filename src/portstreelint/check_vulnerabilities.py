#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import re

import vuxml

from .library import counters, notify_maintainer

####################################################################################################
def _debug_versions(port):
    """ Prints debugging info about a port version """
    pkgnameprefix = ""
    if "PKGNAMEPREFIX" in port:
        pkgnameprefix = port["PKGNAMEPREFIX"]
    portname = ""
    if "PORTNAME" in port:
        portname = port["PORTNAME"]
    pkgnamesuffix = ""
    if "PKGNAMESUFFIX" in port:
        pkgnamesuffix = port["PKGNAMESUFFIX"]
    portversion = ""
    if "PORTVERSION" in port:
        portversion = port["PORTVERSION"]
    portrevision = ""
    if "PORTREVISION" in port:
        portrevision = port["PORTREVISION"]
    portepoch = ""
    if "PORTEPOCH" in port:
        portepoch = port["PORTEPOCH"]

    distversionprefix = ""
    if "DISTVERSIONPREFIX" in port:
        distversionprefix = port["DISTVERSIONPREFIX"]
    distversion = ""
    if "DISTVERSION" in port:
        distversion = port["DISTVERSION"]
    distversionsuffix = ""
    if "DISTVERSIONSUFFIX" in port:
        distversionsuffix = port["DISTVERSIONSUFFIX"]

    logging.debug("  PKGNAMEPREFIX=%s", pkgnameprefix)
    logging.debug("  PORTNAME=%s", portname)
    logging.debug("  PKGNAMESUFFIX=%s", pkgnamesuffix)
    logging.debug("  PORTVERSION=%s", portversion)
    logging.debug("  PORTREVISION=%s", portrevision)
    logging.debug("  PORTEPOCH=%s", portepoch)
    logging.debug("  DISTVERSIONPREFIX=%s", distversionprefix)
    logging.debug("  DISTVERSION=%s", distversion)
    logging.debug("  DISTVERSIONSUFFIX=%s", distversionsuffix)


####################################################################################################
def check_vulnerabilities(ports, excluded_vulnerabilities):
    """ Checks if the port has vulnerabilities reported in VuXML """
    vulns = vuxml.load_vuxml()
    logging.info("Loaded %d vulnerabilities from the FreeBSD VuXML files", len(vulns))

    for name, port in ports.items():
        portname = ""
        if "PORTNAME" in port:
            portname = port["PORTNAME"]
        else:
            logging.debug("No PORTNAME for port %s", name)

        version = ""

        portversion = ""
        if "PORTVERSION" in port:
            portversion = port["PORTVERSION"]
        distversion = ""
        if "DISTVERSION" in port:
            distversion = port["DISTVERSION"]
        portrevision = ""
        if "PORTREVISION" in port:
            portrevision = port["PORTREVISION"]
        portepoch = ""
        if "PORTEPOCH" in port:
            portepoch = port["PORTEPOCH"]

        if portversion and distversion:
            logging.error("Both PORTVERSION and DISTVERSION for port %s", name)
            counters["Both PORTVERSION and DISTVERSION"] += 1
            notify_maintainer(port["maintainer"], "Both PORTVERSION and DISTVERSION", name)

        if not portversion and not distversion:
            logging.debug("No PORTVERSION and DISTVERSION for port %s", name)

        if portversion and '$' not in portversion:
            version = portversion
            if portrevision:
                version += '_' + portrevision

        # Try to figure out ourselves from the port name:
        if not portname or not version:
            version = name

            if portepoch:
                version = re.sub(r"," + portepoch + "$", "", version)
            elif ',' in version:
                version = re.sub(r",[0-9]+$", "", version)
                logging.debug("Port epoch without PORTEPOCH for port %s", name)

            if not portrevision and '_' in version:
                logging.debug("Port revision without PORTREVISION for port %s", name)

            group = re.match(r"^(.*)-([^-]+)$", version)
            if group is not None:
                if not portname:
                    portname = group[1]
                version = group[2]
                logging.debug("portname='%s' version='%s' assumed for port %s", portname, version, name)
            else:
                logging.warning("Unable to get version for port %s. Skipping vulnerability check!", name)
                _debug_versions(port)
                counters["Skipped vulnerability checks"] += 1
                continue

        try:
            vids = vuxml.search_vulns_by_package(vulns, portname, version)
        except Exception as error:
            logging.warning('Encountered "%s" while searching vulnerabilities for port %s. Skipping vulnerability check', error, name)
            counters["Skipped vulnerability checks"] += 1
            continue

        for vid in excluded_vulnerabilities:
            if vid in vids:
                vids.remove(vid)
                logging.debug("Discarded false-positive VuXML vulnerability '%s' for port %s", vid, name)

        for vid in vids:
            logging.warning("Found VuXML vulnerability '%s' for port %s", vid, name)
            if not "FORBIDDEN" in port:
                logging.debug("Vulnerable port not marked as FORBIDDEN for port %s", name)

        if vids:
            counters["Vulnerable port version"] += 1
            notify_maintainer(port["maintainer"], "Vulnerable port", name)

    logging.info("Found %d ports with a vulnerable version", counters["Vulnerable port version"])
    logging.info("Skipped vulnerability check for %d ports", counters["Skipped vulnerability checks"])
