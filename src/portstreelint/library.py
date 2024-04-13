#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

# Global dictionary of counters:
counters = {
    "FreeBSD ports": 0,
    "Selected ports": 0,
    "Nonexistent Makefile": 0,
    "Nonexistent port-path": 0,
    "Unusual installation-prefix": 0,
    "Too long comments": 0,
    "Uncapitalized comments": 0,
    "Dot-ended comments": 0,
    "Diverging comments": 0,
    "Nonexistent description-file": 0,
    "URL ending description-file": 0,
    "description-file same as comment": 0,
    "Too short description-file": 0,
    "Nonexistent pkg-plist": 0,
    "PLIST_FILES abuse": 0,
    "Diverging maintainers": 0,
    "Unofficial categories": 0,
    "Diverging categories": 0,
    "Empty www-site": 0,
    "Unresolvable www-site": 0,
    "Unaccessible www-site": 0,
    "Diverging www-site": 0,
    "Marked as BROKEN": 0,
    "Marked as BROKEN for too long": 0,
    "Marked as DEPRECATED": 0,
    "Marked as DEPRECATED for too long": 0,
    "Marked as FORBIDDEN": 0,
    "Marked as FORBIDDEN for too long": 0,
    "Marked as IGNORE": 0,
    "Marked as RESTRICTED": 0,
    "Marked with EXPIRATION_DATE": 0,
    "Unchanged for a long time": 0,
    "Both PORTVERSION and DISTVERSION": 0,
    "Vulnerable port version": 0,
    "Skipped vulnerability checks": 0,
    "Missing LICENSE": 0,
    "Unofficial licenses": 0,
    "Unnecessary LICENSE_COMB=single": 0,
    "Unnecessary LICENSE_COMB=multi": 0,
}

# Global dictionary of notifications to port maintainers:
notifications = {}

####################################################################################################
def notify_maintainer(maintainer, error, port):
    """ Notify a maintainer about an error related to a port """
    if maintainer in notifications:
        if error in notifications[maintainer]:
            if port not in notifications[maintainer][error]:
                notifications[maintainer][error].append(port)
        else:
            notifications[maintainer][error] = [port]
    else:
        notifications[maintainer] = {error: [port]}
