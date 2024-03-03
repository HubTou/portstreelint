#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import textwrap

####################################################################################################
def show_maintainers(ports):
    """ Pretty prints port maintainers """
    maintainers = {}
    for _, port in ports.items():
        if port["maintainer"] in maintainers:
            maintainers[port["maintainer"]] += 1
        else:
            maintainers[port["maintainer"]] = 1

    sorted_maintainers = dict(sorted(maintainers.items()))
    all_maintainers = ""
    for maintainer, count in sorted_maintainers.items():
        all_maintainers += f"{maintainer}({count}), "
    all_maintainers = all_maintainers[:-2]

    print(f"Showing {len(maintainers)} maintainers with ports counts:\n")
    for line in textwrap.wrap(all_maintainers, width=80, break_on_hyphens=False):
        print(line)
