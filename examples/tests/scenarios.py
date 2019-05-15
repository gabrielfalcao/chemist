from sure import scenario
from flask_app.web import application
from flask_app.models import metadata, engine
from flask_app.managers import UserManager


def prepare_db(context):
    set_default_uri('sqlite:///:memory:')
    metadata.drop_all(engine)
    metadata.create_all(engine)


def prepare_user_manager(context):
    context.users = UserManager()


def prepare_api(context):
    context.http = application.test_client()


with_temp_database = scenario(prepare_db)
with_user_manager = scenario([prepare_db, prepare_user_manager])
web_test = scenario([prepare_db, prepare_user_manager, prepare_api])
