# -*- coding: utf-8 -*-

from tests.functional.scenarios import web_test
from flask_app.models import User


@web_test
def test_user_signup(context):
    # Given that I send a post request to user signup
    response = context.http.post('/signup', body=json.dumps({
        'email': 'foo@bar.com',
        'password1': '123insecure',
        'password2': '123insecure',
    }), headers={'content-type': 'application/json'})

    # When I check the response
    response.status_code.should.equal(200)

    # Then the database shoulc contain one user
    users = User.all()
    total_users = len(users)
    assert total_users == 1
