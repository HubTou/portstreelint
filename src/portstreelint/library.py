#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import datetime
import logging
import os
import re
import socket
import sys
import textwrap
import urllib.request

import vuxml

# Headers and timeout delay for HTTP(S) requests:
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en;q=1.0, en-US;q=0.8, *;q=0.5",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
}
CONNECTION_TIMEOUT = 10 # seconds

OFFICIAL_CATEGORIES = [
    "accessibility", "afterstep", "arabic", "archivers", "astro", "audio", "benchmarks", "biology",
    "cad", "chinese", "comms", "converters", "databases", "deskutils", "devel", "dns", "docs",
    "editors", "education", "elisp", "emulators", "enlightenment", "finance", "french", "ftp",
    "games", "geography", "german", "gnome", "gnustep", "graphics", "hamradio", "haskell", "hebrew",
    "hungarian", "irc", "japanese", "java", "kde", "kde-applications", "kde-frameworks",
    "kde-plasma", "kld", "korean", "lang", "linux", "lisp", "mail", "mate", "math", "mbone", "misc",
    "multimedia", "net", "net-im", "net-mgmt", "net-p2p", "net-vpn", "news", "parallel", "pear",
    "perl5", "plan9", "polish", "ports-mgmt", "portuguese", "print", "python", "ruby", "rubygems",
    "russian", "scheme", "science", "security", "shells", "spanish", "sysutils", "tcl", "textproc",
    "tk", "ukrainian", "vietnamese", "wayland", "windowmaker", "www", "x11", "x11-clocks",
    "x11-drivers", "x11-fm", "x11-fonts", "x11-servers", "x11-themes", "x11-toolkits", "x11-wm",
    "xfce", "zope",
]

CSV_FILE_SEPARATOR = ';' # don't use ',' which can appear in port's names

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
}

# Global dictionary of notifications to port maintainers:
notifications = {}


####################################################################################################
def load_freebsd_ports_dict():
    """ Returns a dictionary of FreeBSD ports """
    ports = {}

    # Are we running on FreeBSD?
    operating_system = sys.platform
    if not operating_system.startswith("freebsd"):
        raise SystemError

    # On which version?
    os_version = operating_system.replace("freebsd", "")

    # Is the ports list installed?
    ports_index = "/usr/ports/INDEX-" + os_version
    if not os.path.isfile(ports_index):
        raise FileNotFoundError

    # Loading the ports list:
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
def print_categories(ports):
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


####################################################################################################
def print_maintainers(ports):
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
def _notify_maintainer(maintainer, error, port):
    """ Notify a maintainer about an error related to a port """
    if maintainer in notifications:
        if error in notifications[maintainer]:
            if port not in notifications[maintainer][error]:
                notifications[maintainer][error].append(port)
        else:
            notifications[maintainer][error] = [port]
    else:
        notifications[maintainer] = {error: [port]}


####################################################################################################
def update_with_makefiles(ports):
    """ Loads selected part of port's Makefiles for cross-checking things """
    for name, port in ports.items():
        if not os.path.isdir(port["port-path"]):
            continue

        port_makefile = port["port-path"] + os.sep + 'Makefile'
        if not os.path.isfile(port_makefile):
            logging.error("Nonexistent Makefile for port %s", name)
            counters["Nonexistent Makefile"] += 1
            _notify_maintainer(port["maintainer"], "Nonexistent Makefile", name)
        else:
            # Getting the port last modification datetime:
            ports[name]["Last modification"] = datetime.datetime.fromtimestamp(os.path.getmtime(port_makefile)).replace(tzinfo=datetime.timezone.utc)

            with open(port_makefile, encoding='utf-8', errors='ignore') as file:
                lines = file.read().splitlines()

            previous_lines = ""
            for line in lines:
                if not "#" in line:
                    line = previous_lines + line.strip()
                elif "\\#" in line:
                    line = re.sub(r"\\#", "²", line) # horrible kludge!
                    line = previous_lines + re.sub(r"[ 	]*#.*", "", line.strip()) # remove comments
                    line = re.sub(r"²", "\\#", line)
                else:
                    line = previous_lines + re.sub(r"[ 	]*#.*", "", line.strip()) # remove comments
                previous_lines = ""

                if not line:
                    continue

                if line.endswith("\\"): # Continued line
                    previous_lines = re.sub(r"\\$", "", line)
                    continue

                group = re.match(r"^([A-Z_]+)=[ 	]*(.*)", line)
                if group is not None: # Makefile variable
                    ports[name][group[1]] = group[2]

    logging.info("Found %d ports with nonexistent Makefile", counters["Nonexistent Makefile"])
    return ports


