import os
import cloudinary
from operator import itemgetter
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

#Execute setup code for cloudinary configuration
def setup_cloudinary():
    if settings.configured:
        try:
            #check for the existence of CLOUDINARY_STORAGE object in django settings module
            cloudinary_settings = getattr(settings, 'CLOUDINARY_STORAGE')

            #if CLOUDINARY_STORAGE exists check for the minimum required keys to get cloudinary up and running
            itemgetter('CLOUD_NAME', 'API_KEY', 'API_SECRET')(cloudinary_settings)
        except AttributeError:

            #if CLOUDINARY_STORAGE is not set check for the existence of
            #either CLOUDINARY_URL or (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
            #environment variables and exit silently if they have been set
            if os.environ.get('CLOUDINARY_URL'):
                pass
            if (os.environ.get('CLOUDINARY_CLOUD_NAME') and os.environ.get('CLOUDINARY_API_KEY') and os.environ.get('CLOUDINARY_API_SECRET')):
                pass
            else:
                #else raise an ImproperlyConfigured exceoption if CLOUDINARY_STORAGE does not exist in
                #the django settings module and CLOUDINARY_URL or (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET)
                #environment variables have not been set
                raise ImproperlyConfigured('In order to use cloudinary storage, you need to provide '
                                            'CLOUDINARY_STORAGE dictionary with CLOUD_NAME, API_SECRET '
                                            'and API_KEY in the django settings module or set CLOUDINARY_URL'
                                            '(or CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET) '
                                            'environment variables).')
        except KeyError as e:
            #raise ImproperlyConfigured exception if CLOUDINARY_STORAGE has been set in the django settings
            #module but without all of the minimum required  attributes(CLOUD_NAME, API_KEY, API_SECRET)
            #to get cloudinary working

            raise ImproperlyConfigured(f'{e.args[0]} is a required setting in the cloudinary config.')

        else:
            #While passing config parameters to cloudinary.config(), run dictionary
            #comprehension to convert all keys to snake_case fromat as is required in
            #cloudinary data type guidelines
            cloudinary.config(**{key.lower(): value for key, value in cloudinary_settings.items()})
