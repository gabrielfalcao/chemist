tests: unit functional

unit:
	nosetests tests/unit --rednose

functional:
	nosetests tests/functional --with-spec --spec-color

html-docs:
	cd docs && make html

docs: html-docs
	open docs/build/html/index.html

release:
	@rm -rf dist/*
	@./.release
	@python setup.py build sdist
	@twine upload dist/*.tar.gz

.PHONY: docs
