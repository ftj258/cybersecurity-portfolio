import re
import ast
import os
import codecs

# pattern is a regular expression used to parse through scan_edited.txt
pattern = re.compile(r'\{\"block\_hashdigest\"\:\"(.*)\"\,\s\"count\"\:(.*)\,\s\"source\_list\_id\"\:(.*)\,\s\"sources\"\:(\[.*)\}')

def visualize():
	"""visualize is used to display a graphic for the user to see the concentration of matches in scan_edited.txt and to create a dump of the file offsets.
	"""

	open_file = open("scan_edited.txt", "r")
	list_matches = []

	for line in open_file:
		match = re.search(pattern, line)
		if match:
			matches = ast.literal_eval(match.group(4))
			for duplicate in matches:
				source_id = duplicate["source_id"]
				offset = duplicate["file_offset"]
				list_matches.append([source_id, offset])

	# The matches are sorted in priority of source_id and then offset.
	list_matches.sort(key=lambda i: (i[0], i[1]))
	current_source = list_matches[0][0]
	current_end = 0
	f = codecs.open("results.txt", "a+", encoding = "utf8")
	f_offsets = open("offsets.txt", "a+")
	f.write("Source: " + str(current_source) + "\n")
	f_offsets.write("Source: " + str(current_source) + "\n")

	for i in list_matches:
		if i[0] != current_source:
			current_source = i[0]
			current_end = 0
			f.write("Source: " + str(current_source) + "\n")
			f_offsets.write("END\nSource: " + str(current_source) + "\n")
		num_white_blocks = (i[1] - current_end)//512
		f.write(num_white_blocks * u'\u25a1' + u'\u25a0')
		current_end += ((num_white_blocks * 512) + 512)
		f_offsets.write(str(i[1]) + ", ")
	f_offsets.write("END")

	# Cleanup
	open_file.close()
	f.close()
	f_offsets.close()

if __name__ == "__main__":
	visualize()
