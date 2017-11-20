tests: unit functional

unit:
	nosetests tests/unit

functional:
	nosetests tests/functional

docs:
	cd docs && make html
	#open docs/build/html/index.html

.PHONY: docs
