#!/usr/bin/env python3
""" portstreelint - FreeBSD ports tree lint
License: 3-clause BSD (see https://opensource.org/licenses/BSD-3-Clause)
Author: Hubert Tournier
"""

import logging
import re
import socket
import urllib.request

from .library import counters, notify_maintainer

# Headers and timeout delay for HTTP(S) requests:
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "*/*",
    "Accept-Language": "en;q=1.0, *;q=0.5",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
}
CONNECTION_TIMEOUT = 10 # seconds

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
        notify_maintainer(maintainer, reason, port_name)

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
            notify_maintainer(port["maintainer"], "Empty www-site", name)

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
                notify_maintainer(port["maintainer"], "Unresolvable www-site", name)

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
                notify_maintainer(port["maintainer"], "Diverging www-site", name)

    logging.info("Found %d ports with empty www-site", counters["Empty www-site"])
    if check_host:
        logging.info("Found %d ports with unresolvable www-site", counters["Unresolvable www-site"])
        if check_url:
            logging.info("Found %d ports with unaccessible www-site", counters["Unaccessible www-site"])
    logging.info("Found %d ports with diverging www-site", counters["Diverging www-site"])
