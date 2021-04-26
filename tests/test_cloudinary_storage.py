from unittest.mock import patch
from requests.exceptions import HTTPError
from django.test import SimpleTestCase
from django.core.files.base import ContentFile
from gamma_cloudinary.storage.CloudinaryStorage import CloudinaryStorage
from .helpers import mock_http_response

class CloudinaryStorageTestCase(SimpleTestCase):
    def setUp(self):
        self.storage = CloudinaryStorage()

    def test_upload_path(self):
        filename = 'css/test.css'
        prefixed_name = self.storage.upload_path(filename)
        self.assertTrue(prefixed_name.startswith(self.storage.base_url))

    @patch('gamma_cloudinary.storage.CloudinaryStorage.cloudinary.CloudinaryResource')
    def test_url(self, mocked_resource):
        mocked_resource.return_value.url = 'https://res.cloudinary.com/cloudname/raw/upload/v1/staticfiles/css/test.css'
        self.assertTrue('css/test.css' in self.storage.url('css/test.css'))

    @patch('gamma_cloudinary.storage.CloudinaryStorage.cloudinary.uploader.destroy')
    def test_delete_returns_true_on_success(self, mock_destroy):
        mock_destroy.return_value = {'result': 'ok'}
        self.assertTrue(self.storage.delete('css/test.css'))

    @patch('gamma_cloudinary.storage.CloudinaryStorage.cloudinary.uploader.destroy')
    def test_delete_returns_false_on_failure(self, mock_destroy):
        mock_destroy.return_value = {'result': 'error'}
        self.assertFalse(self.storage.delete('css/test.css'))

    @patch('gamma_cloudinary.storage.CloudinaryStorage.cloudinary.uploader.upload')
    def test___save(self, mock_uploader):
        mock_uploader.return_value = {'public_id':'test_resource_id'}
        self.assertEqual(self.storage._save('css/test.css', ContentFile(b"these are bytes") ), 'test_resource_id')

    @patch('gamma_cloudinary.storage.CloudinaryStorage.requests.get')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage.url')
    def test__open_method_returns_a_file_object(self, mock_url, mock_http_get):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_get.return_value= mock_http_response(
            content='Random words from request'
            )
        file = self.storage._open(file_name)
        self.assertTrue(isinstance(file, ContentFile))
        self.assertTrue(file.name == file_name)

    @patch('gamma_cloudinary.storage.CloudinaryStorage.requests.get')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage.url')
    def test__open_method_raises_an_exception_on_failure(self, mock_url, mock_http_get):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_get.return_value= mock_http_response(
            status=500,
            raise_for_status=HTTPError("Http error")
            )
        self.assertRaises(HTTPError, self.storage._open, file_name)

    @patch('gamma_cloudinary.storage.CloudinaryStorage.requests.head')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage.url')
    def test_exists_returns_false_on_http_404(self, mock_url, mock_http_head):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_head.return_value= mock_http_response(
            status=404,
            raise_for_status=HTTPError("Http error")
            )
        self.assertFalse(self.storage.exists(file_name))

    @patch('gamma_cloudinary.storage.CloudinaryStorage.requests.head')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage.url')
    def test_exists_raises_exception_on_other_http_errors(self, mock_url, mock_http_head):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_head.return_value= mock_http_response(
            status=500,
            raise_for_status=HTTPError("Http error")
            )
        self.assertRaises(HTTPError, self.storage.exists, file_name)

    @patch('gamma_cloudinary.storage.CloudinaryStorage.requests.head')
    @patch('gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage.url')
    def test_exists_returns_true_on_http_200(self, mock_url, mock_http_head):
        file_name = 'css/test.css'
        mock_url.return_value = 'https://res.cloudinary.com/cloudname/raw/upload/v1/files/css/test.css'
        mock_http_head.return_value= mock_http_response(
            status=200,
            )
        self.assertTrue(self.storage.exists(file_name))
