# Adapted from: https://github.com/minetest/minetest/blob/master/util/mod_translation_updater.py
#
# Copyright (C) 2019 Joachim Stolberg, 2020 FaceDeer, 2020 Louis Royer, 2023 Wuzzy, 2024 rubenwardy
# License: LGPLv2.1 or later

import os
import re


class Translation:
	language: str
	textdomain: str
	entries: dict[str]

	def __init__(self, language: str, textdomain: str, entries: dict):
		self.language = language
		self.textdomain = textdomain
		self.entries = entries


# Handles a translation line in *.tr file.
# Group 1 is the source string left of the equals sign.
# Group 2 is the translated string, right of the equals sign.
pattern_tr = re.compile(
	r'(.*)'  # Source string
	# the separating equals sign, if NOT preceded by @, unless
	# that @ is preceded by another @
	r'(?:(?<!(?<!@)@)=)'
	r'(.*)'  # Translation string
)

# Strings longer than this will have extra space added between
# them in the translation files to make it easier to distinguish their
# beginnings and endings at a glance
doublespace_threshold = 80

# These symbols mark comment lines showing the source file name.
# A comment may look like "##[ init.lua ]##".
symbol_source_prefix = "##["
symbol_source_suffix = "]##"
comment_unused = "##### not used anymore #####"


def parse_tr(filepath: str) -> Translation:
	dOut = {}
	in_header = True
	header_comments = None
	textdomain = None

	filename = os.path.basename(filepath)
	filename_parts = filename.split(".")

	assert len(filename_parts) >= 3
	assert filename_parts[-1] == "tr"
	language = filename_parts[-2]

	with open(filepath, "r", encoding='utf-8') as existing_file:
		# save the full text to allow for comparison
		# of the old version with the new output
		existing_file.seek(0)
		# a running record of the current comment block
		# we're inside, to allow preceeding multi-line comments
		# to be retained for a translation line
		latest_comment_block = None
		for line in existing_file.readlines():
			line = line.rstrip('\n')
			# "##### not used anymore #####" comment
			if line == comment_unused:
				# Always delete the 'not used anymore' comment.
				# It will be re-added to the file if neccessary.
				latest_comment_block = None
				if header_comments is not None:
					in_header = False
				continue
			# Comment lines
			elif line.startswith("#"):
				# Source file comments: ##[ file.lua ]##
				if line.startswith(symbol_source_prefix) and line.endswith(symbol_source_suffix):
					continue

				# Store first occurance of textdomain
				# discard all subsequent textdomain lines
				if line.startswith("# textdomain:"):
					if textdomain is None:
						textdomain = line[13:].strip()
					continue
				elif in_header:
					# Save header comments (normal comments at top of file)
					if not header_comments:
						header_comments = line
					else:
						header_comments = header_comments + "\n" + line
				else:
					# Save normal comments
					if line.startswith("# textdomain:") and textdomain is None:
						textdomain = line
					elif not latest_comment_block:
						latest_comment_block = line
					else:
						latest_comment_block = latest_comment_block + "\n" + line

				continue

			match = pattern_tr.match(line)
			if match:
				latest_comment_block = None
				in_header = False
				dOut[match.group(1).strip()] = match.group(2).strip()

	return Translation(language, textdomain, dOut)
