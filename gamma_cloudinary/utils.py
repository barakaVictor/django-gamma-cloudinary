import os
import magic
import mimetypes
from django.core.management import call_command

def value_or_setting(value, setting):
    return setting if value is None else value

def get_mime_type(name):
        mimetype = None
        root, ext = os.path.splitext(name)
        if ext == "":
            filepath = find_file(name)
            if bool(filepath):
                mimetype = magic.from_buffer(open(filepath, "rb").read(2048), mime=True)
        else:
            mimetype = mimetypes.guess_type(name)[0]
        return mimetype

def find_file(name):
    filepath = call_command('findstatic', name, first=True, verbosity=0)
    if name in filepath and os.path.isfile(filepath):
        return filepath
    return None

def get_resource_type(name):
        """
        Returns an appropriate resource_type based on the name of the target
        resource.

        The provided name should have the file extension otherwise
        it will be classified as a raw resource_type by default
        """
        mimetype = get_mime_type(name)
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