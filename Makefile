NAME=portstreelint
SOURCES=src/${NAME}/__init__.py src/${NAME}/main.py src/${NAME}/library.py \
        src/${NAME}/load_config.py src/${NAME}/load_data.py src/${NAME}/check_categories.py \
        src/${NAME}/check_comment.py src/${NAME}/check_description_file.py \
        src/${NAME}/check_installation_prefix.py src/${NAME}/check_licenses.py \
        src/${NAME}/check_maintainer.py src/${NAME}/check_marks.py src/${NAME}/check_plist.py \
        src/${NAME}/check_port_path.py src/${NAME}/check_unchanging_ports.py \
        src/${NAME}/check_vulnerabilities.py src/${NAME}/check_www_site.py \
        src/${NAME}/show_categories.py src/${NAME}/show_maintainers.py \
        src/${NAME}/show_notifications.py src/${NAME}/show_summary.py

# Default action is to show this help message:
.help:
	@echo "Possible targets:"
	@echo "  check-code     Verify PEP 8 compliance (lint)"
	@echo "  check-security Verify security issues (audit)"
	@echo "  check-unused   Find unused code"
	@echo "  check-version  Find required Python version"
	@echo "  check-sloc     Count Single Lines of Code"
	@echo "  checks         Make all the previous tests"
	@echo "  format         Format code"
	@echo "  package        Build package"
	@echo "  upload-test    Upload the package to TestPyPi"
	@echo "  upload         Upload the package to PyPi"
	@echo "  distclean      Remove all generated files"

check-code: /usr/local/bin/pylint
	-pylint ${SOURCES}

lint: check-code

check-security: /usr/local/bin/bandit
	-bandit -r ${SOURCES}

audit: check-security

check-unused: /usr/local/bin/vulture
	-vulture --sort-by-size ${SOURCES}

check-version: /usr/local/bin/vermin
	-vermin ${SOURCES}

check-sloc: /usr/local/bin/pygount
	-pygount --format=summary .

checks: check-code check-security check-unused check-version check-sloc

format: /usr/local/bin/black
	black ${SOURCES}

love:
	@echo "Not war!"

man/${NAME}.8.gz: man/${NAME}.8
	@gzip -k9c man/${NAME}.8 > man/${NAME}.8.gz

package: man/${NAME}.8.gz
	python -m build

upload-test:
	python -m twine upload --repository testpypi dist/*

upload:
	python -m twine upload dist/*

distclean:
	rm -rf build dist src/*.egg-info man/${NAME}.8.gz

