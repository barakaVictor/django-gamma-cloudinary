=====
Django-Gamma-Cloudinary
=====

django-gamma-cloudinary is a storage backend for integrating
your static and media asset management with the Cloudinary platform. 

Detailed documentation is in the "docs" directory.

.. image:: https://github.com/barakaVictor/django-gamma-cloudinary/workflows/Python%20package/badge.svg?branch=main

Quick start
-----------

1. Install the package.

As at now, the package is only available from github so to install make sure to have
git installed on your machine then run the command below.

	``$ pip install --upgrade git+git://github.com/barakaVictor/django-gamma-cloudinary.git``

In case you use Django ImageField, make sure you have Pillow installed:

	``$ pip install Pillow``

2. Add "gamma-cloudinary" and "cloudinary" to your INSTALLED_APPS setting like this
::
    INSTALLED_APPS = [
        ...
	'cloudinary',
        'gamma_cloudinary',
    ]

3. Next, you need to add Cloudinary credentials to settings.py
::
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': 'your_cloud_name',
        'API_KEY': 'your_api_key',
        'API_SECRET': 'your_api_secret'
    }
    
4. Set the STATIC_ROOT and MEDIA_ROOT settings to a relative path from the project root.
::
    MEDIA_ROOT = os.path.join(PROJECT_NAME, 'media')
    STATIC_ROOT = os.path.join(PROJECT_NAME, 'staticfiles')

This package uses this values of MEDIA_ROOT and STATIC_ROOT to determine where to place your static and 
media assets on Cloudinary. By default, static and media assets are placed at the top level home "folder" 
on cloudinary

5. Set the values for STATICFILES_STORAGE and DEFAULT_FILE_STORAGE settings like so
::
	STATICFILES_STORAGE = 'gamma_cloudinary.storage.StaticCloudinaryStorage.StaticCloudinaryStorage'
	DEFAULT_FILE_STORAGE = 'gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage'
    
And you are all set to begin using the storage backend!!
