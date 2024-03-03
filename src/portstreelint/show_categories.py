#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import textwrap

####################################################################################################
def show_categories(ports):
    """ Pretty prints port categories """
    categories = {}
    for _, port in ports.items():
        for category in port["categories"].split():
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1

    sorted_categories = dict(sorted(categories.items()))
    all_categories = ""
    for category, count in sorted_categories.items():
        all_categories += f"{category}({count}), "
    all_categories = all_categories[:-2]

    print(f"Showing {len(categories)} categories with ports counts:\n")
    for line in textwrap.wrap(all_categories, width=80, break_on_hyphens=False):
        print(line)
