from django import template
from django.utils.html import conditional_escape
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template.base import kwarg_re

register = template.Library()

class GammaStaticNode(template.Node):
    child_nodelists = ()

    def __init__(self, varname=None, path=None, options={}):
        if path is None:
            raise template.TemplateSyntaxError(
                "Static template nodes must be given a path to return.")

        self.path = path
        self.varname = varname
        self.options = options

    def __repr__(self):
        return (
            f'{self.__class__.__name__}(varname={self.varname!r}, path={self.path!r})'
        )

    def url(self, context):
        options = {k: v.resolve(context) for k, v in self.options.items()}
        if context['request'].is_secure() and 'secure' not in options:
            options['secure'] = True
        path = self.path.resolve(context)
        return self.handle_simple(
            path,
            options=options
        )

    def render(self, context):
        url = self.url(context)
        if context.autoescape:
            url = conditional_escape(url)
        if self.varname is None:
            return url
        context[self.varname] = url
        return ''

    @classmethod
    def handle_simple(cls, path, options=None):
        return staticfiles_storage.url(path, **options)

    @classmethod
    def handle_token(cls, parser, token):
        """
        Class method to parse prefix node and return a Node.
        """
        bits = token.split_contents()

        if len(bits) < 2:
            raise template.TemplateSyntaxError(
                "'%s' takes at least one argument (path to file)" % bits[0])

        path = parser.compile_filter(bits[1])

        options = {}
        varname = None
        bits = bits[2:]
        if len(bits) >= 2 and bits[-2] == 'as':
            varname = bits[-1]
            bits = bits[:-2]

        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to "'%s'" tag" % bits[0])
            name, value = match.groups()
            if name:
                options[name] = parser.compile_filter(value)

        return cls(varname, path, options)


@register.tag('gamma_cl_static')
def do_gamma_cl_static(parser, token):
    """
    Join the given path with the STATIC_URL setting.

    Usage::

        {% gamma_cl_static path [as varname] %}

    Examples::

        {% gamma_cl_static "myapp/css/base.css" %}
        {% gamma_cl_static variable_with_path %}
        {% gamma_cl_static "myapp/css/base.css" as admin_base_css %}
        {% gamma_cl_static variable_with_path as varname %}
    """
    return GammaStaticNode.handle_token(parser, token)


def gamma_cl_static(path, **kwargs):
    """
    Given a relative path to a static asset, return the absolute path to the
    asset.
    """
    return GammaStaticNode.handle_simple(path, options=kwargs)
