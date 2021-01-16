from django.conf import settings
from .CloudinaryStorage import CloudinaryStorage
from .RewriteToCloudinaryUrlMixin import RewriteToCloudinaryUrlMixin

class StaticCloudinaryStorage(RewriteToCloudinaryUrlMixin, CloudinaryStorage):
    """
    Cloudinary storage class for static files
    """

    def __init__(self, location=None, *args, **kwargs):
        if location is None:
            location = settings.STATIC_ROOT
        super().__init__(location, *args, **kwargs)
        # CloudinaryStorage fallbacks to MEDIA_ROOT when location
        # is empty, so we restore the empty value.
        if not location:
            self.location = None


    
   