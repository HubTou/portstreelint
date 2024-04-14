#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
Contributor: Emanuel Haupt
"""

import getopt
import logging
import os
import sys

import libpnu

from .load_config import generate_config, load_config
from .load_data import load_freebsd_ports_dict, filter_ports, update_with_makefiles
from .check_categories import check_categories
from .check_comment import check_comment
from .check_description_file import check_description_file
from .check_installation_prefix import check_installation_prefix
from .check_licenses import check_licenses
from .check_maintainer import check_maintainer
from .check_marks import check_marks
from .check_plist import check_plist
from .check_port_path import check_port_path
from .check_unchanging_ports import check_unchanging_ports
from .check_vulnerabilities import check_vulnerabilities
from .check_www_site import check_www_site
from .show_categories import show_categories
from .show_maintainers import show_maintainers
from .show_notifications import show_notifications, output_notifications
from .show_summary import show_summary

# Version string used by the what(1) and ident(1) commands:
ID = "@(#) $Id: portstreelint - FreeBSD ports tree lint v1.4.2 (April 14, 2024) by Hubert Tournier $"

# Default parameters. Can be overcome by command line options:
parameters = {
    "INI filename": "",
    "Ports dir": "/usr/ports",
    "CSV filename": "",
    "Show categories": False,
    "Show maintainers": False,

    "Checks": {
		"categories": True,
		"comment": True,
		"description-file": True,
        "Hostnames": False,
		"installation-prefix": True,
		"Licenses": True,
		"maintainer": True,
		"Marks": True,
		"plist": True,
        "port-path": True,
		"Unchanging ports": True,
        "URL": False,
		"Vulnerabilities": True,
		"www-site": True,
    },
    "Limits": {
        "PLIST abuse": 7, # entries
        "BROKEN since": 6 * 30, # days
        "FORBIDDEN since": 3 * 30, # days
        "DEPRECATED since": 6 * 30, # days
        "Unchanged since": 3 * 365, # days
    },
    "Selections": {
        "Categories": [],
        "Maintainers": [],
        "Ports": [],
    },
    "Exclusions": {
        "Vulnerabilities": [],
        "Licenses": [],
    },
}

####################################################################################################
def _display_help():
    """ Display usage and help """
    #pylint: disable=C0301
    print("usage: portstreelint [--nocfg] [--gencfg|-g FILE]", file=sys.stderr)
    print("        [--tree|-t DIR] [--show-cat|-C] [--show-mnt|-M]", file=sys.stderr)
    print("        [--cat|-c LIST] [--mnt|-m LIST] [--port|-p LIST] [--plist NUM]", file=sys.stderr)
    print("        [--broken NUM] [--deprecated NUM] [--forbidden NUM] [--unchanged NUM]", file=sys.stderr)
    print("        [--check-host|-h] [--check-url|-u] [--output|-o FILE]", file=sys.stderr)
    print("        [--debug] [--help|-?] [--info] [--version] [--]", file=sys.stderr)
    print("  ------------------  -------------------------------------------------------", file=sys.stderr)
    print("  --nocfg             Don't use the configuration file", file=sys.stderr)
    print("  --gencfg|-g FILE    Generate a default configuration file in FILE", file=sys.stderr)
    print("  --show-cat|-C       Show categories with ports count", file=sys.stderr)
    print("  --show-mnt|-M       Show maintainers with ports count", file=sys.stderr)
    print("  --cat|-c LIST       Select only the comma-separated categories in LIST", file=sys.stderr)
    print("  --mnt|-m LIST       Select only the comma-separated maintainers in LIST", file=sys.stderr)
    print("  --port|-p LIST      Select only the comma-separated ports in LIST", file=sys.stderr)
    print("  --tree|-t DIR       Set ports directory (default=/usr/ports)", file=sys.stderr)
    print("  --plist NUM         Set PLIST_FILES abuse to NUM files", file=sys.stderr)
    print("  --broken NUM        Set BROKEN since to NUM days", file=sys.stderr)
    print("  --deprecated NUM    Set DEPRECATED since to NUM days", file=sys.stderr)
    print("  --forbidden NUM     Set FORBIDDEN since to NUM days", file=sys.stderr)
    print("  --unchanged NUM     Set Unchanged since to NUM days", file=sys.stderr)
    print("  --check-host|-h     Enable checking hostname resolution (long!)", file=sys.stderr)
    print("  --check-url|-u      Enable checking URL (very long!)", file=sys.stderr)
    print("  --output|-o FILE    Enable per-maintainer CSV output to FILE", file=sys.stderr)
    print("  --debug             Enable logging at debug level", file=sys.stderr)
    print("  --info              Enable logging at info level", file=sys.stderr)
    print("  --version           Print version and exit", file=sys.stderr)
    print("  --help|-?           Print usage and this help message and exit", file=sys.stderr)
    print("  --                  Options processing terminator", file=sys.stderr)
    print(file=sys.stderr)
    #pylint: enable=C0301

####################################################################################################
def _process_environment_variables():
    """ Process environment variables """
    #pylint: disable=C0103, W0602
    global parameters
    #pylint: enable=C0103, W0602

    if "PORTSTREELINT_DEBUG" in os.environ:
        logging.disable(logging.NOTSET)

    if "PORTSDIR" in os.environ:
        if os.environ["PORTSDIR"].endswith(os.sep):
            parameters["Ports dir"] = os.environ["PORTSDIR"][:-1]
        else:
            parameters["Ports dir"] = os.environ["PORTSDIR"]

    logging.debug("_process_environment_variables(): parameters:")
    logging.debug(parameters)

####################################################################################################
def _process_command_line():
    """ Process command line options """
    #pylint: disable=C0103, W0602
    global parameters
    #pylint: enable=C0103, W0602

    # option letters followed by : expect an argument
    # same for option strings followed by =
    character_options = "CMc:g:hm:o:p:t:u?"
    string_options = [
        "broken=",
        "cat=",
        "check-host",
        "check-url",
        "debug",
        "deprecated=",
        "forbidden=",
        "gencfg=",
        "help",
        "info",
        "mnt=",
        "nocfg",
        "output=",
        "port=",
        "plist=",
        "show-cat",
        "show-mnt",
        "tree=",
        "unchanged=",
        "version",
    ]

    try:
        options, remaining_arguments = getopt.getopt(
            sys.argv[1:], character_options, string_options
        )
    except getopt.GetoptError as error:
        logging.critical("Syntax error: %s", error)
        _display_help()
        sys.exit(1)

    for option, argument in options:
        if option == "--debug":
            logging.disable(logging.NOTSET)

        elif option in ("--help", "-?"):
            _display_help()
            sys.exit(0)

        elif option == "--info":
            logging.disable(logging.DEBUG)

        elif option == "--version":
            print(ID.replace("@(" + "#)" + " $" + "Id" + ": ", "").replace(" $", ""))
            sys.exit(0)

        elif option == "--broken":
            try:
                parameters["Checks"]["BROKEN since"] = int(argument)
            except ValueError:
                logging.critical("Syntax error: expecting a number of days after the broken option")
                sys.exit(1)
            if parameters["Checks"]["BROKEN since"] < 30:
                logging.critical("The number of days after the broken option must be >= 30")
                sys.exit(1)

        elif option in ("--cat", "-c"):
            parameters["Selections"]["Categories"] = argument.lower().split(",")

        elif option in ("--check-host", "-h"):
            parameters["Checks"]["Hostnames"] = True

        elif option in ("--check-url", "-u"):
            parameters["Checks"]["Hostnames"] = True
            parameters["Checks"]["URL"] = True

        elif option == "--deprecated":
            try:
                parameters["Checks"]["DEPRECATED since"] = int(argument)
            except ValueError:
                logging.critical("Syntax error: expecting a number of days after the deprecated option")
                sys.exit(1)
            if parameters["Checks"]["DEPRECATED since"] < 30:
                logging.critical("The number of days after the deprecated option must be >= 30")
                sys.exit(1)

        elif option == "--forbidden":
            try:
                parameters["Checks"]["FORBIDDEN since"] = int(argument)
            except ValueError:
                logging.critical("Syntax error: expecting a number of days after the forbidden option")
                sys.exit(1)
            if parameters["Checks"]["FORBIDDEN since"] < 30:
                logging.critical("The number of days after the forbidden option must be >= 30")
                sys.exit(1)

        elif option in ("--gencfg", "-g"):
            if not os.path.exists(argument):
                parameters["INI filename"] = argument
            else:
                logging.critical("--gencfg|-g argument cannot be an existing filesystem item")
                sys.exit(1)

        elif option in ("--mnt", "-m"):
            maintainers = argument.lower().split(",")
            parameters["Selections"]["Maintainers"] = [m if '@' in m else f"{m}@freebsd.org" for m in maintainers]

        elif option == "--nocfg":
            pass # need to be handled BEFORE this function

        elif option in ("--output", "-o"):
            parameters["CSV filename"] = argument

        elif option == "--plist":
            try:
                parameters["Checks"]["PLIST abuse"] = int(argument)
            except ValueError:
                logging.critical("Syntax error: expecting a number of files after the plist option")
                sys.exit(1)
            if parameters["Checks"]["PLIST abuse"] < 3:
                logging.critical("The number of files after the plist option must be >= 3")
                sys.exit(1)

        elif option in ("--port", "-p"):
            parameters["Selections"]["Ports"] = argument.split(",")

        elif option in ("--show-cat", "-C"):
            parameters["Show categories"] = True
            parameters["Show maintainers"] = False

        elif option in ("--show-mnt", "-M"):
            parameters["Show maintainers"] = True
            parameters["Show categories"] = False

        elif option in ("--tree", "-t"):
            if os.path.isdir(argument):
                if argument.endswith(os.sep):
                    parameters["Ports dir"] = argument[:-1]
                else:
                    parameters["Ports dir"] = argument
            else:
                logging.critical("--tree|-t argument must be a directory name")
                sys.exit(1)

        elif option == "--unchanged":
            try:
                parameters["Checks"]["Unchanged since"] = int(argument)
            except ValueError:
                logging.critical("Syntax error: expecting a number of days after the unchanged option")
                sys.exit(1)
            if parameters["Checks"]["Unchanged since"] < 30:
                logging.critical("The number of days after the unchanged option must be >= 30")
                sys.exit(1)

    logging.debug("_process_command_line(): parameters:")
    logging.debug(parameters)
    logging.debug("_process_command_line(): remaining_arguments:")
    logging.debug(remaining_arguments)

    return remaining_arguments

####################################################################################################
def main():
    """ The program's main entry point """
    #pylint: disable=C0103, W0602
    global parameters
    #pylint: enable=C0103, W0602

    program_name = os.path.basename(sys.argv[0])

    libpnu.initialize_debugging(program_name)
    libpnu.handle_interrupt_signals(libpnu.interrupt_handler_function)

    if not "--nocfg" in sys.argv[1:]:
        parameters = load_config(parameters)
    _process_environment_variables()
    _ = _process_command_line()

    # Load the FreeBSD ports INDEX file
    # and verify structural integrity (ie: 13 pipe-separated fields)
    # and unicity of distribution-names
    try:
        ports = load_freebsd_ports_dict(parameters["Ports dir"])
    except SystemError:
        logging.critical("This program will only run on a FreeBSD operating system")
        sys.exit(1)
    except FileNotFoundError:
        logging.critical("The ports tree is missing. Please install and update it as root ('portsnap fetch extract')")
        sys.exit(1)

    if parameters["INI filename"]:
        # Only generate a configuration file
        generate_config(parameters)
    elif parameters["Show categories"]:
        # Only show port categories with count of associated ports
        show_categories(ports)
    elif parameters["Show maintainers"]:
        # Only show port maintainers with count of associated ports
        show_maintainers(ports)
    else:
        ports = filter_ports(
            ports,
            parameters["Selections"]["Categories"],
            parameters["Selections"]["Maintainers"],
            parameters["Selections"]["Ports"]
        )

        # Check the existence of port Makefile and load its variables
        ports = update_with_makefiles(ports, parameters["Ports dir"])

        # Check the existence of port-path
        if parameters["Checks"]["port-path"]:
            check_port_path(ports, parameters["Ports dir"])

        # Check unusual installation-prefix
        if parameters["Checks"]["installation-prefix"]:
            check_installation_prefix(ports)

        # Cross-check comment identity between Index and Makefile
        if parameters["Checks"]["comment"]:
            check_comment(ports)

        # Check the existence of description-file
        if parameters["Checks"]["description-file"]:
            check_description_file(ports, parameters["Ports dir"])

        # Check the package list
        if parameters["Checks"]["plist"]:
            check_plist(ports, parameters["Limits"]["PLIST abuse"], parameters["Ports dir"])

        # Cross-check maintainer identity between Index and Makefile
        if parameters["Checks"]["maintainer"]:
            check_maintainer(ports)

        # Cross-check categories identity between Index and Makefile
        # and belonging to the official list of categories
        if parameters["Checks"]["categories"]:
            check_categories(ports)

        # Check that www-site is not empty, that the hostnames exist,
        # that the URL is accessible, and identity between Index and Makefile
        if parameters["Checks"]["www-site"]:
            check_www_site(ports, parameters["Checks"]["Hostnames"], parameters["Checks"]["URL"])

        # Check the existence of marks variables (ie. BROKEN, etc.) in Makefiles
        if parameters["Checks"]["Marks"]:
            check_marks(ports, parameters["Limits"])

        # Check static ports
        if parameters["Checks"]["Unchanging ports"]:
            check_unchanging_ports(ports, parameters["Limits"]["Unchanged since"])

        # Check vulnerabilities
        if parameters["Checks"]["Vulnerabilities"]:
            check_vulnerabilities(ports, parameters["Exclusions"]["Vulnerabilities"])

        # Check licenses
        if parameters["Checks"]["Licenses"]:
            check_licenses(ports, parameters["Exclusions"]["Licenses"])

        # Print results per maintainer
        show_notifications()

        # Output per maintainer results in a CSV file
        if parameters["CSV filename"]:
            output_notifications(parameters["CSV filename"])

        # Print summary of findings
        show_summary(parameters["Limits"])

    sys.exit(0)

if __name__ == "__main__":
    main()
