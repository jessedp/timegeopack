#clean: clean-pyc clean-build

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	name '*~' -exec rm --force  {} 

clean-build:

	rm -rf build/
	rm -rf dist/
	rm -rf __pycache__/
	rm -rf *.egg-info

build: clean-build
	/usr/bin/python3.6 timegeopack.py
	/usr/bin/zip data/timegeopack.sqlite3.zip data/timegeopack.sqlite3
	/usr/bin/zip data/cities/topcities.zip data/cities/*

lint:
	autopep8 -i *.py
	flake8 --ignore=E501 --exclude=.tox *.py
	#for when I'm a masochist
	#pylint *.py

test: clean-pyc
	py.test --verbose --color=yes $(TEST_PATH)

run:
	/usr/bin/python3.6 timegeopack.py $1
