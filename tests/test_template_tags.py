from django.test import SimpleTestCase
from django.template import Template, Context
from gamma_cloudinary.templatetags.gamma_cloudinary_static import gamma_cl_static

class Request:

    def is_secure(self):
        return True

class GammaCloudinaryTemplatetagsTestCase(SimpleTestCase):

    def setUp(self):
        self.context = {
            "request":Request()
        }

    def test_gamma_cloudinary_static_tag_with_no_options(self):
        TEMPLATE = Template("{% load gamma_cloudinary_static %}"
                            "{% gamma_cl_static 'images/why-choose-us.jpg' %}")
        rendered = TEMPLATE.render(Context(self.context))
        self.assertIn('https://res.cloudinary.com/test/image/upload/dpr_auto,f_auto,q_auto,w_auto/v1/test/static/images/why-choose-us.jpg', rendered)

    def test_gamma_cloudinary_static_tag_with_options(self):
        TEMPLATE = Template("{% load gamma_cloudinary_static %}"
                            "{% gamma_cl_static 'images/why-choose-us.jpg' fetch_format='jpg' quality='50' %}")
        rendered = TEMPLATE.render(Context(self.context))
        self.assertIn('https://res.cloudinary.com/test/image/upload/dpr_auto,f_jpg,q_50,w_auto/v1/test/static/images/why-choose-us.jpg', rendered)

    def test_gamma_cloudinary_static_tag_with_options_and_template_variable_name(self):
        TEMPLATE = Template("{% load gamma_cloudinary_static %}"
                            "{% gamma_cl_static 'images/why-choose-us.jpg' fetch_format='jpg' quality='50' as test_with_varname %}"
                            "{{test_with_varname}}"
                            )
        rendered = TEMPLATE.render(Context(self.context))
        self.assertIn('https://res.cloudinary.com/test/image/upload/dpr_auto,f_jpg,q_50,w_auto/v1/test/static/images/why-choose-us.jpg', rendered)

    def test_gamma_cloudinary_static_gamma_cl_static_function(self):
        url = gamma_cl_static('images/why-choose-us.jpg', fetch_format='jpg', quality='50')
        self.assertIn('https://res.cloudinary.com/test/image/upload/dpr_auto,f_jpg,q_50,w_auto/v1/test/static/images/why-choose-us.jpg', url)