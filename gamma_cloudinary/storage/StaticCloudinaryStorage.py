from django.conf import settings
from django.contrib.staticfiles.utils import check_settings
from .CloudinaryStorage import CloudinaryStorage
from .RewriteToCloudinaryUrlMixin import RewriteToCloudinaryUrlMixin

class StaticCloudinaryStorage(RewriteToCloudinaryUrlMixin, CloudinaryStorage):
    """Cloudinary storage class for static files"""

    def __init__(self, location=None, base_url=None, *args, **kwargs):
        if location is None:
            location = settings.STATIC_ROOT
        if base_url is None:
            base_url = settings.STATIC_URL
        check_settings(base_url)
        super().__init__(location, base_url, *args, **kwargs)
        # CloudinaryStorage fallbacks to MEDIA_ROOT when location
        # is empty, so we restore the empty value.
        if not location:
            self.base_location = None
            self.location = None


