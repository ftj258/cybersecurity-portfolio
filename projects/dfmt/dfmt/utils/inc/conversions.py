import os
import subprocess
import json
import xml
import re
import time

from dfmt import PACKAGE_ROOT

# Setting variables with file paths from config.json.
config_file = open(os.path.join(PACKAGE_ROOT, "config.json"))
config = json.loads(config_file.read())

# Note: File paths can edited through the config.json file.
hashdb = os.path.join(PACKAGE_ROOT, os.path.normpath(config["filePaths"]["hashDB"]))
md5deep64 = os.path.join(PACKAGE_ROOT, os.path.normpath(config["filePaths"]["md5deep64"]))
trunc = os.path.join(PACKAGE_ROOT, os.path.normpath(config["filePaths"]["trunc"]))
hash_list = os.path.join(PACKAGE_ROOT, os.path.normpath(config["filePaths"]["hash_list"]))
sector_hashsize = config["sectorHashSize"]

# This is a pattern used to parse through an XML file.
pattern = re.compile(r"\<hashdigest type=\'MD5\'\>(.*)\<\/hashdigest\>")

def hashdb_create(database_name):
    """Creates a hashdb database with the specified name.

    Parameters:
        database_name(str): The name of the hashdb database to be created.

    """
    lit_hash_database = os.path.join(PACKAGE_ROOT, 'databases', f'{database_name}')
    response = subprocess.call(f'{hashdb} create -p {sector_hashsize} {lit_hash_database}', shell=True) #stdout=subprocess.PIPE, 
    #stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    if response == 0:
        with open(os.path.join(lit_hash_database, f"{database_name}_images.txt"), "w+"):
            pass
    return response 


def steps(database_name, media_name):
    """steps exports an image as an XML file to load it into the hashdb database,
    and to create hash_freq.txt, which is used by sql_loader.py

    Parameters:
        database_name(str): The name of the hashdb database to load the XML file into.
        media_name(str): The file path of the image we want to convert to XML.

    """
    start = time.time()
    img_to_xml(media_name)
    xml_to_database(database_name)
    hash_freq(database_name)
    end = time.time()
    difference = end - start
    print("Time Taken: " + str(difference))


def img_to_xml(media_path, export_as="temp.xml"):
    """img_to_xml exports an image as an XML file by using md5deep64.

    Parameters:
        media_path(str): The file path of the image we want to convert to XML.
        export_as(str): The name of the XML file after it is exported (temp.xml is the default).

    Returns:
        f"{os.getcwd()}/{export_as}"(str): The file path of the XML file after it is exported.
    """
    lit_media_path = f"\"{os.path.relpath(media_path, PACKAGE_ROOT)}\""
    lit_media_path = f"{os.path.join(PACKAGE_ROOT, media_path)}"
    subprocess.call(f"{md5deep64} -x {hash_list} -d -l -p {sector_hashsize} {lit_media_path} > {os.path.join(PACKAGE_ROOT, export_as)}", shell=True)#, stdout=subprocess.PIPE, 
    #stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    return f"{os.path.join(PACKAGE_ROOT, export_as)}"

def xml_to_database(database_name):
    """xml_to_database loads the XML file into the hashdb database.

    Parameters:
        database_name(str): The name of the hashdb database to load the XML file into.

    """
    lit_hash_database = os.path.join(PACKAGE_ROOT, 'databases', f'{database_name}')
    subprocess.call(f"{hashdb} import {lit_hash_database} {os.path.join(PACKAGE_ROOT, 'temp.xml')}", shell=True)#, stdout=subprocess.PIPE, 
    #stderr=subprocess.PIPE, stdin=subprocess.PIPE)


