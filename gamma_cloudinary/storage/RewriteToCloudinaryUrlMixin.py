import os
import re
import posixpath
from urllib.parse import unquote, urlparse
from django.conf import settings
from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.base import ContentFile


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
                    assert url_parts.path.startswith(settings.STATIC_URL)
                    target_name = url_parts.path[len(settings.STATIC_URL):]
                else:
                    # We're using the posixpath module to mix paths and URLs conveniently.
                    source_name = name if os.sep == '/' else name.replace(os.sep, '/')
                    #print(source_name)
                    target_name = posixpath.join(posixpath.dirname(source_name), url_parts.path)

                transformed_url = self.url(target_name, local=False)

                if url_parts.query:
                    transformed_url += f"?{url_parts.query}"

                if url_parts.fragment:
                    transformed_url += ('?#' if '?#' in url else '#') + url_parts.fragment

                # Return the cloudinary version to the file
                return template % unquote(transformed_url)

            return converter