####################################################################################################
def check_port_path(ports):
    """ Checks the port-path field existence """
    for name, port in ports.items():
        if not os.path.isdir(port["port-path"]):
            logging.error("Nonexistent port-path '%s' for port %s", port["port-path"], name)
            counters["Nonexistent port-path"] += 1
            _notify_maintainer(port["maintainer"], "Nonexistent port-path", name)

    logging.info("Found %d ports with nonexistent port-path", counters["Nonexistent port-path"])


####################################################################################################
def check_installation_prefix(ports):
    """ Checks the installation-prefix field usualness """
    for name, port in ports.items():
        if port["installation-prefix"] == "/usr/local":
            pass
        elif port["installation-prefix"] == "/compat/linux" and name.startswith("linux"):
            pass
        elif port["installation-prefix"] == "/usr/local/FreeBSD_ARM64" and "-aarch64-" in name:
            pass
        elif port["installation-prefix"].startswith("/usr/local/android") and "droid" in name:
            pass
        elif port["installation-prefix"] == "/var/qmail" and "qmail" in name or name.startswith("queue-fix"):
            pass
        elif port["installation-prefix"] == "/usr" and name.startswith("global-tz-") or name.startswith("zoneinfo-"):
            pass
        else:
            logging.warning("Unusual installation-prefix '%s' for port %s", port["installation-prefix"], name)
            counters["Unusual installation-prefix"] += 1
            _notify_maintainer(port["maintainer"], "Unusual installation-prefix", name)

    logging.info("Found %d ports with unusual installation-prefix", counters["Unusual installation-prefix"])


####################################################################################################
def check_comment(ports):
    """ Cross-checks the comment field with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-comment
    """
    for name, port in ports.items():
        if len(port["comment"]) > 70:
            logging.warning("Over 70 characters comment for port %s", name)
            counters["Too long comments"] += 1
            _notify_maintainer(port["maintainer"], "Too long comments", name)

        if 'a' <= port["comment"][0] <= 'z':
            logging.error("Uncapitalized comment for port %s", name)
            counters["Uncapitalized comments"] += 1
            _notify_maintainer(port["maintainer"], "Uncapitalized comments", name)

        if port["comment"].endswith('.'):
            logging.error("Dot-ended comment for port %s", name)
            counters["Dot-ended comments"] += 1
            _notify_maintainer(port["maintainer"], "Dot-ended comments", name)

        if "COMMENT" in port:
            if '$' in port["COMMENT"]:
                continue # don't try to resolve embedded variables. Ignore check

            # Do not take into escaping backslashes which are used inconsistently
            # in both fields
            if port["comment"].replace("\\", "") != port["COMMENT"].replace("\\", ""):
                logging.error("Diverging comments between Index and Makefile for port %s", name)
                logging.error("... Index:comment    '%s'", port["comment"])
                logging.error("... Makefile:COMMENT '%s'", port["COMMENT"])
                counters["Diverging comments"] += 1
                _notify_maintainer(port["maintainer"], "Diverging comments", name)

    logging.info("Found %d ports with too long comments", counters["Too long comments"])
    logging.info("Found %d ports with uncapitalized comments", counters["Uncapitalized comments"])
    logging.info("Found %d ports with dot-ended comments", counters["Dot-ended comments"])
    logging.info("Found %d ports with diverging comments", counters["Diverging comments"])


