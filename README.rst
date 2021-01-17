=====
Django-Gamma-Cloudinary
=====

django-gamma-cloudinary is a storage backend for integrating
your static and media asset management with the Cloudinary platform. 

.. image:: https://github.com/barakaVictor/django-gamma-cloudinary/workflows/Python%20package/badge.svg?branch=main
        :target: https://github.com/barakaVictor/django-gamma-cloudinary 
	
.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg 
	    :target: https://opensource.org/licenses/BSD-3-Clause

Quick start
----------------

1. Install the package.
   As at now, the package is only available from github so to install make sure to have
   git installed on your machine then run the command below.
   ::
   	``$ pip install --upgrade git+git://github.com/barakaVictor/django-gamma-cloudinary.git``
	
   In case you use Django ImageField, make sure you have Pillow installed.
   ::
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

Usage with static assets
------------------------

To use this backend to serve static assets, use the ``StaticCloudinaryStorage`` class as the 
STATICFILES_STORAGE in your settings file. The setting should be specified as follows
::
 STATICFILES_STORAGE = 'gamma_cloudinary.storage.StaticCloudinaryStorage.StaticCloudinaryStorage'

Afterwards, simply using the django ``static`` template tag would suffice to display your static files.
However, if you require to apply cloudinary transformations to the static files during render, this
package defines a custom template tag name ``gamma_cloudinary_static``. To use the tag follow the steps as 
outlined below.

1. load the template tag in the template that requires it like so
   ::
    {% load gamma_cloudinary_static %}

2. Use the template tag providing it with the transformation options you desire like so
   ::
    {% gamma_cloudinary_static 'images/test.png' fetch_format='auto' quality='auto' dpr='auto' width='auto' responsive=True %}
   
   Consult the cloudinary documentation for details about which options are available while applying 
   transformations on stored assets

Usage with media assets
------------------------

For usage with media assets, ensure that the DEFAULT_FILE_STORAGE backend is set to ``CloudinaryStorage`` like so
::
 DEFAULT_FILE_STORAGE = 'gamma_cloudinary.storage.CloudinaryStorage.CloudinaryStorage'

After setting this setting, all media uploads will end up in a location as defined by the MEDIA_ROOT. Consider
setting the MEDIA_ROOT to a relative path from the project root directory as this path will be replicated on 
cloudinary.

After defining the DEFAULT_FILE_STORAGE, proceed to display media assets using the django default method i.e.
Assuming we have a model like this
::
 class TestModel(models.Model):
    image = models.ImageField(upload_to='images')

Then displaying the uploaded image would be as simple as
::
 <img src="{{  test.image.url  }}"/>

However, the above method is less flexible as it does not allow to specify transformations to be applied to the asset
before rendering. To achieve this flexibility, one is required to use the ``cloudinary_url`` template tag that comes with
the cloudinary package, a dependency of django-gamma-cloudinary. This is done following the steps below.

1. Load the ``cloudinary`` template tags in your templates
   ::
    {% load cloudinary %}

2. Use the ``cloudinary_url`` tag passing it the name(public_id) of the resource to render. This name is easily
   retrievable from the name attribute of the django ``ImageField``
   ::
    <img src="{% cloudinary_url team.image.name fetch_format='auto' quality='auto' dpr='auto' width='auto' responsive=True default_image='placeholder' %}"/>

Settings
------------------------

Below are the settings utilized by this package with default values
::
 CLOUDINARY_STORAGE = {
    'CLOUD_NAME': None,  # required
    'API_KEY': None,  # required
    'API_SECRET': None,  # required
    'SECURE': True,
 }