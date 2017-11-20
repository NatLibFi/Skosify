.PHONY: test docs

test:
	python setup.py test

doc:
	rm -rf docs/_build
	$(MAKE) -C docs html
