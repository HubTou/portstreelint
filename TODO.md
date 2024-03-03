# portstreelint TODOLIST

## Planned changes
* Next version: splitting library.py code into multiple files for modularity
* Version +2: checking distfiles availability

## Probable evolutions

## Possible evolutions
* Providing a mechanism to keep track of external events
  * For example, the INDEX:www-site being unavailable since date X
* Having a configuration file
  * Limits setting
  * Checks disabling
  * Exclusion of ports, maintainers, categories
  * Correction of false positives
* Checking the existence of domains in maintainer's email addresses
* Checking the depends fields (extract/patch/fetch/build/run):
  * between the Index and the Makefiles
  * against the existence of the dependencies
* Other Makefiles related checks

## Unprobable evolutions
* Adding an option to notice port maintainers by email => will be better done by a wrapping script using the per-maintainer output
* Side functionalities => not the direct purpose of this tool
  * Checking reported vulnerabilities in dependencies
  * Checking unavailable ports in dependencies
* Checking ports that could be flavourized => no ideas for implementation (yet!)
  * See https://lists.freebsd.org/archives/freebsd-ports/2024-March/005597.html

Feel free to submit your own ideas!
