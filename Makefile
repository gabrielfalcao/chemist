deps:
	@(2>&1 which pipenv > /dev/null) || pip install pipenv
	@pipenv install --dev
	@pipenv run python setup.py develop

tests: unit functional


unit:
	pipenv run nosetests tests/unit --rednose

functional:
	pipenv run nosetests tests/functional --with-spec --spec-color

html-docs:
	cd docs && make html

docs: html-docs
	open docs/build/html/index.html

release:
	@rm -rf dist/*
	@./.release
	@make pypi

pypi:
	@pipenv run python setup.py build sdist
	@pipenv run twine upload dist/*.tar.gz

.PHONY: docs