####################################################################################################
def check_description_file(ports):
    """ Checks the description-file field consistency and existence """
    for name, port in ports.items():
        nonexistent = False
        if not port["description-file"].startswith(port["port-path"]):
            if not os.path.isfile(port["description-file"]):
                nonexistent = True
        elif not os.path.isdir(port["port-path"]):
            pass # already reported
        elif not os.path.isfile(port["description-file"]):
            nonexistent = True

        if nonexistent:
            logging.error("Nonexistent description-file '%s' for port %s", port["description-file"], name)
            counters["Nonexistent description-file"] += 1
            _notify_maintainer(port["maintainer"], "Nonexistent description-file", name)
        else:
            try:
                with open(port["description-file"], encoding="utf-8", errors="ignore") as file:
                    lines = file.read().splitlines()
            except:
                lines = []

            if lines:
                if lines[-1].strip().startswith("https://") or lines[-1].strip().startswith("http://"):
                    logging.error("URL '%s' ending description-file for port %s", lines[-1].strip(), name)
                    counters["URL ending description-file"] += 1
                    _notify_maintainer(port["maintainer"], "URL ending description-file", name)
                    del lines[-1]

                text = " ".join(lines)
                text = text.strip()
                if port["comment"] == text:
                    logging.error("description-file content is identical to comment for port %s", name)
                    counters["description-file same as comment"] += 1
                    _notify_maintainer(port["maintainer"], "description-file same as comment", name)
                elif len(text) <= len(port["comment"]):
                    logging.error("description-file content is no longer than comment for port %s", name)
                    counters["Too short description-file"] += 1
                    _notify_maintainer(port["maintainer"], "Too short description-file", name)

    logging.info("Found %d ports with nonexistent description-file", counters["Nonexistent description-file"])
    logging.info("Found %d ports with URL ending description-file", counters["URL ending description-file"])
    logging.info("Found %d ports with description-file identical to comment", counters["description-file same as comment"])
    logging.info("Found %d ports with too short description-file", counters["Too short description-file"])


####################################################################################################
def check_plist(ports, plist_abuse):
    """ Checks the package list existence and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/book/#porting-pkg-plist
    """
    for name, port in ports.items():
        if os.path.isdir(port["port-path"]):
            if not os.path.isfile(port["port-path"] + os.sep + "pkg-plist"):
                if not "PLIST_FILES" in port:
                    if not "PLIST" in port and not "PLIST_SUB" in port:
                        logging.debug("Nonexistent pkg-plist/PLIST_FILES/PLIST/PLIST_SUB for port %s", name)
                        counters["Nonexistent pkg-plist"] += 1
                        # Don't notify maintainers because there are too many cases I don't understand!
                else:
                    plist_entries = len(port["PLIST_FILES"].split())
                    if plist_entries >= plist_abuse:
                        logging.warning("PLIST_FILES abuse at %d entries for port %s", plist_entries, name)
                        counters["PLIST_FILES abuse"] += 1
                        _notify_maintainer(port["maintainer"], "PLIST_FILES abuse", name)

    logging.info("Found %d ports with nonexistent pkg-plist (use --debug to list them)", counters["Nonexistent pkg-plist"])
    logging.info("Found %d ports with PLIST_FILES abuse", counters["PLIST_FILES abuse"])


####################################################################################################
def check_maintainer(ports):
    """ Cross-checks the maintainer field with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-maintainer
    """
    for name, port in ports.items():
        if "MAINTAINER" in port:
            if '$' in port["MAINTAINER"]:
                continue # don't try to resolve embedded variables. Ignore check

            if port["maintainer"] != port["MAINTAINER"].lower():
                logging.error("Diverging maintainers between Index and Makefile for port %s", name)
                logging.error("... Index:maintainer    '%s'", port["maintainer"])
                logging.error("... Makefile:MAINTAINER '%s'", port["MAINTAINER"])
                counters["Diverging maintainers"] += 1
                _notify_maintainer(port["maintainer"], "Diverging maintainers", name)
                _notify_maintainer(port["MAINTAINER"], "Diverging maintainers", name)

    logging.info("Found %d ports with diverging maintainers", counters["Diverging maintainers"])


####################################################################################################
def check_categories(ports):
    """ Cross-checks the categories field with the Makefile and compliance with rules
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-categories-definition
    """
    for name, port in ports.items():
        for category in port["categories"].split():
            if category not in OFFICIAL_CATEGORIES:
                logging.warning("Unofficial category '%s' in Index for port %s", category, name)
                counters["Unofficial categories"] += 1
                _notify_maintainer(port["maintainer"], "Unofficial category", name)

        if "CATEGORIES" in port:
            if '$' in port["CATEGORIES"]:
                continue # don't try to resolve embedded variables. Ignore check

            if port["categories"] != port["CATEGORIES"]:
                logging.error("Diverging categories between Index and Makefile for port %s", name)
                logging.error("... Index:categories    '%s'", port["categories"])
                logging.error("... Makefile:CATEGORIES '%s'", port["CATEGORIES"])
                counters["Diverging categories"] += 1
                _notify_maintainer(port["maintainer"], "Diverging categories", name)

            for category in port["CATEGORIES"].split():
                if category not in OFFICIAL_CATEGORIES:
                    logging.warning("Unofficial category '%s' in Makefile for port %s", category, name)
                    counters["Unofficial categories"] += 1
                    _notify_maintainer(port["maintainer"], "Unofficial category", name)

    logging.info("Found %d ports with unofficial categories", counters["Unofficial categories"])
    logging.info("Found %d ports with diverging categories", counters["Diverging categories"])


