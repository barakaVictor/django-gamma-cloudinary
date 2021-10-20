import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = 'test_secret_key'

DEBUG = True

TEST_ROOT = os.path.join(BASE_DIR, 'tests')

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'cloudinary',
    'gamma_cloudinary'
]

MIDDLEWARE = [

]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = 'gamma_cloudinary.storage.CloudinaryStorage'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'gamma_cloudinary.storage.StaticCloudinaryStorage'

STATICFILES_DIRS = [
    os.path.join(TEST_ROOT, 'static')
]


CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'test',
    'API_KEY': 'api_key',
    'API_SECRET': 'api_secret',
    'BASE_STORAGE_LOCATION': '/test/',
    'SECURE': True
}


