import os
import tempfile
from werkzeug.utils import secure_filename

from ...utils.inc.conversions import steps
from ...utils.inc.sql_loader import load
from dfmt import PACKAGE_ROOT

def _update_images_list(catalog_path, image_filename):
    """
    Helper function used to update images list to include loaded images and check if image already exists.

    Args:
        catalog_path(str): The path to the catalog.
        image_filename(str): The filename of the image to check if already exists.
    """
    with open(catalog_path, 'a+') as file:
        file.seek(0)
        for line in file.readlines():
            line = line.rstrip('\n')
            if line == image_filename:
                return 1
        file.write(image_filename + "\n")
    return 0

def get_all_images(catalog_name):
    """
    Helper function used to get all images loaded into catalog.

    Args:
        catalog_name(str): The name of the catalog to get all images loaded from.
    """
    data = []
    catalog_path = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}', f'{catalog_name}_images.txt')
    with open(catalog_path, 'r') as file:
        file.seek(0)
        for line in file.readlines():
            line = line.rstrip('\n')
            data.append(line)
    return data



def load_image(catalog_name, image):
    """
    Helper function used to load provided image into catalog.

    Args:
        catalog_name(str): The name of the catalog to load image into.
        image(FileStorage): The image with raw data to be loaded.
    """
    status = 0
    try:
        # Failure if no image file is provided
        if image.filename == None or image.filename == "":
            status = 1
            return (status, "No image provided", None)
        # Failure if image is not in raw format
        if image.content_type != 'application/octet-stream':
            status = 1
            return (status, "Image is not in raw/binary format", secure_filename(image.filename))
        # Check if image already exists and if not, add it to the list
        catalog_path = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}', f'{catalog_name}_images.txt')
        status = _update_images_list(catalog_path, secure_filename(image.filename))
        # Failure if image is already loaded
        if status != 0:
            return (status, "Image already loaded", secure_filename(image.filename))
        # Write image to temporary file
        image_filepath = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}', f'{secure_filename(image.filename)}')
        with open(image_filepath, 'wb') as temp_file:
            temp_file.write(image.stream.read())
            # Load image into catalog
            steps(catalog_name, os.path.abspath(image_filepath))
            load(catalog_name)
            status = 0
        # Remove temporary image file
        os.remove(image_filepath)
        # Successfully loaded image
        return (status, "Successfully loaded image", secure_filename(image.filename))
    except Exception as e:
        status = 2
        # Failure if something went wrong when loading image
        return (status, "Unexpected error occurred when loading image", secure_filename(image.filename))