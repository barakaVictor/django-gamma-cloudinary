import os
import requests
import mimetypes
import cloudinary
from django.conf import settings
from django.core.files.storage import Storage
from django.core.signals import setting_changed
from django.utils.functional import cached_property
from django.core.files.base import ContentFile, File
from django.utils.deconstruct import deconstructible

@deconstructible
class CloudinaryStorage(Storage):

    def __init__(self, location=None, options=None):
        self._location = location
       
    def _value_or_setting(self, value, setting):
        return setting if value is None else value

    @property
    def base_location(self):
        location = self._value_or_setting(self._location, settings.MEDIA_ROOT)
        return os.path.normpath(location).replace('\\', '/')

    def exists(self, name):
        url = self.url(name)
        response = requests.head(url)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def _open(self, name, mode='rb'):
        """
        This must return a File object, though in most cases, you’ll want to 
        return some subclass here that implements logic specific to the backend 
        storage system.
        """
        url = self.url(name)
        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e: 
            raise e

        file = ContentFile(response.content)
        file.name = name
        return file

    def _save(self, name, content):
        """
        The super class implementation returns the actual name of name of the file saved 
        (usually the name passed in, but if the storage needs to change the file name 
        return the new name instead). In this case, it returns the public ID of the file
        uploaded to cloudinary
        """
        options = {
            'use_filename': True, 
            'resource_type': self._get_resource_type(name), 
            'unique_filename': False,
            'overwrite': True
            }
        folder, name = os.path.split(self.upload_path(name))
        if folder:
            options['folder'] = folder
        response = cloudinary.uploader.upload(content, **options)
        return response['public_id']

    def _get_resource_type(self, name):
        resource_type = None
        mimetype = mimetypes.guess_type(name)[0]
        if mimetype is not None:
            resource_type, sub_type = mimetype.split('/')
        if resource_type == 'image':
            """
            when an SVG image is uploaded as a sprite, i.e.
            including many different viewboxes for images/icons vectorial instructions 
            but not printing to the screen whatsoever, the ideal resource_type is raw.
            if image resource_type is used, the image validation fails because when 
            trying to rasterize the image there is nothing display. This results in a failed upload.
            We therefore go a step further and characterize svgs as a raw resource_type
            """
            if sub_type == 'svg+xml':
                return 'raw'
            return 'image'
        elif resource_type == 'video' or resource_type == 'audio':
            return 'video'
        else:
            return 'raw'

    def delete(self, name):
        assert name, "The name argument is not allowed to be empty."
        name = self.upload_path(name)
        options = {
            'invalidate': True
        }
        response = cloudinary.uploader.destroy(name, **options)
        return response['result'] == 'ok'

    #lesson learnt -> prefer to specify the resource_type when using the SDK as
    #opposed to using the auto option
    def url(self, name):
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.upload_path(name),
            default_resource_type=self._get_resource_type(name)
        )
        return cloudinary_resource.url

    def upload_path(self, name):
        """
        Appends the appropriate url/uri prefix to the name based on the kind of upload
        being conducted i.e A media upload or a static file upload. Static file uploads should
        end up in a folder as indicated by the STATIC_ROOT value in the django settings module,
        same case for media files 
        """
        prefix = self.base_location if self.base_location.endswith('/') else self.base_location + '/'
        if not name.startswith(prefix):
            name = prefix + name
        return str(name).replace('\\', '/')

    def size(self, name):
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.upload_path(name),
            default_resource_type=self._get_resource_type(name)
        )
        return cloudinary_resource.bytes