####################################################################################################
def _resolve_hostname(hostname):
    """ Resolve the hostname into an IP address or raise a NameError exception """
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror as error:
        error_message = re.sub(r".*] ", "", str(error))
        raise NameError(error_message) from error

    return ip_address


####################################################################################################
def _handle_url_errors(port_name, www_site, error, maintainer):
    """ Decides what to do with the multiple possible fetching errors """
    is_unaccessible = False
    reason = "Unaccessible www-site"
    if error.lower().startswith("http error"):
        error_code = re.sub(r"http error ","", error.lower())
        error_message = re.sub(r".*: *", "", error_code)
        error_code = re.sub(r":.*","", error_code)
        if error_code == "404":
            reason = "HTTP Error 404 (Not found) on www-site"
            logging.error("%s '%s' for port %s", reason, www_site, port_name)
            is_unaccessible = True
        elif error_code == "410":
            reason = "HTTP Error 410 (Gone) on www-site"
            logging.error("%s '%s' for port %s", reason, www_site, port_name)
            is_unaccessible = True
        elif error_code == "401":
            reason = "HTTP Error 401 (Unauthorized) on www-site"
            logging.error("%s '%s' for port %s", reason, www_site, port_name)
            is_unaccessible = True
        elif error_code == "403":
            reason = "HTTP Error 403 (Forbidden) on www-site"
            logging.error("%s '%s' for port %s", reason, www_site, port_name)
            is_unaccessible = True
        elif error_code == "451":
            reason = "HTTP Error 451 (Unavailable for legal reasons) on www-site"
            logging.error("%s '%s' for port %s", reason, www_site, port_name)
            is_unaccessible = True
        elif error_code == "301":
            reason = "HTTP Error 301 (Moved permanently) on www-site"
            logging.warning("%s '%s' for port %s", reason, www_site, port_name)
        elif error_code == "308":
            reason = "HTTP Error 308 (Permanent redirect) on www-site"
            logging.warning("%s '%s' for port %s", reason, www_site, port_name)
        else:
            # we don't consider 3xx, 5xx, and remaining 4xx errors to be a reliable sign
            # of a definitive www-site issue
            reason = "HTTP Error " + error_code + " (" + error_message + ") on www-site"
            logging.warning("%s '%s' for port %s", reason, www_site, port_name)
    elif error == "<urlopen error [Errno 8] Name does not resolve>":
        reason = "Unresolvable www-site"
        logging.error("%s '%s' for port %s", reason, www_site, port_name)
        counters["Unresolvable www-site"] += 1
    else:
        logging.debug("%s (%s) '%s' for port %s", reason, error, www_site, port_name)

    if is_unaccessible:
        _notify_maintainer(maintainer, reason, port_name)

    return is_unaccessible


