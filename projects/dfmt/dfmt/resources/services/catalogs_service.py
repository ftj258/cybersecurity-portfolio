import os
import shutil

from ...utils.inc.conversions import hashdb_create
from dfmt import PACKAGE_ROOT


def create_catalog(catalog_name):
    """
    Creates a catalog 'hashdb' with the specified name.

    Args:
        catalog_name(str): The name of the catalog to be created.
    """
    # Creates the catalog with the specified name and get response code
    response = hashdb_create(catalog_name)
    # Return 0 if success, 1 if any other response
    if response != 0:
        return 1
    return 0
    
def remove_catalog(catalog_name):
    """
    Removes the hashdb specified by the catalog name.

    Args:
        catalog_name(str): The name of the catalog to delete.
    """
    response = 0
    # Path to the catalog folder containing the catalogs
    catalog_path = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}')
    # If there is a path to the specified catalog, then remove it
    try:
        shutil.rmtree(catalog_path, ignore_errors=False)
    except Exception as e:
        response = 1
    return response

def get_all_catalogs():
    """
    Get all catalogs in the database folder.
    """
    catalogs = []
    # Path to all catalogs
    catalog_path = os.path.join(PACKAGE_ROOT, 'databases')
    # Loop through folder and check if file is a directory
    for file in os.listdir(catalog_path):
        if file != "README.md":
            # Add catalog name to list
            catalogs.append(file)
    return catalogs

