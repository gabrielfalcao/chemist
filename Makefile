deps:
	@(2>&1 which pipenv > /dev/null) || pip install pipenv
	@pipenv install --dev
	@pipenv run python setup.py develop

tests: unit functional


unit:
	pipenv run nosetests tests/unit --rednose

db:
	-@psql postgres -c 'create database chemist;'

functional: db
	pipenv run nosetests tests/functional --with-spec --spec-color

html-docs:
	cd docs && make html

docs: html-docs
	open docs/build/html/index.html

upgrade:
	pipenv update
	pipenv lock -r > requirements.txt
	pipenv lock -r --dev > development.txt

release:
	@rm -rf dist/*
	@./.release
	@make pypi

dist: unit
	pipenv run python setup.py build sdist

pypi: dist
	@pipenv run twine upload dist/*.tar.gz

.PHONY: docs dist
