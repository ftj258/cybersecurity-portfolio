import werkzeug
import os
from flask_restx import Namespace, Resource, fields, abort, reqparse, inputs
from flask import Flask, request, Response, jsonify, make_response
from flask import current_app as app

from .utils.errors import make_error
from .utils.hooks import catalog_exists, images_exist, auth_required
from .resources.services.catalogs_service import create_catalog, remove_catalog, get_all_catalogs
from .resources.services.images_service import load_image, get_all_images
from .resources.services.query_service import query_file

# Catalog namespace that includes all paths for catalog endpoint /catalogs
namespace = Namespace('catalogs', description='Create catalog databases, load images into a catalog and query files from a catalog')
# These 2 parser's are only used for the documentation purposes to accept only 1 image/file (bug in Swagger 3.0)
one_image_parser = namespace.parser().add_argument("image", type=werkzeug.datastructures.FileStorage, location="files", required=True)
one_file_parser = namespace.parser()
one_file_parser.add_argument("file", type=werkzeug.datastructures.FileStorage, location="files", required=True)
one_file_parser.add_argument("compute3", type=inputs.boolean, required=False, default=True)
one_file_parser.add_argument("compute1", type=inputs.boolean, required=False, default=False)

@namespace.route('/')
class GetAllCatalogResource(Resource):
    @auth_required
    @namespace.response(200, 'Succesfully returns all catalogs')
    def get(self):
        """
        Get all catalogs.
        """
        # Get all catalogs from the database folder
        data = get_all_catalogs()
        response = {
            "status" : 200,
            "data" : {
                "catalogs" : data
            }
        }
        return make_response(jsonify(response), 200)

@namespace.route('/<catalog_name>')
class CatalogResource(Resource):
    @namespace.response(200, "Successfully created the catalog")
    @namespace.response(400, "Catalog already exists")
    @namespace.response(500, 'Failed to create the catalog')
    @auth_required
    def post(self, catalog_name):
        """
        Creates empty catalog database with no images loaded.
        """
        # Attempt to create the catalog and get response
        response = create_catalog(catalog_name)
        # Success if catalog is created
        if response == 0:
            data = {
                "status" : 200,
                "message" : f"Successfully created the catalog '{catalog_name}'",
            }
            return make_response(jsonify(data), 200)
        # Failure if catalog already exists
        elif response == 1:
            return make_error(f"The catalog '{catalog_name}' already exists", 400)
        # Failure if something went wrong when creating the catalog
        else:
            return make_error(f"Failed to create the catalog '{catalog_name}'", 500)

    @namespace.response(200, "Successfully removed the catalog")
    @namespace.response(404, "Catalog does not exist")
    @namespace.response(500, "Failed to remove the catalog")
    @auth_required
    @catalog_exists
    def delete(self, catalog_name):
        """
        Deletes catalog from database folder.
        """
        # Attempt to delete the catalog and get response
        response = remove_catalog(catalog_name)
        # Success if catalog is removed
        if response == 0:
            data = {
                "status" : 200,
                "message" : f"Successfully removed the catalog '{catalog_name}'",
            }
            return make_response(jsonify(data), 200)
        # Failure if catalog could not be removed
        else:
            return make_error(f"Failed to remove the catalog '{catalog_name}'", 500)

@namespace.route('/<catalog_name>/images/')
class CatalogImagesResource(Resource):

    def __init__(self, api=None, *args, **kwargs):
        # Initialize parser that accepts images
        self.query_file_parser = api.parser()
        self.query_file_parser.add_argument("image", type=werkzeug.datastructures.FileStorage, location="files", required=False, action='append')
        super().__init__(api=api, *args, **kwargs)

    @namespace.response(200, "Successfully returns all images of the catalog")
    @namespace.response(404, "Catalog does not exist")
    @auth_required
    @catalog_exists
    def get(self, catalog_name):
        """
        Get all images loaded into catalog.
        """
        # Get list of images loaded into catalog
        data = get_all_images(catalog_name)
        response = {
            "status" : 200,
            "data" : {
                "catalog" : catalog_name,
                "images" : data
            }
        }
        return make_response(jsonify(response), 200)

    @namespace.expect(one_image_parser)
    @namespace.response(200, "Succesfully attempted to load all images into the catalog")
    @namespace.response(400, "No images provided")
    @namespace.response(404, "Catalog does not exist")
    @auth_required
    @catalog_exists
    def post(self, catalog_name):
        """
        Load provided images into catalog.
        """
        args = self.query_file_parser.parse_args()
        # Validate that atleast 1 image was provided in request
        if args["image"] == None:
            return make_error("No images provided in request (must use 'image' as key)", 400)
        image_list = []
        # Loop through each image provided in request
        for image in args["image"]:
            # Load the image into the catalog
            status, message, filename = load_image(catalog_name, image)
            # Construct dictionary for image loading status
            image_dict = {
                "image" : filename,
                "loaded" : True if status==0 else False,
                "message" : message
            }
            # Add each image dictionary to a list
            image_list.append(image_dict)
        # Construct final response dictionary with status, and data of all images loaded into catalog
        response = {
            "status" : 200,
            "data" : {
                "catalog" : catalog_name,
                "images" : image_list
            }
        }
        return make_response(jsonify(response), 200)

@namespace.route('/<catalog_name>/query/')
class CatalogQueryResource(Resource):

    def __init__(self, api=None, *args, **kwargs):
        # Initialize parser that accepts files and compute modes
        self.query_file_parser = api.parser()
        self.query_file_parser.add_argument("file", type=werkzeug.datastructures.FileStorage, location="files", required=False, action='append')
        self.query_file_parser.add_argument("compute3", type=inputs.boolean, required=False, default=True)
        self.query_file_parser.add_argument("compute1", type=inputs.boolean, required=False, default=False)
        super().__init__(api=api, *args, **kwargs)

    @namespace.expect(one_file_parser)
    @namespace.response(200, "Successfully queried all files against the catalog")
    @namespace.response(400, "No images exist to query or no files provided or compute modes are invalid")
    @namespace.response(404, "Catalog does not exist")
    @auth_required
    @catalog_exists
    def post(self, catalog_name):
        """
        Query provided files against the catalog.
        """
        # Check if image already exists
        images_exist(catalog_name)
        # Parse provided arguments
        args = self.query_file_parser.parse_args()
        # Failure if no files provided
        if args["file"] == None:
            return make_error("No query files provided in request (must use 'file' as key)", 400)
        # Failure if both compute modes are false
        if (args["compute3"] == False) and (args["compute1"] == False):
            return make_error("Both compute modes turned off", 400)
        # Create response dictionary
        response = {
            "status" : 200,
            "catalog" : catalog_name,
            "data" : {}
        }
        # Loop through each file provided in request
        for file in args["file"]:
            # Query the file from the catalog with the given compute modes
            data, filename = query_file(catalog_name, file, args["compute3"], args["compute1"])
            # Insert data from each query result into result dictionary
            response["data"][filename] = data
        # Return success response with data
        return make_response(jsonify(response), 200)       