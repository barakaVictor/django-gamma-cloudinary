========================
Django-Gamma-Cloudinary
========================

A django storage backend for integrating your static and media asset management with the Cloudinary platform.
It applies some of the automatic image optimization capabilities provided by cloudinary. These optimization capabilities can be
customized using the CLOUDINARY_STORAGE settings variable.

.. image:: https://github.com/barakaVictor/django-gamma-cloudinary/workflows/Python%20package/badge.svg?branch=main
        :target: https://github.com/barakaVictor/django-gamma-cloudinary

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
	:target: https://opensource.org/licenses/BSD-3-Clause

.. image:: https://app.codacy.com/project/badge/Coverage/46f9e273015842829ba79cff86b9d409
	:target: https://www.codacy.com/gh/barakaVictor/django-gamma-cloudinary/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=barakaVictor/django-gamma-cloudinary&amp;utm_campaign=Badge_Coverage

.. image:: https://app.codacy.com/project/badge/Grade/46f9e273015842829ba79cff86b9d409
	:target: https://www.codacy.com/gh/barakaVictor/django-gamma-cloudinary/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=barakaVictor/django-gamma-cloudinary&amp;utm_campaign=Badge_Grade)

Quick start
----------------

Installation and setup.
~~~~~~~~~~~~~~~~~~~~~~~
Install the package using ``pip``.

.. code-block:: sh

	$ pip install django-gamma-cloudinary

In case you use Django ImageField, make sure you have Pillow installed.

.. code-block:: sh

	$ pip install Pillow

Also, this package has a python-magic dependency which is a simple wrapper around the libmagic C library.
If running on Windows platform, be sure to also also install ``python-magic-bin`` by running ``pip install python-magic-bin``
while on linux (Debian/Ubuntu), be sure to install the libmagic C library by running ``sudo apt-get install libmagic1``

Add "gamma-cloudinary" and "cloudinary" to your INSTALLED_APPS setting like this

.. code-block:: python

	INSTALLED_APPS = [
		'...',
		'cloudinary',
		'gamma_cloudinary',
	]

Next, you need to add Cloudinary credentials to settings.py

.. code-block:: python

	CLOUDINARY_STORAGE = {
		'CLOUD_NAME': 'your_cloud_name',
		'API_KEY': 'your_api_key',
		'API_SECRET': 'your_api_secret'
	}

Set the STATIC_ROOT and MEDIA_ROOT as well as STATIC_URL and MEDIA_URL.

.. code-block:: python

	MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
	STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

	STATIC_URL = '/static/'
	MEDIA_URL = '/media/'

This package uses this values of MEDIA_ROOT and STATIC_ROOT to determine where to place your static and
media assets on Cloudinary. By default, static and media assets are placed at the top level location of your media library
on cloudinary

Set the values for STATICFILES_STORAGE and DEFAULT_FILE_STORAGE settings like so

.. code-block:: python

	STATICFILES_STORAGE = 'gamma_cloudinary.storage.StaticCloudinaryStorage'
	DEFAULT_FILE_STORAGE = 'gamma_cloudinary.storage.CloudinaryStorage'


And you are all set to begin using the storage backend!!

Usage with static assets
------------------------

To use this backend to serve static assets, use the ``StaticCloudinaryStorage`` class as the
STATICFILES_STORAGE in your settings file. The setting should be specified as follows

.. code-block:: python

 	STATICFILES_STORAGE = 'gamma_cloudinary.storage.StaticCloudinaryStorage'

Afterwards, simply using the django ``static`` template tag would suffice to display your static files.
However, if you require to apply cloudinary transformations to the static files during render, this
package defines a custom template tag name ``gamma_cl_static``. To use the tag follow the steps as
outlined below.

load the template tag in the template that requires it like so

.. code-block:: htmldjango

	{% load gamma_cl_static %}

Use the template tag providing it with the transformation options you desire like so

.. code-block:: htmldjango

	{% gamma_cl_static 'images/test.png' fetch_format='auto' quality='auto' dpr='auto' width='auto' responsive=True %}

Consult the cloudinary documentation for details about which options are available while applying
transformations on stored assets

Usage with media assets
------------------------

For usage with media assets, ensure that the DEFAULT_FILE_STORAGE backend is set to ``CloudinaryStorage`` like so

.. code-block:: python

 	DEFAULT_FILE_STORAGE = 'gamma_cloudinary.storage.CloudinaryStorage'

After setting this setting, all media uploads will end up in a location characterized by a combination of the MEDIA_ROOT and the value
of ``CLOUDINARY_STORAGE['BASE_STORAGE_LOCATION']`` if this setting has been set.

After defining the DEFAULT_FILE_STORAGE, proceed to display media assets using the django default method i.e.
Assuming we have a model like this

.. code-block:: python

	 class TestModel(models.Model):
	    image = models.ImageField(upload_to='images')

Then displaying the uploaded image would be as simple as

.. code-block:: htmldjango

	<img src="{{  test.image.url  }}"/>

However, the above method is less flexible as it does not allow one to specify transformations to be applied to the asset
before rendering. To achieve this flexibility, one is required to use the ``cloudinary_url`` template tag that comes with
the cloudinary package, a dependency of django-gamma-cloudinary. This is done following the steps below.

Load the ``cloudinary`` template tags in your templates

.. code-block:: htmldjango

	{% load cloudinary %}

Use the ``cloudinary_url`` tag passing it the name(public_id) of the resource to render. This name is easily
retrievable from the name attribute of the django ``ImageField``

.. code-block:: htmldjango

	<img src="{% cloudinary_url team.image.name fetch_format='auto' quality='auto' dpr='auto' width='auto' responsive=True default_image='placeholder' %}"/>

Settings
------------------------

Below are the settings utilized by this package with default values

.. code-block:: python

	 CLOUDINARY_STORAGE = {
	    'CLOUD_NAME': None,  # required
	    'API_KEY': None,  # required
	    'API_SECRET': None,  # required
	    'BASE_STORAGE_LOCATION': '/base_storage_location/', #parent folder to keep all media and static assets under in cloudinary media library
	    'SECURE': True,
		'DEFAULT_IMAGE_QUALITY': 'auto', # the default cloudinary quality setting for delivering images. Options are:auto;best;good;eco;low.
		'IMAGE_FETCH_FORMAT': 'auto',
	 }

Additional resources
--------------------

Additional resources are available at:

-  `Cloudinary Website <http://cloudinary.com>`__
-  `Cloudinary Documentation <http://cloudinary.com/documentation>`__
-  `Cloudinary Knowledge Base <http://support.cloudinary.com/forums>`__
-  `Cloudinary documentation for Django integration
   integration <http://cloudinary.com/documentation/django_integration>`__
-  `Cloudinary documentation for Django image upload
   documentation <http://cloudinary.com/documentation/django_image_upload>`__
-  `Cloudinary documentation for Django image manipulation
   documentation <http://cloudinary.com/documentation/django_image_manipulation>`__
-  `Cloudinary documentation for image transformations
   documentation <http://cloudinary.com/documentation/image_transformations>`__

Support
-------

You can `open an issue through
GitHub <https://github.com/barakaVictor/django-gamma-cloudinary/issues>`__.
