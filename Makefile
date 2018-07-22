#clean: clean-pyc clean-build

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +

clean-build:
	rm -rf data/
	rm -rf log/
	rm -rf build/
	rm -rf dist/
	rm -rf __pycache__/
	rm -rf *.egg-info

build: clean-build test
	python timegeopack.py
	sh data-dist.sh
	
lint:
	autopep8 -i *.py
	flake8 --ignore=E501 --exclude=.tox *.py
	#for when I'm a masochist
	#pylint *.py

test: clean-pyc
	python -m pytest --verbose --color=yes $(TEST_PATH)

run:
	python timegeopack.py $1
