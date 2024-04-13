#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import configparser
import logging
import os

import libpnu

####################################################################################################
def generate_config(parameters):
    """ Generates a configuration file with the default + environment + command line parameters """

    content = f"""# PortsTreeLint configuration file

# Check the following URL for the file format:
# https://docs.python.org/3/library/configparser.html#supported-ini-file-structure

[params]
ports_dir = {parameters['Ports dir']}
csv_filename =
debug_level = warning
#debug_level = info
#debug_level = debug

[checks]
categories = {parameters['Checks']['categories']}
comment = {parameters['Checks']['comment']}
description_file = {parameters['Checks']['description-file']}
hostnames = {parameters['Checks']['Hostnames']}
installation_prefix = {parameters['Checks']['installation-prefix']}
licenses = {parameters['Checks']['Licenses']}
maintainer = {parameters['Checks']['maintainer']}
marks = {parameters['Checks']['Marks']}
plist = {parameters['Checks']['plist']}
port_path = {parameters['Checks']['port-path']}
unchanging_ports = {parameters['Checks']['Unchanging ports']}
url = {parameters['Checks']['URL']}
vulnerabilities = {parameters['Checks']['Vulnerabilities']}
www_site = {parameters['Checks']['www-site']}

[limits]
# number of entries:
plist_abuse = {parameters['Limits']['PLIST abuse']}
# number of days:
broken_since = {parameters['Limits']['BROKEN since']}
forbidden_since = {parameters['Limits']['FORBIDDEN since']}
deprecated_since = {parameters['Limits']['DEPRECATED since']}
unchanged_since = {parameters['Limits']['Unchanged since']}

[selections]
# (multilines) lists of space separated values:
categories =
maintainers =
ports =

[exclusions]
# (multilines) list of space separated Vulnerabilities IDs:
vulnerabilities = 92442c4b-6f4a-11db-bd28-0012f06707f0
    bd579366-5290-11d9-ac20-00065be4b5b6
# (multilines) list of space separated PORTNAMEs:
licenses = xfce
"""

    with open(parameters["INI filename"], "w", encoding="utf-8") as file:
        file.write(content)

####################################################################################################
def _string2bool(string):
    """ Converts a string to a boolean without ValueError exception """
    if string.lower() in ("true", "yes", "on", "1"):
        return True

    # .getboolean() would generate an exception if string wasn't in "false", "no", "off", 0"...
    return False

####################################################################################################
def _string2int(string, default):
    """ Converts a string to an int or use a default value without ValueError exception """
    try:
        value = int(string)
    except ValueError:
        value = default

    return value

####################################################################################################
def load_config(parameters):
    """ Loads the user configuration file """
    home = libpnu.get_home_directory()
    if os.name == "nt":
        config_file = home + os.sep + "ptlint.ini"
    else:
        config_file = home + os.sep + ".ptlint"

    if os.path.isfile(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        if "params" in config:
            if "ports_dir" in config["params"]:
                parameters["Ports dir"] = config["params"]["ports_dir"]
            if "csv_filename" in config["params"]:
                parameters["CSV filename"] = config["params"]["csv_filename"]
            if "debug_level" in config["params"]:
                if config["params"]["debug_level"] == "info":
                    logging.disable(logging.DEBUG)
                elif config["params"]["debug_level"] == "debug":
                    logging.disable(logging.NOTSET)
        if "checks" in config:
            if "categories" in config["checks"]:
                parameters["Checks"]["categories"] = _string2bool(config["checks"]["categories"])
            if "comment" in config["checks"]:
                parameters["Checks"]["comment"] = _string2bool(config["checks"]["comment"])
            if "description_file" in config["checks"]:
                parameters["Checks"]["description-file"] = _string2bool(config["checks"]["description_file"])
            if "hostnames" in config["checks"]:
                parameters["Checks"]["Hostnames"] = _string2bool(config["checks"]["hostnames"])
            if "installation_prefix" in config["checks"]:
                parameters["Checks"]["installation-prefix"] = _string2bool(config["checks"]["installation_prefix"])
            if "licenses" in config["checks"]:
                parameters["Checks"]["Licenses"] = _string2bool(config["checks"]["licenses"])
            if "maintainer" in config["checks"]:
                parameters["Checks"]["maintainer"] = _string2bool(config["checks"]["maintainer"])
            if "marks" in config["checks"]:
                parameters["Checks"]["Marks"] = _string2bool(config["checks"]["marks"])
            if "plist" in config["checks"]:
                parameters["Checks"]["plist"] = _string2bool(config["checks"]["plist"])
            if "port_path" in config["checks"]:
                parameters["Checks"]["port-path"] = _string2bool(config["checks"]["port_path"])
            if "unchanging_ports" in config["checks"]:
                parameters["Checks"]["Unchanging ports"] = _string2bool(config["checks"]["unchanging_ports"])
            if "url" in config["checks"]:
                parameters["Checks"]["URL"] = _string2bool(config["checks"]["url"])
            if "vulnerabilities" in config["checks"]:
                parameters["Checks"]["Vulnerabilities"] = _string2bool(config["checks"]["vulnerabilities"])
            if "www_site" in config["checks"]:
                parameters["Checks"]["www-site"] = _string2bool(config["checks"]["www_site"])
        if "limits" in config:
            if "plist_abuse" in config["limits"]:
                parameters["Limits"]["PLIST abuse"] = _string2int(config["limits"]["plist_abuse"], parameters["Limits"]["PLIST abuse"])
            if "broken_since" in config["limits"]:
                parameters["Limits"]["BROKEN since"] = _string2int(config["limits"]["broken_since"], parameters["Limits"]["BROKEN since"])
            if "forbidden_since" in config["limits"]:
                parameters["Limits"]["FORBIDDEN since"] = _string2int(config["limits"]["forbidden_since"], parameters["Limits"]["FORBIDDEN since"])
            if "deprecated_since" in config["limits"]:
                parameters["Limits"]["DEPRECATED since"] = _string2int(config["limits"]["deprecated_since"], parameters["Limits"]["DEPRECATED since"])
            if "unchanged_since" in config["limits"]:
                parameters["Limits"]["Unchanged since"] = _string2int(config["limits"]["unchanged_since"], parameters["Limits"]["Unchanged since"])
        if "selections" in config:
            if "categories" in config["selections"]:
                parameters["Selections"]["Categories"] = config["selections"]["categories"].split()
            if "maintainers" in config["selections"]:
                parameters["Selections"]["Maintainers"] = [m if '@' in m else f"{m}@freebsd.org" for m in config["selections"]["maintainers"].split()]
            if "ports" in config["selections"]:
                parameters["Selections"]["Ports"] = config["selections"]["ports"].split()
        if "exclusions" in config:
            if "vulnerabilities" in config["exclusions"]:
                parameters["Exclusions"]["Vulnerabilities"] = config["exclusions"]["vulnerabilities"].split()
            if "licenses" in config["exclusions"]:
                parameters["Exclusions"]["Licenses"] = config["exclusions"]["licenses"].split()

    return parameters