def hash_freq(database_name):
    """hash_freq exports the contents of a hashdb database into an XML file and uses scan_expanded to find matches
    between the XML file and the hashdb database. This may seem that we are conducting a pointless step of matching
    the same thing against itself. The purpose of this step is to obtain the contents of the hashdb database in a format
    that can be easily used by regular expressions.

    Parameters:
        database_name(str): The name of the hashdb database to extract data from.
    """
    lit_hash_database = os.path.join(PACKAGE_ROOT, 'databases', f'{database_name}')
    # Export an XML file from the hashdb database in order to use the scan_expanded function.
    subprocess.call(f"{hashdb} export {lit_hash_database} {os.path.join(PACKAGE_ROOT, 'hash.xml')}", shell=True)#, stdout=subprocess.PIPE, 
    #stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    subprocess.call(f"{hashdb} scan_expanded {lit_hash_database} {os.path.join(PACKAGE_ROOT, 'hash.xml')} > {os.path.join(PACKAGE_ROOT,'utils','inc','hash_freq.txt')}", shell=True)#, stdout=subprocess.PIPE, 
    #stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    # Cleanup
    #os.remove(os.path.abspath("temp.xml"))
    path = os.path.join(PACKAGE_ROOT, "hash.xml")
    os.remove(path)


def hash_query(database_name, media_path, skip_xml=False, xml_file="temp.xml", export_as="scan.txt"):
    """hash_query is used to query for hash values that are in both the media file and the hashdb database.

    Parameters:
        database_name(str): The name of the hashdb database to load the XML file into.
        media_path(str): The file path of the media being queried.
        skip_xml(bool): Whether or not img_to_xml has to be called on the media file (False is the default).
        xml_file(str): The name of the XML file that is being used with scan_expanded (temp.xml is the default).
        export_as(str):The name of the TXT file of the scan_expanded results (scan.txt is the default).

    Returns:
        total(int): The total number of non-empty sectors in the media file.
        file_path_xml(str): The file path of the XML file after it is exported.
    """

    lit_hash_database = os.path.join(PACKAGE_ROOT, 'databases', f'{database_name}')
    lit_media_path = media_path
    # Pads the last 512-byte sector with 0s in the queried media.
    current_size = os.path.getsize(media_path)
    num_sectors_float = current_size / 512
    num_sectors = current_size // 512
    if num_sectors_float > num_sectors:
        new_size = (num_sectors * 512) + 512
        subprocess.call(f"{trunc} {lit_media_path} {new_size}", shell=True)#, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    else:
        print("File unchanged.")

    # An image will be exported as an XML file if skip_xml is False.
    if not skip_xml:
        file_path_xml = img_to_xml(media_path, export_as=xml_file)

    # empty is a list of hash values to ignore. 
    empty = ["bf619eac0cdf3f68d496ea9344137e8b", "393a0fa0f348fb03871ab93726057ddc", "de03fe65a6765caa8c91343acc62cffc",
            "0f343b0931126a20f133d67c2b018a3b", "9a8918b11878da506f761bc1c9c4ce17", "c5d77850e62433f25d5496bfad94c1b2",
            "c99a74c555371a433d121f551d6c6398", "e0deebd3c3f560212af17c68b9344bae", "2c08651e2ae72796062369ad988f358b",
            "620f0b67a91f7f74151bc5be745b7110", "6ae59e64850377ee5470c854761551ea"]

    # The number of non-empty hashes is counted.
    total = 0
    open_file = open(os.path.join(PACKAGE_ROOT, xml_file), "r")
    for line in open_file:
        match = re.search(pattern,line)

        if match:
            a_hash = match.group(1)

            if a_hash not in empty:
                total += 1

    #The media's XML file includes the hash value of the entire file that will be recognized by the pattern. Subtracting 1 fixes the total.
    total -= 1
    open_file.close()

    
    subprocess.call(f"{hashdb} scan_expanded {lit_hash_database} {os.path.join(PACKAGE_ROOT, xml_file)} > {os.path.join(PACKAGE_ROOT, export_as)}", shell=True)#, stdout=subprocess.PIPE, 
    #stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    # Creates an edited text file to account for the backslash problem in Windows OS.
    with open(os.path.join(PACKAGE_ROOT, "scan.txt"), "rt") as fin:
        with open(os.path.join(PACKAGE_ROOT, "scan_edited.txt"), "wt") as fout:
            for line in fin:
                fout.write(line.replace("\\", "/"))

    return total, file_path_xml
