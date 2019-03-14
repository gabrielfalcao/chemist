# -*- coding: utf-8 -*-

from tests.functional.scenarios import web_test


@web_test
def test_index(context):
    response = context.http.get('/')
    response.status_code.should.equal(200)
