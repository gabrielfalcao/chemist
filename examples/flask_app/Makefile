default: recreate dependencies tests docs


.venv/bin/python:
	python3 -mvenv .venv

.venv/bin/alembic: .venv/bin/python
	.venv/bin/pip install flask chemist argon2-cffi pendulum chemist alembic psycopg2-binary

clean:
	rm -rf .venv

recreate: clean  # destroys virtualenv, create new virtualenv and install all python dependencies
	make dependencies

dependencies: .venv/bin/python
	.venv/bin/pip install flask chemist argon2-cffi pendulum chemist

run:.venv/bin/python
	.venv/bin/python web.py


db: drop-db create-db

create-db: .venv/bin/alembic
	-createuser chemist
	-@createdb -Ochemist chemist
	.venv/bin/alembic upgrade head

drop-db: .venv/bin/alembic
	-dropdb chemist
	-dropuser chemist
