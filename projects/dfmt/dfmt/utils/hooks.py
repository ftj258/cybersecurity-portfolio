import os
import functools
from flask_restx import abort
from flask import current_app as app
from flask import request

from .errors import make_error
from dfmt import PACKAGE_ROOT

def _catalog_exists(catalog_name):
    catalog_path = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}')
    if not os.path.exists(catalog_path):
        abort(404, message=f"Catalog '{catalog_name}' does not exist", status=404)

def catalog_exists(func):
    @functools.wraps(func)
    def wrapper_catalog_exists(*args, catalog_name):
        _catalog_exists(catalog_name)
        value = func(*args, catalog_name)
        return value
    return wrapper_catalog_exists

def images_exist(catalog_name):
    catalog_path = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}', f'{catalog_name}_images.txt')
    with open(catalog_path, 'r') as file:
        file.seek(0)
        line_count = file.readlines()
        if len(line_count) == 0:
            abort(400, message=f"Catalog '{catalog_name}' contains no loaded images", status=400)

def auth_required(func):
    @functools.wraps(func)
    def wrapper_auth_required(*args, **kwargs):
        if 'Authorization' not in request.headers:
            abort(401, message="Authorization failed", status=401)
        else:
            auth = request.headers.get('Authorization')
            key = auth.split(" ")[-1]
            if key != app.config["API_KEY"]:
                abort(401, message="Authorization failed", status=401)
        value = func(*args, **kwargs)
        return value
    return wrapper_auth_required