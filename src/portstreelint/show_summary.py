#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

from .library import counters

####################################################################################################
def _conditional_print(counter, message):
    """ Print a message if the counter is non zero """
    if counters[counter]:
        value = counters[counter]
        print(f"  {value} port{'' if value == 1 else 's'} {message}")

####################################################################################################
def show_summary(limits):
    """ Pretty prints a summary of findings """
    print(f'Selected {counters["Selected ports"]} ports out of {counters["FreeBSD ports"]} in the FreeBSD port tree, and found:')
    _conditional_print("Nonexistent port-path", "with non existent port-path")
    _conditional_print("Nonexistent Makefile", "without Makefile")
    _conditional_print("Unusual installation-prefix", "with unusual installation-prefix (warning)")
    _conditional_print("Too long comments", "with a comment string exceeding 70 characters (warning)")
    _conditional_print("Uncapitalized comments", "with an uncapitalized comment")
    _conditional_print("Dot-ended comments", "comment ending with a dot")
    _conditional_print("Diverging comments", "with a comment different between the Index and Makefile")
    _conditional_print("Nonexistent description-file", "with non existent description-file")
    _conditional_print("URL ending description-file", "with URL ending description-file")
    _conditional_print("description-file same as comment", "with description-file identical to comment")
    _conditional_print("Too short description-file", "with description-file no longer than comment")
    _conditional_print("Nonexistent pkg-plist", "without pkg-plist/PLIST_FILES/PLIST/PLIST_SUB (info)")
    _conditional_print("PLIST_FILES abuse", f"abusing PLIST_FILES with more than {limits['PLIST abuse'] - 1} entries (warning)")
    _conditional_print("Diverging maintainers", "with a maintainer different between the Index and Makefile")
    _conditional_print("Unofficial categories", "referring to unofficial categories (warning)")
    _conditional_print("Diverging categories", "with categories different between the Index and Makefile")
    _conditional_print("Empty www-site", "with no www-site")
    _conditional_print("Unresolvable www-site", "with an unresolvable www-site hostname")
    _conditional_print("Unaccessible www-site", "with an unaccessible www-site")
    _conditional_print("Diverging www-site", "with a www-site different betwwen the Index and makefile")
    _conditional_print("Marked as BROKEN", "with a BROKEN mark (info)")
    _conditional_print("Marked as BROKEN for too long", f"with a BROKEN mark older than {limits['BROKEN since']} days (warning)")
    _conditional_print("Marked as DEPRECATED", "with a DEPRECATED mark (info)")
    _conditional_print("Marked as DEPRECATED for too long", f"with a DEPRECATED mark older than {limits['DEPRECATED since']} days (warning)")
    _conditional_print("Marked as FORBIDDEN", "with a FORBIDDEN mark (info)")
    _conditional_print("Marked as FORBIDDEN for too long", f"with a FORBIDDEN mark older than {limits['FORBIDDEN since']} days (warning)")
    _conditional_print("Marked as IGNORE", "with a IGNORE mark in some cases (info)")
    _conditional_print("Marked as RESTRICTED", "with a RESTRICTED mark (info)")
    _conditional_print("Marked with EXPIRATION_DATE", "with an EXPIRATION_DATE mark (warning)")
    _conditional_print("Unchanged for a long time", f"with a last modification older than {limits['Unchanged since']} days (info)")
    _conditional_print("Both PORTVERSION and DISTVERSION", "with both PORTVERSION and DISTVERSION")
    _conditional_print("Vulnerable port version", "with a vulnerable version (warning)")
    _conditional_print("Missing LICENSE", "without defined LICENSE")
    _conditional_print("Unofficial licenses", "referring to unofficial licenses (warning)")
    _conditional_print("Unnecessary LICENSE_COMB=single", "with unnecessary LICENSE_COMB=single (warning)")
    _conditional_print("Unnecessary LICENSE_COMB=multi", "with unnecessary LICENSE_COMB=multi (warning)")
