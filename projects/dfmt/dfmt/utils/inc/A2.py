import re
import ast
import sqlite3
import os

from .exceptions import HashException
from dfmt import PACKAGE_ROOT

# These are patterns used to parse through the TXT files.
pattern = re.compile(r'\{\"block\_hashdigest\"\:\"(.*)\"\,\s\"count\"\:(.*)\,\s\"source\_list\_id\"\:(.*)\,\s\"sources\"\:(\[.*)\}')
len_offset_pattern = re.compile('\<byte\_run\sfile\_offset\=\'(.*)\'\slen\=\'(.*)\>')
hash_pattern = re.compile('\<hashdigest\stype\=\'MD5\'\>(.*)\<\/hashdigest\>')


def compute1(image, total):
	"""compute1 returns the frequency of weighted matches. A media file is matched to a hashdb database containing prior evidence.
	The frequency is the number of times the hash occurs in the hashdb overall. The more frequent matches are weighted less towards the score.

	Parameters:
		image(str): The file path to the media's XML file. 
		total(int): The total number of non-empty sectors in the media file.

	Returns:
		score(float): The score that is calculated by the total sum of the values divided by count. 
		count(int): The total number of unique hashes in the matches.

	"""

	try:
		# Inserting the contents of the XML file into an sqlite3 database, so that the number of duplicates of each unique hash value can be counted.
		bool_found_offset = False
		conn = sqlite3.connect(os.path.join(PACKAGE_ROOT, "comp1.db"))
		c = conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS offsets (hash text, file_offset integer)")

		openFile = open(image)
		for line in openFile:
			match = re.search(len_offset_pattern, line)
			match2 = re.search(hash_pattern, line)

			if match:
				bool_found_offset = True
				offset_found = int(match.group(1))

			if match2 and bool_found_offset:
				bool_found_offset = False
				hash_found = match2.group(1)
				c.execute(f"INSERT INTO offsets VALUES ('{hash_found}', '{offset_found}')")

		conn.commit()

		file = open(os.path.join(PACKAGE_ROOT, "scan_edited.txt"), "r")
		count = total_sum = 0

		for line in file:
			match3 = re.search(pattern, line)

			if match3:
				count += 1
				aHash = match3.group(1)
				c.execute(f'SELECT file_offset FROM offsets WHERE hash = "{aHash}"')
				listOffsets = c.fetchall()
				frequency = match3.group(2)
				value = len(listOffsets) / int(frequency)
				total_sum += value
		# To prevent a divide-by-zero error
		if total == 0:
			score = 0
		else:
			score = total_sum/total
		return score, count

	finally:
		openFile.close()
		file.close()


def compute2(image, total):
	"""compute2 returns frequency per source weighted matches. In this case, the frequency is the number of different sources containing the hash. A hash would be
	weighted less if it occurs in more sources.

	Parameters:
		image(str): The file path to the media's XML file. 
		total(int): The total number of non-empty sectors in the media file.

	Returns:
		(score, count)(tuple): score is calculated by the total sum of the values divided by count. count is the total number of unique hashes in the matches.

	"""

	try:
		# Inserting the contents of the XML file into an sqlite3 database, so that the number of duplicates of each unique hash value can be counted.
		bool_found_offset = False
		conn = sqlite3.connect(os.path.join(PACKAGE_ROOT, "comp2.db"))
		c = conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS offsets (hash text, file_offset integer)")

		openFile = open(image)
		for line in openFile:
			match = re.search(len_offset_pattern, line)
			match2 = re.search(hash_pattern, line)

			if match:
				bool_found_offset = True
				offset_found = int(match.group(1))

			if match2 and bool_found_offset:
				bool_found_offset = False
				hash_found = match2.group(1)
				c.execute(f"INSERT INTO offsets VALUES ('{hash_found}', '{offset_found}')")

		conn.commit()

		file = open(os.path.join(PACKAGE_ROOT, "scan_edited.txt"), "r")
		count = total_sum = 0

		for line in file:
			match3 = re.search(pattern, line)

			if match3:
				count += 1
				aHash = match3.group(1)
				c.execute(f'SELECT file_offset FROM offsets WHERE hash = "{aHash}"')
				listOffsets = c.fetchall()
				duplicates = ast.literal_eval(match3.group(4))
				unique = set(())
				for entry in duplicates:
					source_id = entry["source_id"]
					unique.add(source_id)
				value = len(listOffsets) / len(unique)
				total_sum += value

		# To prevent a divide-by-zero error
		if total == 0:
			score = 0
		else:
			score = total_sum/total
		return (score, count)

	finally:
		openFile.close()
		file.close()