####################################################################################################
def check_www_site(ports, check_host, check_url):
    """ Checks the www-site field existence
    Rules at https://docs.freebsd.org/en/books/porters-handbook/makefiles/#makefile-www
    """
    unresolvable_hostnames = []
    url_ok = []
    url_ko = {}
    for name, port in ports.items():
        if port["www-site"] == "":
            logging.error("Empty www-site for port %s", name)
            counters["Empty www-site"] += 1
            _notify_maintainer(port["maintainer"], "Empty www-site", name)

        elif check_host:
            hostname = re.sub(r"http[s]*://", "", port["www-site"])
            hostname = re.sub(r"/.*", "", hostname)
            hostname = re.sub(r":[0-9]*", "", hostname)
            resolvable = True
            if hostname in unresolvable_hostnames:
                resolvable = False
            else:
                try:
                    _ = _resolve_hostname(hostname)
                except NameError:
                    resolvable = False
                    unresolvable_hostnames.append(hostname)

            if not resolvable:
                logging.error("Unresolvable www-site '%s' for port %s", hostname, name)
                counters["Unresolvable www-site"] += 1
                _notify_maintainer(port["maintainer"], "Unresolvable www-site", name)

            elif port["www-site"] in url_ok:
                pass

            elif port["www-site"] in url_ko:
                if _handle_url_errors(name, port["www-site"], url_ko[port["www-site"]], port["maintainer"]):
                    counters["Unaccessible www-site"] += 1

            elif check_url:
                request = urllib.request.Request(port["www-site"], headers=HTTP_HEADERS)
                try:
                    with urllib.request.urlopen(request, timeout=CONNECTION_TIMEOUT) as http:
                        _ = http.read()
                    url_ok.append(port["www-site"])
                except Exception as error:
                    url_ko[port["www-site"]] = str(error)
                    if _handle_url_errors(name, port["www-site"], str(error), port["maintainer"]):
                        counters["Unaccessible www-site"] += 1

        if "WWW" in port:
            if '$' in port["WWW"]:
                continue # don't try to resolve embedded variables. Ignore check

            if port["www-site"] not in port["WWW"].split():
                logging.error("Diverging www-site between Index and Makefile for port %s", name)
                logging.error("... Index:www-site '%s'", port["www-site"])
                logging.error("... Makefile:WWW   '%s'", port["WWW"])
                counters["Diverging www-site"] += 1
                _notify_maintainer(port["maintainer"], "Diverging www-site", name)

    logging.info("Found %d ports with empty www-site", counters["Empty www-site"])
    if check_host:
        logging.info("Found %d ports with unresolvable www-site", counters["Unresolvable www-site"])
        if check_url:
            logging.info("Found %d ports with unaccessible www-site", counters["Unaccessible www-site"])
    logging.info("Found %d ports with diverging www-site", counters["Diverging www-site"])


####################################################################################################
def check_marks(ports, limits):
    """ Checks the existence of special marks variables (ie. BROKEN, etc.) in Makefiles """
    for name, port in ports.items():
        today = datetime.datetime.now(datetime.timezone.utc)

        if "BROKEN" in port:
            if port["Last modification"] < today - datetime.timedelta(days=limits["BROKEN since"]):
                logging.warning("BROKEN mark '%s' for port %s", port["BROKEN"], name)
                counters["Marked as BROKEN for too long"] += 1
                _notify_maintainer(port["maintainer"], "Marked as BROKEN for too long", name)
            else:
                logging.info("BROKEN mark '%s' for port %s", port["BROKEN"], name)
                counters["Marked as BROKEN"] += 1
                _notify_maintainer(port["maintainer"], "Marked as BROKEN", name)

        if "DEPRECATED" in port:
            if port["Last modification"] < today - datetime.timedelta(days=limits["DEPRECATED since"]):
                logging.warning("DEPRECATED mark '%s' for port %s", port["DEPRECATED"], name)
                counters["Marked as DEPRECATED for too long"] += 1
                _notify_maintainer(port["maintainer"], "Marked as DEPRECATED for too long", name)
            else:
                logging.info("DEPRECATED mark '%s' for port %s", port["DEPRECATED"], name)
                counters["Marked as DEPRECATED"] += 1
                _notify_maintainer(port["maintainer"], "Marked as DEPRECATED", name)

        if "FORBIDDEN" in port:
            if port["Last modification"] < today - datetime.timedelta(days=limits["FORBIDDEN since"]):
                logging.warning("FORBIDDEN mark '%s' for port %s", port["FORBIDDEN"], name)
                counters["Marked as FORBIDDEN for too long"] += 1
                _notify_maintainer(port["maintainer"], "Marked as FORBIDDEN for too long", name)
            else:
                logging.info("FORBIDDEN mark '%s' for port %s", port["FORBIDDEN"], name)
                counters["Marked as FORBIDDEN"] += 1
                _notify_maintainer(port["maintainer"], "Marked as FORBIDDEN", name)

        if "IGNORE" in port:
            logging.info("IGNORE mark '%s' for port %s", port["IGNORE"], name)
            counters["Marked as IGNORE"] += 1
            _notify_maintainer(port["maintainer"], "Containing an IGNORE mark", name)

        if "RESTRICTED" in port:
            logging.info("RESTRICTED mark '%s' for port %s", port["RESTRICTED"], name)
            counters["Marked as RESTRICTED"] += 1
            _notify_maintainer(port["maintainer"], "Marked as RESTRICTED", name)

        if "EXPIRATION_DATE" in port:
            logging.warning("EXPIRATION_DATE mark '%s' for port %s", port["EXPIRATION_DATE"], name)
            counters["Marked with EXPIRATION_DATE"] += 1
            _notify_maintainer(port["maintainer"], "Marked with EXPIRATION_DATE", name)

    logging.info("Found %d ports marked as BROKEN", counters["Marked as BROKEN"])
    logging.info("Found %d ports marked as BROKEN for too long", counters["Marked as BROKEN for too long"])
    logging.info("Found %d ports marked as DEPRECATED", counters["Marked as DEPRECATED"])
    logging.info("Found %d ports marked as DEPRECATED for too long", counters["Marked as DEPRECATED for too long"])
    logging.info("Found %d ports marked as FORBIDDEN", counters["Marked as FORBIDDEN"])
    logging.info("Found %d ports marked as FORBIDDEN for too long", counters["Marked as FORBIDDEN for too long"])
    logging.info("Found %d ports marked as IGNORE", counters["Marked as IGNORE"])
    logging.info("Found %d ports marked as RESTRICTED", counters["Marked as RESTRICTED"])
    logging.info("Found %d ports marked with EXPIRATION_DATE", counters["Marked with EXPIRATION_DATE"])


