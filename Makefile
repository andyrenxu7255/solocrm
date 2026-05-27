PYTHON ?= python

.PHONY: install-local test doctor audit graph

install-local:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m pytest -q

doctor:
	solocrm doctor --json

audit:
	solocrm audit summary --json

graph:
	solocrm graph recall --industry 能源 --domain 数据中台 --json
