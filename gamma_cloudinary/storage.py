import os
import re
import json
import magic
import requests
import mimetypes
import posixpath
import cloudinary
from datetime import datetime
from operator import itemgetter
from urllib.parse import unquote, urlparse
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.signals import setting_changed
from django.utils.encoding import filepath_to_uri
from django.utils.functional import cached_property
from django.utils.deconstruct import deconstructible
from django.core.exceptions import SuspiciousFileOperation
from django.contrib.staticfiles.utils import matches_patterns, check_settings

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
        if settings.DEBUG:
            return self._value_or_setting(self._base_url, settings.MEDIA_URL).lstrip('/')
        return os.path.join(
            root_folder,
            self._value_or_setting(self._base_url, settings.MEDIA_URL).lstrip('/'),
            '').replace('\\', '/')

    def get_mime_type(self, name):
        mimetype = None
        root, ext = os.path.splitext(name)
        if ext == "":
            filepath = self.find_file(name)
            if bool(filepath):
                mimetype = magic.from_buffer(open(filepath, "rb").read(2048), mime=True)
        else:
            mimetype = mimetypes.guess_type(name)[0]
        return mimetype

    def get_resource_type(self, name):
        """
        Returns an appropriate resource_type based on the name of the target
        resource.

        The provided name should have the file extension otherwise
        it will be classified as a raw resource_type by default
        """
        mimetype = self.get_mime_type(name)
        if bool(mimetype):
            resource_type, sub_type = mimetype.split('/')
            if resource_type == 'image':
                #when an SVG image is uploaded as a sprite, i.e.
                #including many different viewboxes for images/icons vectorial instructions
                #but not printing to the screen whatsoever, the ideal resource_type is raw.
                #if image resource_type is used, the image validation fails because when
                #trying to rasterize the image there is nothing display. This results in a failed upload.
                #We therefore go a step further and characterize svgs as a raw resource_type
                if sub_type == 'svg+xml':
                    return 'raw'
                return 'image'
            elif resource_type == 'video' or resource_type == 'audio':
                return 'video'
        return 'raw'

    def find_file(self, name):
        filepath = call_command('findstatic', name, first=True, verbosity=0)
        if name in filepath and os.path.isfile(filepath):
            return filepath
        return None


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

    def get_file_metadata(self, name):
        response = requests.head(self.url(name))
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return None
        return response.headers

    def size(self, name):
        file_metada = self.get_file_metadata(name)
        if bool(file_metada) and hasattr(file_metada, 'Content-Length'):
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
            'resource_type': self.get_resource_type(name),
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
        name = self.url(name)
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
        url = filepath_to_uri(name).lstrip('/')
        if settings.DEBUG:
            return os.path.join(self.base_url, url)
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.upload_path(url),
            default_resource_type=self.get_resource_type(name)
        )
        return cloudinary_resource.url

    def upload_path(self, name):
        name = name.replace('\\', '/').lstrip('/')
        if name.startswith(self.base_url.lstrip('/')):
            return name
        return (os.path.join(self.base_url.lstrip('/'), name).lstrip('/')).replace('\\', '/').lstrip('/')


    def get_available_name(self, name, max_length=None):
        if max_length is None:
            return name
        # Truncate name if max_length exceeded.
        truncation = len(name) - max_length
        if truncation > 0:
            name = name[:-truncation]
            # Entire name was truncated in attempt to find an available filename.
            if not name:
                raise SuspiciousFileOperation(
                    'Storage can not find an available filename for "%s". '
                    'Please make sure that the corresponding file field '
                    'allows sufficient "max_length".' % name
                )
        return name

    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime) of the file specified by
        name. The datetime will be timezone-aware if USE_TZ=True.
        """
        file_metada = self.get_file_metadata(name)
        if bool(file_metada) and hasattr(file_metada, 'Last-Modified'):
            return timezone.make_aware(datetime.strptime(file_metada['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z'))
        return timezone.now()

    """
    def save_manifest(self):
        with open(self.manifest_name, 'w') as manifest:
            json.dump(self.url_to_resource_metadata_map, manifest)


    def read_manifest(self):
        try:
            with open(self.manifest_name) as manifest:
                if manifest is None:
                    return {}
                try:
                    stored = json.load(manifest)
                except json.JSONDecodeError:
                    pass
                else:
                    return stored
        except FileNotFoundError:
            return None
    """

class RewriteToCloudinaryUrlMixin:
    """
    Provides mechanism to rewrite relative paths referencing
    other static assets to their cloudinary urls

    Without this, the paths would end up being broken as on
    cloudinary we no longer use the relative paths as is the
    case when developing locally.
    """
    default_template = """url("%s")"""
    patterns = (
        (
            "*.css", (
                r"""(url\(['"]{0,1}\s*(.*?)["']{0,1}\))""",
                (r"""(@import\s*["']\s*(.*?)["'])""", """@import url("%s")"""),
            )
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._patterns = {}
        for extension, patterns in self.patterns:
            for pattern in patterns:
                if isinstance(pattern, (tuple, list)):
                    pattern, template = pattern
                else:
                    template = self.default_template
                compiled = re.compile(pattern, re.IGNORECASE)
                self._patterns.setdefault(extension, []).append((compiled, template))

    def post_process(self, paths, dry_run=False, **options):

        # build a list of adjustable files
        adjustable_paths = [
            path for path in paths if matches_patterns(path, self._patterns)
        ]

        def path_level(name):
            return len(name.split(os.sep))

        for name in sorted(paths, key=path_level, reverse=True):
            # use the original, local file, not the copied-but-unprocessed
            # file, which might be somewhere far away, like Cloudinary
            storage, path = paths[name]
            with storage.open(path) as original_file:

                # then get the original's file content..
                if hasattr(original_file, 'seek'):
                    original_file.seek(0)

                processed = False

                saved_name  = name
                # ..to apply each replacement pattern to the content
                if name in adjustable_paths:
                    content = original_file.read().decode('utf-8')
                    for extension, patterns in self._patterns.items():
                        if matches_patterns(path, (extension,)):
                            for pattern, template in patterns:
                                converter = self.url_converter(name, template)
                                try:
                                    content = pattern.sub(converter, content)
                                except ValueError as exc:
                                    yield name, None, exc, False

                    # then save the processed result
                    saved_name = self._save(name, ContentFile(content, name=name))
                    processed = True

                yield name, saved_name, processed

    def url_converter(self, name, template=None):
            """
            Return the custom URL converter for the given file name.

            """
            if template is None:
                template = self.default_template

            def converter(matchobj):
                """
                Convert the matched URL to a URL of the referenced resource in
                cloudinary.

                This requires figuring out which files the matched URL resolves
                to and calling the url() method of the storage.
                """
                matched, url = matchobj.groups()

                # Ignore absolute/protocol-relative and data-uri URLs.
                if re.match(r'^[a-z]+:', url):
                    return matched

                url_parts = urlparse(url)
                if url_parts.path.startswith('/'):
                    if url_parts.path.startswith(settings.STATIC_URL):
                        target_name = url_parts.path[len(settings.STATIC_URL):]
                else:
                    # We're using the posixpath module to mix paths and URLs conveniently.
                    source_name = name if os.sep == '/' else name.replace(os.sep, '/')
                    #print(source_name)
                    target_name = posixpath.join(posixpath.dirname(source_name), url_parts.path)

                transformed_url = self.url(target_name)

                if url_parts.query:
                    transformed_url += f"?{url_parts.query}"

                if url_parts.fragment:
                    transformed_url += ('?#' if '?#' in url else '#') + url_parts.fragment

                # Return the cloudinary version to the file
                return template % unquote(transformed_url)

            return converter

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


