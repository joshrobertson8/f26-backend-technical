PYTHON ?= python3

.PHONY: all run test smoke sanitize clean

all:
	$(PYTHON) build.py

run: all
	$(PYTHON) build.py run

test:
	$(PYTHON) build.py test

smoke:
	$(PYTHON) build.py smoke

sanitize:
	$(PYTHON) build.py --sanitize smoke

clean:
	$(PYTHON) build.py clean
