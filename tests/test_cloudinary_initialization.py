from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from gamma_cloudinary.config import setup_cloudinary

class CloudinarySetUpTestCase(SimpleTestCase):

    @override_settings()
    def test_initialization_without_CLOUDINARY_STORAGE_setting(self):
        del settings.CLOUDINARY_STORAGE
        with self.assertRaisesMessage(ImproperlyConfigured, 'In order to use cloudinary storage, you need to provide '
                                                            'CLOUDINARY_STORAGE dictionary with CLOUD_NAME, API_SECRET '
                                                            'and API_KEY in the django settings module or set CLOUDINARY_URL'
                                                            '(or CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET) '
                                                            'environment variables).'):
            setup_cloudinary()

    @override_settings(
        CLOUDINARY_STORAGE={
            'CLOUD_NAME': 'test',
            'API_KEY': 'test_api_key'
        }
    )
    def test_initialization_with_missing_required_CLOUDINARY_STORAGE_required_key_value_pairs(self):
        with self.assertRaisesMessage(ImproperlyConfigured, 'API_SECRET is a required setting in the cloudinary config.'):
            setup_cloudinary()
