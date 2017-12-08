#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy as db
from mock import patch, Mock
from chemist import Model


metadata = db.MetaData()


class FakeEncryptionModel(Model):
    table = db.Table('fake_enc_model', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('name', db.String(80)),
                     db.Column('age', db.Integer))
    encryption = {
        'name': 'fake-encryption-key1'
    }


@patch('chemist.models.nacl.utils.random')
@patch('chemist.models.nacl.secret.SecretBox')
def test_model_get_encryption_box_for_attribute(SecretBox, random):
    ("Model.get_encryption_box_for_attribute should return a SecretBox")

    fem = FakeEncryptionModel()

    box = fem.get_encryption_box_for_attribute('name')

    box.should.equal(SecretBox.return_value)

    SecretBox.assert_called_once_with('fake-encryption-key1')


@patch('chemist.models.nacl.utils.random')
@patch('chemist.models.nacl.secret.SecretBox')
def test_model_encrypt_value(SecretBox, random):
    "Model.encrypt_attribute should use a SecretBox and a nonce to encrypt the data"

    SecretBox.NONCE_SIZE = 4269
    random.return_value = 'a random value'

    class MyEncModel(FakeEncryptionModel):
        get_encryption_box_for_attribute = Mock(
            name='MyEncModel.get_encryption_box_for_attribute')

    box_mock = MyEncModel.get_encryption_box_for_attribute.return_value

    fem = MyEncModel()
    result = fem.encrypt_attribute("name", 'gabriel')

    result.should.equal(box_mock.encrypt.return_value)
    box_mock.encrypt.assert_called_once_with('gabriel', 'a random value')
    random.assert_called_once_with(4269)


@patch('chemist.models.nacl.secret.SecretBox')
def test_model_decrypt_value(SecretBox):
    "Model.decrypt_attribute should use a secret box to decrypt the data"

    SecretBox.NONCE_SIZE = 4269

    class MyEncModel(FakeEncryptionModel):
        get_encryption_box_for_attribute = Mock(
            name='MyEncModel.get_encryption_box_for_attribute')

    box_mock = MyEncModel.get_encryption_box_for_attribute.return_value

    fem = MyEncModel()
    result = fem.decrypt_attribute("name", 'THIS|IS|ENCRYPTED|DATA')

    result.should.equal(box_mock.decrypt.return_value)
    box_mock.decrypt.assert_called_once_with('THIS|IS|ENCRYPTED|DATA')


@patch('chemist.models.nacl.secret.SecretBox')
def test_decrypt_value_already_decrypted(SecretBox):
    "Model.decrypt_attribute should ignore ValueError"

    SecretBox.NONCE_SIZE = 4269

    class MyEncModel(FakeEncryptionModel):
        get_encryption_box_for_attribute = Mock(
            name='MyEncModel.get_encryption_box_for_attribute')

    box_mock = MyEncModel.get_encryption_box_for_attribute.return_value
    box_mock.decrypt.side_effect = ValueError('boom')
    fem = MyEncModel()
    result = fem.decrypt_attribute("name", 'THIS|IS|ENCRYPTED|DATA')

    result.should.equal("THIS|IS|ENCRYPTED|DATA")
    box_mock.decrypt.assert_called_once_with('THIS|IS|ENCRYPTED|DATA')
