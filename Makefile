PYTHON ?= python

.PHONY: install-local test doctor audit

install-local:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m pytest -q

doctor:
	solocrm doctor --json

audit:
	solocrm audit summary --json
