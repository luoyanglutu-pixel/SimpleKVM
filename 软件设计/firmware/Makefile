PYTHON ?= python

.PHONY: all bringup dev release test
all: dev
bringup dev release:
	$(PYTHON) ../tools/build.py --profile $@
test:
	$(PYTHON) ../tests/test_behavior.py
