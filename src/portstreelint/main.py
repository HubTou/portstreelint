#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import getopt
import logging
import os
import sys

import libpnu

from .library import load_freebsd_ports_dict, print_categories, print_maintainers, filter_ports, \
                     update_with_makefiles, check_port_path, check_installation_prefix, \
                     check_comment, check_description_file, check_plist, check_maintainer, \
                     check_categories, check_www_site, check_marks, check_static_ports, \
                     print_notifications, print_summary

# Version string used by the what(1) and ident(1) commands:
ID = "@(#) $Id: portstreelint - FreeBSD ports tree lint v1.0.1 (March 1st, 2024) by Hubert Tournier $"

# Default parameters. Can be overcome by command line options:
parameters = {
    "Show categories": False,
    "Show maintainers": False,
    "Checks": {
        "Hostnames": False,
        "URL": False,
    },
    "Limits": {
        "PLIST abuse": 7, # entries
        "BROKEN since": 6 * 30, # days
        "FORBIDDEN since": 3 * 30, # days
        "DEPRECATED since": 6 * 30, # days
        "Unchanged since": 3 * 365, # days
    },
    "Categories": [],
    "Maintainers": [],
    "Ports": [],
}


####################################################################################################
def _display_help():
    """ Display usage and help """
    #pylint: disable=C0301
    print("usage: portstreelint [--show-cat|-C] [--show-mnt|-M]", file=sys.stderr)
    print("        [--cat|-c LIST] [--mnt|-m LIST] [--port|-p LIST] [--plist NUM]", file=sys.stderr)
    print("        [--broken NUM] [--deprecated NUM] [--forbidden NUM] [--unchanged NUM]", file=sys.stderr)
    print("        [--check-host|-h] [--check-url|-u]", file=sys.stderr)
    print("        [--debug] [--help|-?] [--info] [--version] [--]", file=sys.stderr)
    print("  ------------------  -------------------------------------------------------", file=sys.stderr)
    print("  --show-cat|-C       Show categories with ports count", file=sys.stderr)
    print("  --show-mnt|-M       Show maintainers with ports count", file=sys.stderr)
    print("  --cat|-c LIST       Select only the comma-separated categories in LIST", file=sys.stderr)
    print("  --mnt|-m LIST       Select only the comma-separated maintainers in LIST", file=sys.stderr)
    print("  --port|-p LIST      Select only the comma-separated ports in LIST", file=sys.stderr)
    print("  --plist NUM         Set PLIST_FILES abuse to NUM files", file=sys.stderr)
    print("  --broken NUM        Set BROKEN since to NUM days", file=sys.stderr)
    print("  --deprecated NUM    Set DEPRECATED since to NUM days", file=sys.stderr)
    print("  --forbidden NUM     Set FORBIDDEN since to NUM days", file=sys.stderr)
    print("  --unchanged NUM     Set Unchanged since to NUM days", file=sys.stderr)
    print("  --check-host|-h     Enable checking hostname resolution (long!)", file=sys.stderr)
    print("  --check-url|-u      Enable checking URL (very long!)", file=sys.stderr)
    print("  --debug             Enable logging at debug level", file=sys.stderr)
    print("  --info              Enable logging at info level", file=sys.stderr)
    print("  --version           Print version and exit", file=sys.stderr)
    print("  --help|-?           Print usage and this help message and exit", file=sys.stderr)
    print("  --                  Options processing terminator", file=sys.stderr)
    print(file=sys.stderr)
    #pylint: enable=C0301


####################################################################################################
def _handle_interrupts(signal_number, current_stack_frame):
    """ Prevent SIGINT signals from displaying an ugly stack trace """
    print(" Interrupted!\n", file=sys.stderr)
    sys.exit(0)


####################################################################################################
def _process_environment_variables():
    """ Process environment variables """
    #pylint: disable=C0103, W0602
    global parameters
    #pylint: enable=C0103, W0602

    if "PORTSTREELINT_DEBUG" in os.environ:
        logging.disable(logging.NOTSET)

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
    character_options = "CMc:hm:p:u?"
    string_options = [
        "broken=",
        "cat=",
        "check-host",
        "check-url",
        "debug",
        "deprecated=",
        "forbidden=",
        "help",
        "info",
        "mnt=",
        "port=",
        "plist=",
        "show-cat",
        "show-mnt",
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
            parameters["Categories"] = argument.lower().split(",")

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

        elif option in ("--mnt", "-m"):
            parameters["Maintainers"] = argument.lower().split(",")

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
            parameters["Ports"] = argument.split(",")

        elif option in ("--show-cat", "-C"):
            parameters["Show categories"] = True
            parameters["Show maintainers"] = False

        elif option in ("--show-mnt", "-M"):
            parameters["Show maintainers"] = True
            parameters["Show categories"] = False

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
    program_name = os.path.basename(sys.argv[0])

    libpnu.initialize_debugging(program_name)
    libpnu.handle_interrupt_signals(_handle_interrupts)
    _process_environment_variables()
    _ = _process_command_line()

    # Load the FreeBSD ports INDEX file
    # and verify structural integrity (ie: 13 pipe-separated fields)
    # and unicity of distribution-names
    try:
        ports = load_freebsd_ports_dict()
    except SystemError:
        logging.critical("This program will only run on a FreeBSD operating system")
        sys.exit(1)
    except FileNotFoundError:
        logging.critical("The ports tree is missing. Please install and update it as root ('portsnap fetch extract')")
        sys.exit(1)

    if parameters["Show categories"]:
        # Only print port categories with count of associated ports
        print_categories(ports)
    elif parameters["Show maintainers"]:
        # Only print port maintainers with count of associated ports
        print_maintainers(ports)
    else:
        ports = filter_ports(ports, parameters["Categories"], parameters["Maintainers"], parameters["Ports"])

        # Check the existence of port Makefile and load its variables
        ports = update_with_makefiles(ports)

        # Check the existence of port-path
        check_port_path(ports)

        # Check unusual installation-prefix
        check_installation_prefix(ports)

        # Cross-check comment identity between Index and Makefile
        check_comment(ports)

        # Check the existence of description-file
        check_description_file(ports)

        # Check the package list
        check_plist(ports, parameters["Limits"]["PLIST abuse"])

        # Cross-check maintainer identity between Index and Makefile
        check_maintainer(ports)

        # Cross-check categories identity between Index and Makefile
        # and belonging to the official list of categories
        check_categories(ports)

        # Check that www-site is not empty, that the hostnames exist,
        # that the URL is accessible, and identity between Index and Makefile
        check_www_site(ports, parameters["Checks"]["Hostnames"], parameters["Checks"]["URL"])

        # Check the existence of BROKEN, IGNORE or FORBIDDEN variables in Makefiles
        check_marks(ports, parameters["Limits"])

        # Check static ports
        check_static_ports(ports, parameters["Limits"]["Unchanged since"])

        # Print results per maintainer
        print_notifications()

        # Print summary of findings
        print_summary(parameters["Limits"])

    sys.exit(0)


if __name__ == "__main__":
    main()