####################################################################################################
def check_static_ports(ports, unchanged_days):
    """ Checks if the port has been unmodified for too long """
    for name, port in ports.items():
        today = datetime.datetime.now(datetime.timezone.utc)
        if "Last modification" in port:
            if port["Last modification"] < today - datetime.timedelta(days=unchanged_days):
                logging.info("No modification since more than %d days for port %s", unchanged_days, name)
                counters["Unchanged for a long time"] += 1
                _notify_maintainer(port["maintainer"], "Unchanged for a long time", name)

    logging.info("Found %d ports unchanged for a long time", counters["Unchanged for a long time"])


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
def check_vulnerabilities(ports):
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
            _notify_maintainer(port["maintainer"], "Both PORTVERSION and DISTVERSION", name)

        if not portversion and not distversion:
            logging.debug("No PORTVERSION and DISTVERSION for port %s", name)

        if portversion and not '$' in portversion:
            version = portversion

        # Try to figure out ourselves from the port name:
        if not portname or not version:
            version = name

            if portepoch:
                version = re.sub(r"," + portepoch + "$", "", version)
            elif ',' in version:
                version = re.sub(r",[0-9]+$", "", version)
                logging.debug("Port epoch without PORTEPOCH for port %s", name)

            if portrevision:
                version = re.sub(r"_" + portrevision + "$", "", version)
            elif '_' in version:
                version = re.sub(r"_[0-9]+$", "", version)
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

        for vid in vids:
            logging.warning("Found VuXML vulnerability '%s' for port %s", vid, name)
            if not "FORBIDDEN" in port:
                logging.debug("Vulnerable port not marked as FORBIDDEN for port %s", name)

        if vids:
            counters["Vulnerable port version"] += 1
            _notify_maintainer(port["maintainer"], "Vulnerable port", name)

    logging.info("Found %d ports with a vulnerable version", counters["Vulnerable port version"])
    logging.info("Skipped vulnerability check for %d ports", counters["Skipped vulnerability checks"])


####################################################################################################
def print_notifications():
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
        file = open(filename, "w")
    except Exception as error:
        logging.error("Unable to save per-maintainer output to file '%s'", filename)
    else:
        with file:
            print("MAINTAINER" + CSV_FILE_SEPARATOR + "ISSUE" + CSV_FILE_SEPARATOR + "PORT", file=file)
            for maintainer, details in sorted_notifications.items():
                for issue, ports in details.items():
                    for port in ports:
                        print(maintainer + CSV_FILE_SEPARATOR + issue + CSV_FILE_SEPARATOR + port, file=file)


####################################################################################################
def _conditional_print(counter, message):
    """ Print a message if the counter is non zero """
    if counters[counter]:
        value = counters[counter]
        print(f"  {value} port{'' if value == 1 else 's'} {message}")


####################################################################################################
def print_summary(limits):
    """ Pretty prints a summary of findings """
    print(f'\nSelected {counters["Selected ports"]} ports out of {counters["FreeBSD ports"]} in the FreeBSD port tree, and found:')
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
