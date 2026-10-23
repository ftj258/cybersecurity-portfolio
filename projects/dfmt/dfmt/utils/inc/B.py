from bloom_filter import BloomFilter
import subprocess
import re
import os

from . import extract_bloom
from dfmt import PACKAGE_ROOT

# pattern is a regular expression used to parse through the media's XML file.
pattern = re.compile(r"\<hashdigest type=\'MD5\'\>(.*)\<\/hashdigest\>")

bloom_list = (
    "bloom_1",
    "bloom_2_9",
    "bloom_10_99",
    "bloom_100plus"
)

def compute(bloom_txt):
    """compute is a lightweight function that calculates a score based on whether the hash values were found in bloom filters or not.

    Parameters:
        bloom_txt(str): The path to the bloom filter TXT file.

    Returns:
        matched(int): A counter for the number of non-empty hash values that were in the bloom filter. 
        total(int): A counter for the number of non-empty hash values that were processed by the function.
        empties(int): A counter for the number of hash values in the media's XML file that were empty.
        final_score(float): The final score that is calculated by the sum of the score values divided by the total processed hash values.
    """

    image_path = os.path.join(PACKAGE_ROOT, "temp.xml")
    open_file = None

    try:
        extract_bloom.from_file(bloom_txt)

        matched = total = empties = score_sum = 0
        # empty is a list of hash values to ignore.
        empty = ["bf619eac0cdf3f68d496ea9344137e8b", "393a0fa0f348fb03871ab93726057ddc", "de03fe65a6765caa8c91343acc62cffc",
                 "0f343b0931126a20f133d67c2b018a3b", "9a8918b11878da506f761bc1c9c4ce17", "c5d77850e62433f25d5496bfad94c1b2",
                 "c99a74c555371a433d121f551d6c6398", "e0deebd3c3f560212af17c68b9344bae", "2c08651e2ae72796062369ad988f358b",
                 "620f0b67a91f7f74151bc5be745b7110", "6ae59e64850377ee5470c854761551ea"]

        open_file = open(image_path, "r")
        for line in open_file:
            match = re.search(pattern,line)

            if match:
                a_hash = match.group(1)

                if a_hash not in empty:
                    score_value = extract_bloom.check(a_hash)

                    if score_value == 0:
                        total += 1
                    elif score_value != None:
                        matched += 1
                        total += 1
                        score_sum += score_value
                else:
                    empties += 1

        #The media's XML file includes the hash value of the entire file that will be recognized by the pattern. Subtracting 1 fixes the total. 
        total -= 1
        final_score = score_sum/total

        return matched, total, empties, final_score

    finally:
        if open_file:
            open_file.close()
        os.remove(os.path.join(PACKAGE_ROOT, "temp.xml"))