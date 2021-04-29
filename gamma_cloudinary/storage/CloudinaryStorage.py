import os
import requests
import cloudinary
from urllib.parse import urljoin
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
    def storage_folder(self):
        folder = ""
        if 'BASE_STORAGE_LOCATION' in settings.CLOUDINARY_STORAGE.keys():
            folder = itemgetter('BASE_STORAGE_LOCATION')(settings.CLOUDINARY_STORAGE)  
        elif hasattr(settings, 'BASE_DIR'):
            folder = os.path.basename(settings.BASE_DIR) 
        if folder.startswith("/") == False:
            folder = "/"+ folder
        if folder.endswith("/") == False:
            folder += "/"
        return folder 

    @cached_property
    def base_url(self):
        if self._base_url is not None and not self._base_url.endswith('/'):
            self._base_url += "/"
        return urljoin(
            self.storage_folder, 
            self._value_or_setting(self._base_url, settings.MEDIA_URL).lstrip("/")
            )

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
        folder, name = os.path.split(self.custom_path(name, local=False))
        if folder:
            options['folder'] = folder
        response = cloudinary.uploader.upload(content, **options)
        return response['public_id']

    def delete(self, name):
        assert name, "The name argument is not allowed to be empty."
        name = self.custom_path(name, local=False)
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
        local = options['local'] if 'local' in options.keys() else settings.DEBUG   
        if local:
            path = self.custom_path(name)
            if self._base_url is not None:
                if path.startswith(self._base_url.lstrip('/')):
                    pass
                else:
                    path = urljoin(self._base_url, self.custom_path(name))
            return path  
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.custom_path(name, local=False),
            default_resource_type=get_cloudinary_resource_type(name)
        )
        return cloudinary_resource.url

    def custom_path(self, name, local=settings.DEBUG):
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
        url = filepath_to_uri(name)
        if url is not None:
            if local:
                url = url[len(self.storage_folder.lstrip('/').rstrip('/')):] if url.startswith(self.storage_folder.lstrip('/')) else url
                if not url.startswith('/'):
                    url = '/'+url
                if not url.startswith(self.base_url[len(self.storage_folder.rstrip('/')):]):
                    url = urljoin(self.base_url[len(self.storage_folder.rstrip('/')):], url.lstrip('/'))
                if self.get_local_file_name(url) is not None:
                    url = self.get_local_file_name(url)
            else:
                if not url.startswith(self.base_url.lstrip('/')): 
                    url = urljoin(
                        self.base_url, 
                        url.lstrip('/')
                    ).lstrip('/')
        return url
    
    def get_local_file_name(self, path):
        folder, name = os.path.split(path)
        for root, dirs, files in os.walk(os.path.normpath(os.path.join(settings.BASE_DIR, folder.lstrip('/')))):
            for file_name in files:
                if file_name.startswith(name):
                    return os.path.join(folder, file_name)

