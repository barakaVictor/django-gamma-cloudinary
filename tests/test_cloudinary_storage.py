from unittest.mock import patch
from requests.exceptions import HTTPError
from django.test import SimpleTestCase
from django.core.files.base import ContentFile
from gamma_cloudinary.storage import CloudinaryStorage
from .helpers import mock_http_response

class CloudinaryStorageTestCase(SimpleTestCase):
    def setUp(self):
        self.storage = CloudinaryStorage()

    @patch('gamma_cloudinary.storage.cloudinary.CloudinaryResource.build_url')
    def test_url(self, mocked_resource):
        mocked_resource.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/staticfiles/css/test.css'
        self.assertTrue('css/test.css' in self.storage.url('css/test.css'))

    @patch('gamma_cloudinary.storage.cloudinary.uploader.destroy')
    def test_delete_returns_true_on_success(self, mock_destroy):
        mock_destroy.return_value = {'result': 'ok'}
        self.assertTrue(self.storage.delete('css/test.css'))

    @patch('gamma_cloudinary.storage.cloudinary.uploader.destroy')
    def test_delete_returns_false_on_failure(self, mock_destroy):
        mock_destroy.return_value = {'result': 'error'}
        self.assertFalse(self.storage.delete('css/test.css'))

    @patch('gamma_cloudinary.storage.cloudinary.uploader.upload')
    def test___save(self, mock_uploader):
        mock_uploader.return_value = {
          "asset_id": "b5e6d2b39ba3e0869d67141ba7dba6cf",
          "public_id": "eneivicys42bq5f2jpn2",
          "version": 1570979139,
          "version_id": "98f52566f43d8e516a486958a45c1eb9",
          "signature": "abcdefghijklmnopqrstuvwxyz12345",
          "width": 1000,
          "height": 672,
          "format": "jpg",
          "resource_type": "image",
          "created_at": "2017-08-11T12:24:32Z",
          "tags": [],
          "pages": 1,
          "bytes": 350749,
          "type": "upload",
          "etag": "5297bd123ad4ddad723483c176e35f6e",
          "placeholder": False,
          "url": "http://res.cloudinary.com/demo/image/upload/v1570979139/eneivicys42bq5f2jpn2.jpg",
          "secure_url": "https://res.cloudinary.com/demo/image/upload/v1570979139/eneivicys42bq5f2jpn2.jpg",
          "access_mode": "public",
          "original_filename": "sample",
          "eager": [
            { "transformation": "c_pad,h_300,w_400",
              "width": 400,
              "height": 300,
              "url": "http://res.cloudinary.com/demo/image/upload/c_pad,h_300,w_400/v1570979139/eneivicys42bq5f2jpn2.jpg",
              "secure_url": "https://res.cloudinary.com/demo/image/upload/c_pad,h_300,w_400/v1570979139/eneivicys42bq5f2jpn2.jpg" },
            { "transformation": "c_crop,g_north,h_200,w_260",
              "width": 260,
              "height": 200,
              "url": "http://res.cloudinary.com/demo/image/upload/c_crop,g_north,h_200,w_260/v1570979139/eneivicys42bq5f2jpn2.jpg",
              "secure_url": "https://res.cloudinary.com/demo/image/upload/c_crop,g_north,h_200,w_260/v1570979139/eneivicys42bq5f2jpn2.jpg" }]
        }

        self.assertEqual(self.storage._save('css/test.css', ContentFile(b"these are bytes") ), 'eneivicys42bq5f2jpn2.jpg')

    @patch('gamma_cloudinary.storage.requests.get')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.url')
    def test__open_method_returns_a_file_object(self, mock_url, mock_http_get):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_get.return_value= mock_http_response(
            content='Random words from request'
            )
        file = self.storage._open(file_name)
        self.assertTrue(isinstance(file, ContentFile))
        self.assertTrue(file.name == file_name)

    @patch('gamma_cloudinary.storage.requests.get')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.url')
    def test__open_method_raises_an_exception_on_failure(self, mock_url, mock_http_get):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_get.return_value= mock_http_response(
            status=500,
            raise_for_status=HTTPError("Http error")
            )
        self.assertRaises(HTTPError, self.storage._open, file_name)

    @patch('gamma_cloudinary.storage.requests.head')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.url')
    def test_exists_returns_false_on_http_404(self, mock_url, mock_http_head):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_head.return_value= mock_http_response(
            status=404,
            raise_for_status=HTTPError("Http error")
            )
        self.assertFalse(self.storage.exists(file_name))

    @patch('gamma_cloudinary.storage.requests.head')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.url')
    def test_exists_raises_exception_on_other_http_errors(self, mock_url, mock_http_head):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_head.return_value= mock_http_response(
            status=500,
            raise_for_status=HTTPError("Http error")
            )
        self.assertRaises(HTTPError, self.storage.exists, file_name)

    @patch('gamma_cloudinary.storage.requests.head')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.url')
    def test_exists_returns_true_on_http_200(self, mock_url, mock_http_head):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_head.return_value= mock_http_response(
            status=200,
            )
        self.assertTrue(self.storage.exists(file_name))
