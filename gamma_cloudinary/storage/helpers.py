import os
import re
import magic
import mimetypes
import cloudinary
import urllib
from operator import itemgetter
from django.core.management import call_command
from django.conf import settings
from django.core.files.base import File
from django.contrib.staticfiles.storage import staticfiles_storage


def get_cloudinary_resource_type(name):
    """
    Returns an appropriate resource_type based on the name of the target
    resource. 
    
    The provided name should have the file extension otherwise
    it will be classified as a raw resource_type by default
    """
    resource_type = None
    mimetype = None
    root, ext = os.path.splitext(name)
    if ext is "":
        buffer_content = find_files(name)
        if buffer_content is not None:
            mimetype = magic.from_buffer(buffer_content, mime=True)
    else:
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

def find_files(name):
    filepath = call_command('findstatic', name, '--first')
    if f"Found '{name}' here:" in filepath:
        path = ' '.join(filepath.split(f"Found '{name}' here:",1)[1].split())
        with open(path) as f:
            return f.read(300)
    else:
        return checkOnline(name)

def checkOnline(name):
    prefix = storage_folder()
    
    targets = [settings.STATIC_URL, settings.MEDIA_URL]
    resource_types = ['raw', 'video', 'image']

    for target in targets:
        if not name.replace('\\', '/').lstrip('/').startswith(os.path.join(prefix, target.lstrip('/')).lstrip('/')):
            name = os.path.join(prefix, target.lstrip('/'), name.lstrip('/')).replace('\\', '/')
        for resource_type in resource_types:
            url = cloudinary.CloudinaryResource(name.lstrip('/'), default_resource_type=resource_type).url
            request = urllib.request.Request(url)
            request.get_method = lambda: 'HEAD'
            try:
                response = urllib.request.urlopen(request)
                status_code = response.getcode()
    
            except urllib.request.HTTPError as e:
                if e.code == 404:
                    continue
                raise e

            if status_code == 200:
                request = urllib.request.Request(url)
                with urllib.request.urlopen(request) as f:
                    return f.read(300)
