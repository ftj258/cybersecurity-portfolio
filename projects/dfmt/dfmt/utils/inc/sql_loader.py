import re
import subprocess
import ast
import sqlite3
import os

from .exceptions import HashException
from dfmt import PACKAGE_ROOT

# pattern is a regular expression used to parse through hash_freq_edited.txt
pattern = re.compile(r'\{\"block\_hashdigest\"\:\"(.*)\"\,\s\"count\"\:(.*)\,\s\"source\_list\_id\"\:(.*)\,\s\"sources\"\:(\[.*)\}')

def load(db_name):
	"""load is used to load information from hash_freq.txt into an sqlite3 database.

	Parameters:
		db_name(str): The specified name of the sqlite3 database.

	"""
	# This is the location of where the sqlite3 database will be created.
	db_add = os.path.join(PACKAGE_ROOT, 'databases', f'{db_name}', f'{db_name}.db')

	try:
		try:
			# Creates an edited text file to account for the backslash problem in Windows OS.
			with open(os.path.join(PACKAGE_ROOT, 'utils', 'inc', 'hash_freq.txt'), "r") as fin:
				with open(os.path.join(PACKAGE_ROOT, 'utils', 'inc', 'hash_freq_edited.txt'), "w") as fout:
						for line in fin:
							fout.write(line.replace('\\', '/'))
		except FileNotFoundError:
			raise HashException("hash_freq.txt not found")

		# Checks for an existing sqlite3 database and deletes it to avoid loading duplicates.
		if os.path.exists(db_add):
			os.remove(db_add)
			print("Deleted the sqlite3.")

		# Creates a new sqlite3 database with a table that has columns hash, frequency, source_id, and file_offset.
		conn = sqlite3.connect(db_add)
		c = conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS hashes (hash text, frequency integer, source_id integer, file_offset integer)")

		# Parses through hash_freq_edited.txt line by line to retrieve the hash value, frequency, source_id, and file_offset by using a regular expression.
		f = open(os.path.join(PACKAGE_ROOT, 'utils', 'inc', 'hash_freq_edited.txt'), "r")
		for line in f:
			match = re.search(pattern, line)

			if match:
				a_hash = match.group(1)
				frequency = match.group(2)
				# duplicates is a list of dictionaries that have source_id and file_offset of the corresponding hash.
				duplicates = ast.literal_eval(match.group(4))
				for entry in duplicates:
					source_id = entry["source_id"]
					file_offset = entry["file_offset"]
					c.execute(f"INSERT INTO hashes VALUES ('{a_hash}', '{frequency}', '{source_id}', '{file_offset}')")
		conn.commit()
		f.close()
	# Cleanup
	finally:
		os.remove(os.path.join(PACKAGE_ROOT, 'utils', 'inc', 'hash_freq.txt'))
		os.remove(os.path.join(PACKAGE_ROOT, 'utils', 'inc', 'hash_freq_edited.txt'))

def hash_lister(db_path):
	"""hash_lister returns the content of an sqlite3 database of the specified name as a list.

	Parameters:
		db_path(str): The specified path of the sqlite3 database.

	Returns:
		c.fetchall()(list): A list of all the content in the database.
	"""

	conn = sqlite3.connect(db_path)
	c = conn.cursor()
	c.execute('SELECT * FROM hashes')
	return(c.fetchall())
