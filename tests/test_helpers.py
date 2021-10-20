"""
from django.test import SimpleTestCase
from gamma_cloudinary.storage.helpers import get_cloudinary_resource_type

class HelpersTestCase(SimpleTestCase):

    def test__get_resource_type_returns_the_right_resource_type(self):
        self.assertEqual(get_cloudinary_resource_type('css/test.css'), 'raw')
        self.assertEqual(get_cloudinary_resource_type('images/image.jpg'), 'image')
        self.assertEqual(get_cloudinary_resource_type('images/test.svg'), 'raw')
        self.assertEqual(get_cloudinary_resource_type('videos/test.mp4'), 'video')
        self.assertEqual(get_cloudinary_resource_type('audio/test.mp3'), 'video')
"""