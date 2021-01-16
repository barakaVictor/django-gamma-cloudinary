from django import template
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.storage import staticfiles_storage

from cloudinary import CloudinaryResource

register = template.Library()

@register.simple_tag(name='gamma_cloudinary_static', takes_context=True)
def gamma_cloudinary_static(context, resource_name, options_dict={}, **options):
    options = dict(options_dict, **options)
    try:
        if context['request'].is_secure() and 'secure' not in options:
            options['secure'] = True
    except KeyError:
        pass
    if not isinstance(resource_name, CloudinaryResource):
        resource_path = staticfiles_storage.upload_path(resource_name)
        resource = CloudinaryResource(
            resource_path,
            default_resource_type=staticfiles_storage._get_resource_type(resource_path)
            )
    return mark_safe(resource.build_url(**options))