#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import textwrap

from .library import notifications

CSV_FILE_SEPARATOR = ';' # don't use ',' which can appear in port's names

####################################################################################################
def show_notifications():
    """ Pretty prints notifications """
    sorted_notifications = dict(sorted(notifications.items()))
    print("\nIssues per maintainer:")
    for maintainer, details in sorted_notifications.items():
        print(f"  {maintainer}:")
        for issue, ports in details.items():
            print(f"    {issue}:")
            all_ports = " ".join(ports)
            for line in textwrap.wrap(all_ports, width=74, break_on_hyphens=False):
                print(f"      {line}")
        print()

####################################################################################################
def output_notifications(filename):
    """ Output notifications in a CSV file """
    sorted_notifications = dict(sorted(notifications.items()))
    try:
        file = open(filename, "w",  encoding='utf-8')
    except Exception:
        logging.error("Unable to save per-maintainer output to file '%s'", filename)
    else:
        with file:
            print("MAINTAINER" + CSV_FILE_SEPARATOR + "ISSUE" + CSV_FILE_SEPARATOR + "PORT", file=file)
            for maintainer, details in sorted_notifications.items():
                for issue, ports in details.items():
                    for port in ports:
                        print(maintainer + CSV_FILE_SEPARATOR + issue + CSV_FILE_SEPARATOR + port, file=file)
