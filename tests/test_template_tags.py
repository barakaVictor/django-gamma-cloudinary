from django.test import SimpleTestCase
from django.template import Template, Context


class GammaCloudinaryTemplatetagsTestCase(SimpleTestCase):

    def setUp(self):
        pass

    def test_gamma_cloudinary_static_tag(self):
        TEMPLATE = Template("{% load gamma_cloudinary_static %}"
                            "{% gamma_cl_static 'images/why-choose-us.jpg' %}")
        rendered = TEMPLATE.render(Context({}))
        self.assertIn('https://res.cloudinary.com/', rendered)
        self.assertIn('images/why-choose-us.jpg', rendered)