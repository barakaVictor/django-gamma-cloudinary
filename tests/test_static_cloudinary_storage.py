import re
from unittest import mock
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from gamma_cloudinary.storage import StaticCloudinaryStorage
from tests.helpers import find_files

class StaticCloudinaryStorageTestCase(SimpleTestCase):

    def setUp(self):
        self.storage = StaticCloudinaryStorage()

    @override_settings(STATIC_ROOT=None)
    def test_class_instantiation(self):
        instance = StaticCloudinaryStorage()
        self.assertTrue(instance.location==None)
        self.assertTrue(instance.base_location==settings.STATIC_ROOT)

    @mock.patch('gamma_cloudinary.storage.CloudinaryStorage._save')
    def test_post_process(self, mock_save):

        #find static files to pass to the post_process method
        files = find_files()

        #mock the _save method of CloudinaryStorage class to avoid
        #making http requests to cloudinary
        mock_save.side_effect = files.keys()

        processed = self.storage.post_process(files)
        for original_path, _processed_path, _is_processed in processed:
            self.assertIn(original_path, files.keys())

    def test_url_converter_correctly_replaces_relative_static_urls_with_cloudinary_urls(self):
        pattern = re.compile(r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))""", re.IGNORECASE)
        name = 'css\\test.css'
        content = 'url(/static/css/random.css?t=56#test)'
        converter = self.storage.url_converter(name)

        self.assertEqual(
            pattern.sub(converter, content),
            'url("https://res.cloudinary.com/test/raw/upload/v1/test/static/css/random.css?t=56#test")'
            )

    def test_url_converter_correctly_replaces_relative_static_urls_without_leading_slash_with_cloudinary_urls(self):
        pattern = re.compile(r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))""", re.IGNORECASE)
        name = 'css\\test.css'
        content = 'url(/static/css/random.css?t=56#test)'
        converter = self.storage.url_converter(name)
        self.assertEqual(
            pattern.sub(converter, content),
            'url("https://res.cloudinary.com/test/raw/upload/v1/test/static/css/random.css?t=56#test")'
            )

    def test_url_converter_ignores_absolute_urls(self):
        pattern = re.compile(r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))""", re.IGNORECASE)
        name = 'css\\test.css'
        content = 'url(https://gammaadvocates.com/staticfiles/css/random.css?t=56#test)'
        converter = self.storage.url_converter(name)

        self.assertEqual(
            pattern.sub(converter, content),
            'url(https://gammaadvocates.com/staticfiles/css/random.css?t=56#test)'
            )

