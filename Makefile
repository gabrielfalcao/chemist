all: deps tests html-docs

deps:
	@(2>&1 which poetry > /dev/null) || pip install poetry
	@poetry install
	@poetry run python setup.py develop

tests: unit functional


unit:
	poetry run nosetests tests/unit --rednose

functional:
	poetry run nosetests tests/functional --with-spec --spec-color

html-docs:
	poetry run make -C docs html

docs: html-docs
	open docs/build/html/index.html

release: tests html-docs
	@rm -rf dist/*
	@./.release
	@make pypi

dist: unit
	poetry run python setup.py build sdist

pypi: dist
	@poetry run twine upload dist/*.tar.gz

.PHONY: docs dist
