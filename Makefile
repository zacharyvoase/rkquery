.PHONY: all test

all: test README.rst

test:
	nosetests --with-coverage --with-doctest

README.rst: README.md
	pandoc -f markdown -t rst <README.md >README.rst
