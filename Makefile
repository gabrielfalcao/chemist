tests: unit functional

unit:
	nosetests tests/unit --rednose

functional:
	nosetests tests/functional --with-spec --spec-color

docs:
	cd docs && make html
	#open docs/build/html/index.html

.PHONY: docs
