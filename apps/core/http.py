import os
import re

from django.http import FileResponse, Http404

from apps.core.uploads import content_type_for

TOKEN_RE = re.compile(r"^[a-f0-9]{32}$")


def guarded_file_response(field_file, *, download_name=None, cache_control="private, no-store"):
    if not field_file or not getattr(field_file, "name", ""):
        raise Http404
    name = field_file.name
    if ".." in name or name.startswith(("/", "\\")):
        raise Http404
    handle = field_file.open("rb")
    response = FileResponse(handle, content_type=content_type_for(name))
    response["Cache-Control"] = cache_control
    response["X-Content-Type-Options"] = "nosniff"
    if download_name:
        safe = os.path.basename(download_name).replace('"', "")
        response["Content-Disposition"] = f'attachment; filename="{safe}"'
    return response
