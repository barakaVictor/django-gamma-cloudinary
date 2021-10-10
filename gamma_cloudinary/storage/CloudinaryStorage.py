import os
import json
import requests
import cloudinary
from datetime import datetime
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
    manifest_name= 'manifest.json'
    url_to_resource_metadata_map = {}

    def __init__(self, location=None, base_url=None, options=None):
        self._location = location
        self._base_url = base_url
        setting_changed.connect(self._clear_cached_properties)

    def _clear_cached_properties(self, setting, **kwargs):
        """Reset setting based property values."""
        if setting == 'MEDIA_ROOT':
            self.__dict__.pop('base_location', None)
        elif setting == 'MEDIA_URL':
            self.__dict__.pop('base_url', None)

    def _value_or_setting(self, value, setting):
        return setting if value is None else value

    @cached_property
    def base_location(self):
        return self._value_or_setting(self._location, settings.MEDIA_ROOT)

    @cached_property
    def base_url(self):
        root_folder = ""
        if 'BASE_STORAGE_LOCATION' in settings.CLOUDINARY_STORAGE.keys():
            root_folder = itemgetter('BASE_STORAGE_LOCATION')(settings.CLOUDINARY_STORAGE)
        else:
            root_folder = os.path.basename(self.base_location)
        return os.path.join(
            root_folder,
            self._value_or_setting(self._base_url, settings.MEDIA_URL).lstrip('/'),
            '').replace('\\', '/')

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

    def get_file_metadata(self, name):
        response = requests.head(self.url(name, local=False))
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return None
        return response.headers

    def size(self, name):
        file_metada = self.get_file_metadata(name)
        if file_metada:
            return file_metada['Content-Length']
        return None

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
        response.pop('api_key')
        self.url_to_resource_metadata_map[response['secure_url']] = response
        self.save_manifest()
        return response['public_id']

    def delete(self, name):
        assert name, "The name argument is not allowed to be empty."
        name = self.url(name, local=False)
        options = {
            'invalidate': True
        }
        response = cloudinary.uploader.destroy(name, **options)
        return response['result'] == 'ok'


    def get_alternative_name(self, file_root, file_ext):
        """
        Return an alternative filename, by adding an underscore and a random 7
        character alphanumeric string (before the file extension, if one
        exists) to the filename.
        """
        return '%s%s' % (file_root, file_ext)

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
        name = name.replace('\\', '/')
        if name.startswith(self.base_url.lstrip('/')):
            return name
        return (os.path.join(self.base_url.lstrip('/'), name).lstrip('/')).replace('\\', '/').lstrip('/')


    def get_created_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        file_metada = {k:v for (k,v) in self.read_manifest().items() if name in k}
        return datetime.fromisoformat(file_metada['created_at'][:-1]).strptime('%Y-%m-%d %H:%M:%S')

    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        file_metada = self.get_file_metadata(name)
        if file_metada and hasattr(file_metada, 'Last-Modified'):
            return datetime.strptime(file_metada['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z')
        return datetime.now()

    def save_manifest(self):
        with open(self.manifest_name, 'w') as manifest:
            json.dump(self.url_to_resource_metadata_map, manifest)


    def read_manifest(self):
        try:
            with self.open(self.manifest_name) as manifest:
                content = manifest.read().decode()
                if content is None:
                    return {}
                try:
                    stored = json.loads(content)
                except json.JSONDecodeError:
                    pass
                else:
                    return stored
        except FileNotFoundError:
            return None



