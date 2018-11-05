#!/usr/bin/env make

MAKE 	   ?= make
KNGET_DIR  ?= KngetPy

.PHONY: all
all: kngetx

.PHONY: knget
knget:
	$(MAKE) -C $(KNGET_DIR)

.PHONY: knget-debug
knget-debug:
	$(MAKE) -C $(KNGET_DIR) debug

.PHONY: kngetx
kngetx: knget setup.py
	@ - sed -Ei 's,^ *(__version__.*debug.*),# \1,g' \
					kngetx/__version__.py
	@test -f dist/kngetx-*.tar.gz || python setup.py sdist
	cp $(KNGET_DIR)/dist/* ./dist/

.PHONY: debug
debug: knget-debug
	@ - sed -Ei 's,^# *(__version__.*debug.*),\1,g' \
					kngetx/__version__.py
	@test -f dist/knget-*.tar.gz || python setup.py sdist
	cp $(KNGET_DIR)/dist/* ./dist/

.PHONY: clean
clean:
	- rm -rf dist
	- rm -rf *.egg-info
	$(MAKE) -C $(KNGET_DIR) clean

