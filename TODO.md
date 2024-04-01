# PortsTreeLint TODOLIST
Feel free to submit your own ideas!

## Planned changes
* Better Makefiles exploitation by expanding embedded variables when possible locally
  * Using Make to do the job when there are embedded variables

## Probable evolutions
* Checking distfiles availability
* Improving versions comparison for versions with letters -> pnu-vuxml change needed

## Possible evolutions
* Printing the number of notifications and a congratulation message if everything is OK
* Checking the existence of domains in maintainer's email addresses
* Checking the depends fields (extract/patch/fetch/build/run):
  * Between the Index and the Makefiles
  * Against the existence of the dependencies
* Other Makefiles related checks

## Unprobable evolutions
* Adding an option to notify port maintainers by email => will be better done by a wrapping script using the per-maintainer output
* Providing a mechanism to keep track of external events => will be better done by a wrapping script using the per-maintainer output
  * For example, the INDEX:www-site being unavailable since date X
* Side functionalities => not the direct purpose of this tool
  * Checking reported vulnerabilities in dependencies
  * Checking unavailable ports in dependencies
* Checking ports that could be flavourized => no ideas for implementation (yet!)
  * See https://lists.freebsd.org/archives/freebsd-ports/2024-March/005597.html

