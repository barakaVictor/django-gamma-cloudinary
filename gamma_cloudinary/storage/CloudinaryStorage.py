import os
import requests
import cloudinary
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from .helpers import get_cloudinary_resource_type

@deconstructible
class CloudinaryStorage(Storage):

    """
    The base cloudinary storage class

    """

    def __init__(self, location=None, options=None):
        self._location = location

    def _value_or_setting(self, value, setting):
        return setting if value is None else value

    @property
    def base_location(self):
        location = self._value_or_setting(self._location, settings.MEDIA_ROOT)
        return os.path.normpath(location).replace('\\', '/')

    def exists(self, name):
        """
        Check wether a file exists in storage

        Parameters:
        name(string): The name of the target file to check for.

        Returns:
        True if the file does exist and False if it does not. 
        It raises an exception incase a http error other than 404 
        is encountered while querying Cloudinary.
        """
        url = self.url(name)
        response = requests.head(url)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def _open(self, name, mode='rb'):
        """
        Mechanism used to open a file

        Arguments:
        name -- The name of the file to open
        mode -- The mode used when opening the file
        
        returns a File object or raises an exception
        if the file does not exist
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
        Saves a file to cloudinary storage

        Arguments:
        name (string): The name of the file to open
        content (file object): The content of the file

        Returns:
        string: the public_id of the file uploaded to cloudinary
        """
        options = {
            'use_filename': True,
            'resource_type': get_cloudinary_resource_type(name),
            'unique_filename': False,
            'overwrite': True,
            'invalidate': True
            }
        folder, name = os.path.split(self.upload_path(name))
        if folder:
            options['folder'] = folder
        response = cloudinary.uploader.upload(content, **options)
        return response['public_id']

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
        """
        Get the full cloudinary url to a resource

        Parameters:
        name(string): The name of the target file used as the public_id when querying Cloudinary

        Returns:
        string: The url to use to access the target resource on Cloudinary
        
        """
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.upload_path(name),
            default_resource_type=get_cloudinary_resource_type(name)
        )
        return cloudinary_resource.url

    def upload_path(self, name):
        """
        Generate a proper path to use when uploading a file

        Parameters:
        name (string): The name of/path to the file to upload

        Returns:
        string: The proper name/path to use to upload a file

        Appends the appropriate url/uri prefix to the name based on the kind of upload
        being conducted i.e A media upload or a static file upload. Static file uploads should
        end up in a folder as indicated by the STATIC_ROOT value in the django settings module,
        same case for media files
        """
        prefix = self.base_location if self.base_location.endswith('/') else self.base_location + '/'
        if not name.startswith(prefix):
            name = prefix + name
        return str(name).replace('\\', '/')
