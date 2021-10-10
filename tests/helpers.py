import os
from unittest import mock
from django.apps import apps
from django.contrib.staticfiles.finders import get_finders

def mock_http_response(status=200, content=None, json_data=None, raise_for_status=None):
    """
    Helper function that builds http reponse mock

    since we typically test a bunch of different
    requests calls for a service, we are going to do
    a lot of mock responses, so its usually a good idea
    to have a helper function that builds these things
    """
    mock_resp = mock.Mock()
    # mock raise_for_status call w/optional error
    mock_resp.raise_for_status = mock.Mock()
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    # set status code and content
    mock_resp.status_code = status
    mock_resp.content = content
    # add json data if provided
    if json_data:
        mock_resp.json = mock.Mock(
            return_value=json_data
        )
    return mock_resp

def find_files():
    ignore_patterns = list({os.path.normpath(p) for p in apps.get_app_config('staticfiles').ignore_patterns})
    found_files = {}
    for finder in get_finders():
        for path, storage in finder.list(ignore_patterns):
            # Prefix the relative path if the source storage contains it
            if getattr(storage, 'prefix', None):
                prefixed_path = os.path.join(storage.prefix, path)
            else:
                prefixed_path = path

            if prefixed_path not in found_files:
                found_files[prefixed_path] = (storage, path)
    return found_files
