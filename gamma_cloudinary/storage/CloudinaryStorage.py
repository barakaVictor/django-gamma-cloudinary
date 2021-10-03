import os
import json
import requests
import cloudinary
from operator import itemgetter
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri
from django.utils.functional import cached_property
from django.core.signals import setting_changed
from .helpers import get_cloudinary_resource_type

@deconstructible
class CloudinaryStorage(Storage):

    """
    The base cloudinary storage class

    """

    def __init__(self, location=None, base_url=None, options=None):
        self._location = location
        self._base_url = base_url
        setting_changed.connect(self._clear_cached_properties)
    
    def _clear_cached_properties(self, setting, **kwargs):
        """Reset setting based property values."""
        if setting == 'MEDIA_ROOT':
            self.__dict__.pop('base_location', None)
            self.__dict__.pop('location', None)
        elif setting == 'MEDIA_URL':
            self.__dict__.pop('base_url', None)

    def _value_or_setting(self, value, setting):
        return setting if value is None else value

    @cached_property
    def base_location(self):
        return self._value_or_setting(self._location, settings.MEDIA_ROOT)
    
    @cached_property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def upload_folder(self):
        folder = ""
        if 'BASE_STORAGE_LOCATION' in settings.CLOUDINARY_STORAGE.keys():
            folder = itemgetter('BASE_STORAGE_LOCATION')(settings.CLOUDINARY_STORAGE)  
        else:
            folder = os.path.basename(self.base_location) 
        return os.path.join(folder, '') 

    @cached_property
    def base_url(self):
        return os.path.join(self._value_or_setting(self._base_url, settings.MEDIA_URL), '')

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
        url = self.url(name, local=False)
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
        url = self.url(name, local=False)
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
        name = self.url(name, local=False)
        options = {
            'invalidate': True
        }
        response = cloudinary.uploader.destroy(name, **options)
        return response['result'] == 'ok'

    #lesson learnt -> prefer to specify the resource_type when using the SDK as
    #opposed to using the auto option
    def url(self, name, **options):
        """
        Get the full cloudinary url to a resource

        Parameters:
        name(string): The name of the target file used as the public_id when querying Cloudinary

        Returns:
        string: The url to use to access the target resource on Cloudinary
        
        """  
        url = filepath_to_uri(name).lstrip('/')
        if settings.DEBUG:
            return os.path.join(self.base_url, url)
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.upload_path(url),
            default_resource_type=get_cloudinary_resource_type(name)
        )
        return cloudinary_resource.url

    def upload_path(self, name):
        name.replace('\\', '/')
        base = os.path.join(self.upload_folder, self.base_url.lstrip('/')).replace('\\', '/')
        if name.startswith(base):
            return name
        return (os.path.join(base, name).lstrip('/')).replace('\\', '/')
        
    def save_file_types(self, file_props):
        url_types_dict_name = 'remotefiletypes'

        with open(url_types_dict_name, rw)as types_file:
            types_file.write(json.dumps(file_props))
