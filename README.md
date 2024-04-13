[![PyPI package](https://repology.org/badge/version-for-repo/pypi/python:pnu-portstreelint.svg)](https://repology.org/project/python:pnu-portstreelint/versions)
[![FreeBSD port](https://repology.org/badge/version-for-repo/freebsd/python:pnu-portstreelint.svg)](https://repology.org/project/python:pnu-portstreelint/versions)

# Installation
Once you have installed [Python](https://www.python.org/downloads/) and its packages manager [pip](https://pip.pypa.io/en/stable/installation/),
use one of the following commands, depending on if you want only this tool, the full set of PNU tools, or PNU plus a selection of additional third-parties tools:

```
pip install pnu-portstreelint
pip install PNU
pip install 'PNU[freebsd]' # if you use a platform other than FreeBSD
pip install pytnix
```

# PortsTreeLint(8)

## NAME
portstreelint - FreeBSD ports tree lint

## SYNOPSIS
**portstreelint**
\[--nocfg\]
\[--gencfg|-g FILE\]
\[--show-cat|-C\]
\[--show-mnt|-M\]
\[--cat|-c LIST\]
\[--mnt|-m LIST\]
\[--port|-p LIST\]
\[--tree|-t DIR\]
\[--plist NUM\]
\[--broken NUM\]
\[--deprecated NUM\]
\[--forbidden NUM\]
\[--unchanged NUM\]
\[--check-host|-h\]
\[--check-url|-u\]
\[--output|-o FILE\]
\[--debug\]
\[--info\]
\[--version\]
\[--help|-?\]
\[--\]

The aliases **ptlint** and **ptl** are also available to shorten the command name.

## DESCRIPTION
The **portstreelint** utility checks the FreeBSD ports tree Index
and some parts of the ports' Makefiles for errors and warnings.

By default it will scan the whole port tree, but you can select
a subset of the ports with the options *--cat|-c* for categories,
*--mnt|-m* for maintainers and *--port|-p* for ports.
All these options expect a parameter which can be a single item
or a comma-separated list of items.
If you combine several of these operators they will perform as
a logical AND.

The *--mnt|-m* option defaults to @FreeBSD.org for unspecified
domains.

In order to know which categories or maintainers are available
for selection, you can use the *--show-cat|-C* and *--show-mnt|-M*
options to view all the categories and maintainers with their
number of associated ports.

The two costlier analysis are disabled by default.
You can check if the port's www sites hostnames are resolvable
with the *--check-host|-h* option (takes about 15 minutes on the
whole port tree).
And you can check if the port's www sites URL are available
with the *--check-url|-u* option, which implies the previous one
(takes about 6 hours on the whole port tree).

The checks list includes:
* Nonexistent Makefile
* Nonexistent INDEX:port-path
* Unusual INDEX:installation-prefix (warning)
* Too long INDEX:comments (> 70 characters) (warning)
* Uncapitalized INDEX:comments
* INDEX:comments ending with a dot
* INDEX:comments different from Makefile:COMMENT
* Nonexistent INDEX:description-file
* URL ending INDEX:description-file
* INDEX:description-file content same as INDEX:comment
* INDEX:description-file content no longer than INDEX:comment
* Nonexistent pkg-plist, Makefile:PLIST_FILES/PLIST/PLIST_SUB (debug)
* Makefile:PLIST_FILES abuse (warning)
* INDEX:maintainer different from Makefile:MAINTAINER
* Unofficial categories (warning)
* INDEX:categories different from Makefile:CATEGORIES
* Empty INDEX:www-site
* Unresolvable INDEX:www-site (optional)
* Unaccessible INDEX:www-site (optional)
* INDEX:www-site different from Makefile:WWW
* Ports marked as BROKEN, DEPRECATED, FORBIDDEN, IGNORE, RESTRICTED (info)
* Ports marked with an EXPIRATION_DATE (warning)
* Ports marked as BROKEN, FORBIDDEN or DEPRECATED for too long (warning)
* Ports unchanged for a long time (info)
* Makefile:PORTVERSION and Makefile:DISTVERSION used simultaneously
* VuXML vulnerabilities for the current port versions (warning)
* Missing Makefile:LICENSE
* Unofficial licenses (warning)
* Unnecessary Makefile:LICENSE_COMB=single (warning)
* Unnecessary Makefile:LICENSE_COMB=multi (warning)

It's possible to change the default values for PLIST_FILES abuse,
BROKEN_since, DEPRECATED_since, FORBIDDEN_since and Unchanged_since
with the *--plist*, *--broken*, *--deprecated*, *--forbidden* and
*--unchanged* options, followed by a number of files for the first
one and a number of days for the others. And you can select a port
tree in a location other than */usr/ports* with the *--tree|-t*
option.

Finally, there's a *--output|-o* option to generate a CSV delimited
file with the per-maintainer findings to a specified filename. This
allows for automated processing of the results, such as, for example,
sending warning emails, storing results and displaying only diffs
since previous run...

For convenience, you can put your favourite options in a
configuration file, which will be read before processing the
environment and the command line, unless you use the *--nocfg*
option. You can generate a default configuration file with the
*--gencfg|-g* option followed by a filename. This file also offers
full control over the checks to perform, and a way to discard
false-positive vulnerabilities and unwanted licenses report
messages.

### OPTIONS
Options | Use
------- | ---
--nocfg|Don't use the configuration file
--gencfg\|-g FILE|Generate a default configuration file in FILE
--show-cat\|-C|Show categories with ports count
--show-mnt\|-M|Show maintainers with ports count
--cat\|-c LIST|Select only the comma-separated categories in LIST
--mnt\|-m LIST|Select only the comma-separated maintainers in LIST
--port\|-p LIST|Select only the comma-separated ports in LIST
--tree\|-t DIR|Set ports directory (default=/usr/ports)
--plist NUM|Set PLIST_FILES abuse to NUM files
--broken NUM|Set BROKEN since to NUM days
--deprecated NUM|Set DEPRECATED since to NUM days
--forbidden NUM|Set FORBIDDEN since to NUM days
--unchanged NUM|Set Unchanged since to NUM days
--check-host\|-h|Enable checking hostname resolution (long!)
--check-url\|-u|Enable checking URL (very long!)
--output\|-o|Enable per-maintainer CSV output to FILE
--debug|Enable logging at debug level
--info|Enable logging at info level
--version|Print version and exit
--help\|-?|Print usage and this help message and exit
--|Options processing terminator

## ENVIRONMENT
The *PTLINT_DEBUG* environment variable can be set to any value to enable debug mode.

If the system's *PORTSDIR* environment variable is set, it'll be used instead of the
default "/usr/ports". But the *--tree|-t DIR* option will still override it.

## FILES
The whole port tree under */usr/ports*, or the location indicated by the *PORTSDIR*
environment variable, or the *--tree|-t* argument:
- as root, if you have installed portsnap, update to the last version with "portsnap fetch update"
- or, if you have installed git, clone the latest repository with "git clone https://git.FreeBSD.org/ports.git /usr/ports"

[/usr/ports/INDEX-xx](https://wiki.freebsd.org/Ports/INDEX)
: where xx is the major version of FreeBSD that you are using (as I write this xx=14).
- as root, get the last version with "cd /usr/ports ; make fetchindex"
- or rebuild it from your port tree with "cd /usr/ports ; make index"

${HOME}/.ptlint
: an [INI-style](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure) configuration file.
- Generate a default one with the *--gencfg|-g* option and tweak it to your taste.

## EXIT STATUS
The **portstreelint** utility exits 0 on success, and >0 if an error occurs.

## EXAMPLES
To analyze the full port tree in the background, do:
```Shell
$ nohup portstreelint --info -hu > stdout.txt 2> stderr.txt &
```
Results for this example are available there:
* [stdout output](https://www.frbsd.org/xch/stdout.txt),
* [stderr output](https://www.frbsd.org/xch/stderr.txt) for details.

To analyze the full port tree in the background and generate a CSV
file, do:
```Shell
$ nohup portstreelint -huo csv_results.txt > /dev/null 2>&1 &
```
Results for this example are available there:
* [CSV output](https://www.frbsd.org/xch/csv_results.txt) for machine processing.

To analyze the ports of a specific maintainer identified by id@domain, do:
```Shell
$ portstreelint --info -m id@domain
```

## SEE ALSO
[ports(7)](https://man.freebsd.org/cgi/man.cgi?query=ports),
[lint(1)](https://man.freebsd.org/cgi/man.cgi?query=lint&manpath=Unix+Seventh+Edition),
[portlint(1)](https://www.freshports.org/ports-mgmt/portlint/),
[vuxml(3)](https://github.com/HubTou/vuxml)

[FreeBSD Porter's Handbook](https://docs.freebsd.org/en/books/porters-handbook/)

## STANDARDS
The **portstreelint** utility is not a standard UNIX command.

This implementation tries to follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for [Python](https://www.python.org/) code.

## PORTABILITY
None. Works only on FreeBSD, but who needs anything else?

Packaged for FreeBSD as *pyXX-pnu-portstreelint*.

## HISTORY
While working on the 4th version of the [pysec2vuxml](https://github.com/HubTou/pysec2vuxml) tool,
I noticed there were errors in the FreeBSD port Index,
so I built the [portlint2](https://github.com/HubTou/portlint2) tool to analyze this more thoroughly...

After discussions on the freebsd-ports mailing list an interest in checking port vulnerabilities arose,
which led me to convert that standalone command into a Python package in order to benefit from my
[vuxml](https://github.com/HubTou/vuxml) library.

## LICENSE
It is available under the [3-clause BSD license](https://opensource.org/licenses/BSD-3-Clause).

## AUTHORS
[Hubert Tournier](https://github.com/HubTou)

## CAVEATS
The IGNORE mark check is not reliable because this tool doesn't parse
the ports' Makefiles, but just loads their variables without regard to
the conditional tests that may surround them.

The nonexistent plist check is not very helpful because there are still
undocumented cases where the list is auto generated.

The ports using exotic versioning schemes will be skipped from the
vulnerability check because the library we use for version comparisons
is geared toward Python ports and limited for this usage.
