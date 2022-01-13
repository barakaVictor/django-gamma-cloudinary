import os
import re
import requests
import posixpath
import cloudinary
from datetime import datetime
from urllib.parse import unquote, urlparse
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.core.signals import setting_changed
from django.utils.encoding import filepath_to_uri
from django.utils.functional import cached_property
from django.utils.deconstruct import deconstructible
from django.core.exceptions import SuspiciousFileOperation
from django.contrib.staticfiles.utils import matches_patterns, check_settings
from gamma_cloudinary.utils import value_or_setting, get_resource_type

@deconstructible
class CloudinaryStorage(Storage):

    """
    The base cloudinary storage class

    """
    def __init__(self, location=None, base_url=None, options=None):
        self._base_location = location
        self._base_url = base_url
        setting_changed.connect(self._clear_cached_properties)

    def _clear_cached_properties(self, setting, **kwargs):
        """Reset setting based property values."""
        if setting == 'MEDIA_ROOT':
            self.__dict__.pop('base_location', None)
        elif setting == 'MEDIA_URL':
            self.__dict__.pop('base_url', None)

    @cached_property
    def base_location(self):
        """ The location where the media/static files are located """
        return value_or_setting(self._base_location, settings.MEDIA_ROOT)

    @cached_property
    def base_url(self):
        """
        The base url upon which the final full urls to the individual
        media/static files are based. Forms part of the url that remains constant
        even as the endings for these urls change across separate files.
        """
        root_folder = settings.CLOUDINARY_STORAGE.get(
            'BASE_STORAGE_LOCATION',
            os.path.basename(self.base_location)
        )
        return os.path.join(
            root_folder,
            value_or_setting(self._base_url, settings.MEDIA_URL).lstrip('/'),
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
        url = self.url(name)
        response = requests.head(url)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def get_file_metadata(self, name):
        """
        Probe Cloudinary servers for metadata about a resource and
        return this metadata e.g. file last modified time.
        """
        response = requests.head(self.url(name))
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.headers

    def size(self, name):
        """
        Return the total size, in bytes, of the file specified by name.

        Arguments:
        name -- The name of the target resource on Cloudinary

        Returns:
        integer: The size in bytes of the target resource
        """
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

        Returns:
        file: A File object or raises an exception if the file does not exist
        """
        url = self.url(name)
        response = requests.get(url)

        if response.status_code == 404:
            return None
        response.raise_for_status()

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
        #Do not attempt to upload empty files
        if content.size <= 0:
            return None

        options = {
            'use_filename': True,
            'resource_type': get_resource_type(name),
            'unique_filename': False,
            'overwrite': True,
            'invalidate': True
            }
        folder, name = os.path.split(self.upload_path(name))
        if folder:
            options['folder'] = folder
        response = cloudinary.uploader.upload(content, **options)
        if settings.MEDIA_ROOT == self.base_location and response['resource_type'] in ['image', 'video', 'audio']:
            response['public_id'] = "%s.%s"%(response['public_id'], response['format'])
        return response['public_id'].split('media/', 1)[-1]

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
    def url(self, name, **options):
        """
        Get the full cloudinary url to a resource

        Parameters:
        name(string): The name of the target file used as the public_id when querying Cloudinary

        Returns:
        string: The url to use to access the target resource on Cloudinary

        """
        url = filepath_to_uri(name).lstrip('/')
        cloudinary_resource = cloudinary.CloudinaryResource(
            self.upload_path(url),
            default_resource_type=get_resource_type(name)
        )
        if cloudinary_resource.resource_type == 'image' and 'quality' not in options:
            options = dict(
                {
                    'quality': settings.CLOUDINARY_STORAGE.get('DEFAULT_IMAGE_QUALITY', 'auto'),
                    'fetch_format': settings.CLOUDINARY_STORAGE.get('IMAGE_FETCH_FORMAT', 'auto'),
                    'width': 'auto',
                    'dpr': 'auto'
                },
                **options
                )
        if 'ckeditor' in url:
            print(url, cloudinary_resource.build_url(**options))
        return cloudinary_resource.build_url(**options)

    def upload_path(self, name):
        """
        Appends the name of the target resource to the base_url to generate the
        resource's public_id.

        Arguments:
        name(string): the name of the target resource.

        Returns:
        string: the result of concatenating the name of the resource and the base_url.
        """
        name = name.replace('\\', '/').lstrip('/')
        if name.startswith(self.base_url.lstrip('/')):
            return name
        return (os.path.join(self.base_url.lstrip('/'), name).lstrip('/')).replace('\\', '/').lstrip('/')


    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system and
        available for new content to be written to.

        Arguments:
        name(string): The prospective available name for the resource.
        max_length(int): The acceptable length of the filename. Defaults to None.

        Returns:
        string: The availabl resource name for use.
        """
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


