# -*- coding: utf-8 -*-
import uuid

from nose.plugins.skip import SkipTest
import six

from bson import Binary

from mongoengine import *
from tests.utils import MongoDBTestCase

BIN_VALUE = six.b('\xa9\xf3\x8d(\xd7\x03\x84\xb4k[\x0f\xe3\xa2\x19\x85p[J\xa3\xd2>\xde\xe6\x87\xb1\x7f\xc6\xe6\xd9r\x18\xf5')


class TestBinaryField(MongoDBTestCase):
    def test_binary_fields(self):
        """Ensure that binary fields can be stored and retrieved.
        """
        class Attachment(Document):
            content_type = StringField()
            blob = BinaryField()

        BLOB = six.b('\xe6\x00\xc4\xff\x07')
        MIME_TYPE = 'application/octet-stream'

        Attachment.drop_collection()

        attachment = Attachment(content_type=MIME_TYPE, blob=BLOB)
        attachment.save()

        attachment_1 = Attachment.objects().first()
        self.assertEqual(MIME_TYPE, attachment_1.content_type)
        self.assertEqual(BLOB, six.binary_type(attachment_1.blob))

    def test_validation_succeeds(self):
        """Ensure that valid values can be assigned to binary fields.
        """
        class AttachmentRequired(Document):
            blob = BinaryField(required=True)

        class AttachmentSizeLimit(Document):
            blob = BinaryField(max_bytes=4)

        attachment_required = AttachmentRequired()
        self.assertRaises(ValidationError, attachment_required.validate)
        attachment_required.blob = Binary(six.b('\xe6\x00\xc4\xff\x07'))
        attachment_required.validate()

        _5_BYTES = six.b('\xe6\x00\xc4\xff\x07')
        _4_BYTES = six.b('\xe6\x00\xc4\xff')
        self.assertRaises(ValidationError, AttachmentSizeLimit(blob=_5_BYTES).validate)
        AttachmentSizeLimit(blob=_4_BYTES).validate()

    def test_validation_fails(self):
        """Ensure that invalid values cannot be assigned to binary fields."""

        class Attachment(Document):
            blob = BinaryField()

        for invalid_data in (2, u'Im_a_unicode', ['some_str']):
            self.assertRaises(ValidationError, Attachment(blob=invalid_data).validate)

    def test__primary(self):
        class Attachment(Document):
            id = BinaryField(primary_key=True)

        Attachment.drop_collection()
        binary_id = uuid.uuid4().bytes
        att = Attachment(id=binary_id).save()
        self.assertEqual(1, Attachment.objects.count())
        self.assertEqual(1, Attachment.objects.filter(id=att.id).count())
        att.delete()
        self.assertEqual(0, Attachment.objects.count())

    def test_primary_filter_by_binary_pk_as_str(self):
        raise SkipTest("Querying by id as string is not currently supported")

        class Attachment(Document):
            id = BinaryField(primary_key=True)

        Attachment.drop_collection()
        binary_id = uuid.uuid4().bytes
        att = Attachment(id=binary_id).save()
        self.assertEqual(1, Attachment.objects.filter(id=binary_id).count())
        att.delete()
        self.assertEqual(0, Attachment.objects.count())

    def test_match_querying_with_bytes(self):
        class MyDocument(Document):
            bin_field = BinaryField()

        MyDocument.drop_collection()

        doc = MyDocument(bin_field=BIN_VALUE).save()
        matched_doc = MyDocument.objects(bin_field=BIN_VALUE).first()
        self.assertEqual(matched_doc.id, doc.id)

    def test_match_querying_with_binary(self):
        class MyDocument(Document):
            bin_field = BinaryField()

        MyDocument.drop_collection()

        doc = MyDocument(bin_field=BIN_VALUE).save()

        matched_doc = MyDocument.objects(bin_field=Binary(BIN_VALUE)).first()
        self.assertEqual(matched_doc.id, doc.id)

    def test_modify_operation__set(self):
        """Ensures no regression of bug #1127"""
        class MyDocument(Document):
            some_field = StringField()
            bin_field = BinaryField()

        MyDocument.drop_collection()

        doc = MyDocument.objects(some_field='test').modify(
            upsert=True, new=True,
            set__bin_field=BIN_VALUE
        )
        self.assertEqual(doc.some_field, 'test')
        self.assertEqual(doc.bin_field, Binary(BIN_VALUE))

    def test_update_one(self):
        """Ensures no regression of bug #1127"""
        class MyDocument(Document):
            bin_field = BinaryField()

        MyDocument.drop_collection()

        bin_data = six.b('\xe6\x00\xc4\xff\x07')
        doc = MyDocument(bin_field=bin_data).save()

        n_updated = MyDocument.objects(bin_field=bin_data).update_one(bin_field=BIN_VALUE)
        self.assertEqual(n_updated, 1)
        fetched = MyDocument.objects.with_id(doc.id)
        self.assertEqual(fetched.bin_field, Binary(BIN_VALUE))
