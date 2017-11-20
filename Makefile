.PHONY: test docs build

test:
	python setup.py test

doc:
	rm -rf docs/_build
	$(MAKE) -C docs html

build:
	python setup.py bdist_wheel
