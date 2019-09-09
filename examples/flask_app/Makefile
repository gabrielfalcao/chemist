# prepare toolbelt to run in test-mode
current_dir := $(shell pwd)
POETRY_RUN	:= poetry run

default: recreate develop tests docs


recreate: clean  # destroys virtualenv, create new virtualenv and install all python dependencies
	rm -rf .venv poetry.lock
	make dependencies

dependencies: # install and configure poetry, create new virtualenv and install python dependencies
	pip3 install -q -U poetry --no-cache-dir --user
	poetry config settings.virtualenvs.in-project true
	poetry install
	make develop

develop: # install all development dependencies with poetry
	poetry install
	$(POETRY_RUN) python setup.py develop

run:
	$(POETRY_RUN) python web.py


db: drop-db create-db

create-db:
	-createuser chemist
	-@createdb -Ochemist chemist
	poetry run alembic upgrade head

drop-db:
	-dropdb chemist
	-dropuser chemist
k
