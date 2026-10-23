import os
import tempfile
from werkzeug.utils import secure_filename

from ...utils.inc import A2 as A2
from ...utils.inc.conversions import hash_query
from dfmt import PACKAGE_ROOT

def query_file(catalog_name, query_file, compute3, compute1):
    """
    Helper function used to query a file from catalog using given compute modes.

    Args:
        catalog_name(str): The name of the catalog to query files from.
        query_file(FileStorage): The file to be queried on the catalog.
        compute3(bool): True if compute3 should be used, False otherwise.
        compute1(bool): True if compute1 should be used, False otherwise.
    """
    data = {}
    # Get secure filename given the file
    filename = secure_filename(query_file.filename)
    temp_file_path = os.path.join(PACKAGE_ROOT, 'databases', f'{catalog_name}', f'{filename}')
    # Write file data into temporary file
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(query_file.stream.read())
    # Query the file on the catalog and then remove it
    total, file_path_xml = hash_query(catalog_name, os.path.abspath(temp_file_path))
    os.remove(temp_file_path)
    # If compute1 is provided
    if compute1:
        # Calculate compute1 score and count and add to dictionary
        compute1_score, compute1_count = A2.compute1(file_path_xml, total)
        compute1_data = {
            "score": compute1_score, 
            "unique matched hashes": compute1_count, 
            "total sectors in media": total, 
        }
        data['compute1'] = compute1_data
    # If compute3 is provided
    if compute3:
        # Calculate harmonic means compute3 score, count and compute2
        harmonic_means_dic = {}
        harmonic_means, compute3_count, c2 = A2.compute3(file_path_xml, total)
        # Parse harmonic means dictionary to create readable result dictionary
        for mean in harmonic_means.keys():
            image_name = os.path.split(harmonic_means[mean][0])[1]
            score = {"score" : harmonic_means[mean][1]}
            harmonic_means_dic[image_name] = score
        compute3_data = {
            "images": harmonic_means_dic, 
            "unique matched hashes": compute3_count, 
            "total sectors in media": total, 
            "compute2": c2,
        }
        data['compute3'] = compute3_data
    # Clean up files that have to be removed after query
    cleanup_list = ["scan.txt", "temp.xml", "comp1.db", "comp2.db", "comp3.db"]
    for file in cleanup_list:
        try:
            path = os.path.join(PACKAGE_ROOT, file)
            os.remove(path)
        except:
            continue
    # Return final data dictionary
    return data, filename