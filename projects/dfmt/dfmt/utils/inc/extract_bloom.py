from bloom_filter import BloomFilter
import json

bloom_names = ["bloom_1", "bloom_2_9", "bloom_10_99", "bloom_100plus"]

blooms = {x: BloomFilter() for x in bloom_names}


def insert(hash_value, frequency):
    """insert adds a hash value to the corresponding bloom filter based on how many times it occurs in the media.

    Parameters:
        hash_value(str): The hash value being inserted.
        frequency(int): The number of times the hash value occurs in the media.
    """
    if frequency == 1:
        blooms["bloom_1"].add(hash_value)
    elif frequency > 1 and frequency < 10:
        blooms["bloom_2_9"].add(hash_value)
    elif frequency > 9 and frequency < 100:
        blooms["bloom_10_99"].add(hash_value)
    else:
        blooms["bloom_100plus"].add(hash_value)


def from_file(file_name="bloom_export.txt", *, contents_dict=None):
    """from_file imports a bloom filter text file in JSON format and loads the contents.

    Parameters:
        file_name(str): The name of the imported file (bloom_export.txt is the default).
    """

    if contents_dict:
        for k, v in contents_dict.items():
            for i in range(len(v)):
                blooms[k].backend.array_[i] = v[i]
    else:
        with open(file_name, "r") as f:
            contents = json.loads(f.read())
            for k, v in contents.items():
                for i in range(len(v)):
                    blooms[k].backend.array_[i] = v[i]


def check(hash_value):
    """check returns a value that contributes to the final score based on which bloom filter the hash value is in.
    These values are based on the research paper, [Insert paper name here].

    Parameters:
        hash_value(str): The hash value being checked.
    """
    if hash_value in blooms["bloom_1"]:
        return 1
    elif hash_value in blooms["bloom_2_9"]:
        return 0.31545741324
    elif hash_value in blooms["bloom_10_99"]:
        return 0.0521920668
    elif hash_value in blooms["bloom_100plus"]:
        return 0.01
    else:
        return 0.0

def extract():
    """returns the blooms name and items in a dictionary."""
    return {x:y.backend.array_.tolist() for x,y in blooms.items()}
