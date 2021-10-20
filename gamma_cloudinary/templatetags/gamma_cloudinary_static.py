from cloudinary import CloudinaryResource
from django import template
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.storage import staticfiles_storage

register = template.Library()

@register.simple_tag(name='gamma_cl_static', takes_context=True)
def gamma_cloudinary_static(context, resource_name, options_dict=None, **options):

    if options_dict is None:
        options = dict(**options)
    else:
        options = dict(options_dict, **options)
    try:
        if context['request'].is_secure() and 'secure' not in options:
            options['secure'] = True
    except KeyError:
        pass
    if not isinstance(resource_name, CloudinaryResource):
        resource_path = staticfiles_storage.url(resource_name)
        resource = CloudinaryResource(
            resource_path,
            default_resource_type=staticfiles_storage.get_resource_type(resource_path)
            )
    return mark_safe(resource.build_url(**options))