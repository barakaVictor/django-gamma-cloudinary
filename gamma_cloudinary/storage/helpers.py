import os
import mimetypes

def get_cloudinary_resource_type(name):
    """
    Returns an appropriate resource_type based on the name of the target
    resource. 
    
    The provided name should have the file extension otherwise
    it will be classified as a raw resource_type by default
    """
    root, ext = os.path.splitext(name)
    if ext is not "":
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
    else:
        return 'image'