def compute3(image, total):
	"""compute3 also calculates frequency per source weighted matches, but is more precise by using sequencing factor.
	The matched hashes of a media file are checked if they are sequenced by the same relative offsets as the original source.

	Parameters:
		image(str): The file path to the media's XML file. 
		total(int): The total number of non-empty sectors in the media file; used by compute2.

	Returns:
		combined(dictionary): Harmonic means for each of the source IDs. Also, includes the associated file name for each source ID.
		count(int): The total number of unique hashes in the matches.
		s1(float): The score calculated by Compute 2.

	"""
	s1 = compute2(image, total)[0]
	if s1 == 0:
		print("There were no matches.")
		return "none", 0, s1

	bool_found_offset = False
	conn = sqlite3.connect(os.path.join(PACKAGE_ROOT, "comp3.db"))
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS offsets (hash text, file_offset integer)")

	# Parsing through the XML file for the hashes and offsets.
	openFile = open(image)
	for line in openFile:
		match = re.search(len_offset_pattern, line)
		match2 = re.search(hash_pattern, line)

		if match:
			bool_found_offset = True
			offset_found = int(match.group(1))

		if match2 and bool_found_offset:
			bool_found_offset = False
			hash_found = match2.group(1)
			c.execute(f"INSERT INTO offsets VALUES ('{hash_found}', '{offset_found}')")

	conn.commit()


	try:
		open_file = open(os.path.join(PACKAGE_ROOT, "scan_edited.txt"))
		count = 0
		list_matches = []
		dict_filename = {}

		for line in open_file:
			match3 = re.search(pattern, line)

			if match3:
				count += 1
				a_hash = match3.group(1)
				matches = ast.literal_eval(match3.group(4))

				for duplicate in matches:
					source_id = duplicate["source_id"]
					offset = duplicate["file_offset"]
					list_matches.append([a_hash, (source_id, offset)])

					# Associate the source_id with the matched media's filename.
					try:
						filename = duplicate["filename"]

					except KeyError:
						pass

					else:
						dict_filename[source_id] = filename

		# The entries are sorted in priority of source_id and then offset.
		list_matches.sort(key=lambda i: (i[1][0], i[1][1]))
		current_source_num = list_matches[0][1][0]
		base_point_matched = base_point_original = current_original_offset = 0
		dict_sources = {}
		dict_sources[current_source_num] = 0
		base_point_bool = True
		start_streak = True
		c = conn.cursor()

		for entry in list_matches:

			if entry[1][0] != current_source_num:
				current_source_num = entry[1][0]
				dict_sources[current_source_num] = 0
				base_point_original = current_original_offset = 0
				base_point_bool = True

			c.execute(f'SELECT file_offset FROM offsets WHERE hash = "{entry[0]}"')

			if base_point_bool == True:
				start_streak = True
				base_point_matched = entry[1][1]

				for line in c.fetchall():
					# Ignores the offsets that are before the current original offset, a new basepoint for the original media is set.
					if line[0] > current_original_offset or current_original_offset == 0:
						base_point_original = current_original_offset = line[0]
						break

				base_point_bool = False

			# Begin moving and calculating the difference between the offsets from the two basepoints to see how long the relative offset sequencing will streak for.
			else:
				difference_matched = entry[1][1] - base_point_matched

				for line in c.fetchall():
					# Ignores the offsets that are before the current original offset, and go to the next offset in the original media.
					if line[0] > current_original_offset:
						current_original_offset = line[0]

						break

				original_difference = current_original_offset - base_point_original

				if difference_matched == original_difference:
					num = dict_sources[current_source_num]
					# The number of streaked offset for that source is increased by 2 if it's the start of a streak because isolated offsets that are disregarded.
					if start_streak:
						num += 2
						start_streak = False
					else:
						num += 1
					dict_sources[current_source_num] = num

				else:
					# The process of setting a new basepoint for the original media is started again when the streak ends.
					base_point_bool = True

		harmonic_means = {}
		combined = {}

		for source in dict_sources:
			s2 = dict_sources[source] / total
			harmonic = (2 * s1 * s2) / (s1 + s2)
			harmonic_means[source] = harmonic

		# Combine the harmonic means with their associated filenames.
		for source in dict_filename:
			combined[source] = (dict_filename[source], harmonic_means[source])

		return combined, count, s1

	finally:
		open_file.close()
		conn.close()
