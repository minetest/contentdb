import os, re
from . import MinetestCheckError, ContentType
from .config import parse_conf

basenamePattern = re.compile("^([a-z0-9_]+)$")

def get_base_dir(path):
	if not os.path.isdir(path):
		raise IOError("Expected dir")

	root, subdirs, files = next(os.walk(path))
	if len(subdirs) == 1 and len(files) == 0:
		return get_base_dir(path + "/" + subdirs[0])
	else:
		return path


def detect_type(path):
	if os.path.isfile(path + "/game.conf"):
		return ContentType.GAME
	elif os.path.isfile(path + "/init.lua"):
		return ContentType.MOD
	elif os.path.isfile(path + "/modpack.txt") or \
			os.path.isfile(path + "/modpack.conf"):
		return ContentType.MODPACK
	elif os.path.isdir(path + "/mods"):
		return ContentType.GAME
	elif os.path.isfile(path + "/texture_pack.conf"):
		return ContentType.TXP
	else:
		return ContentType.UNKNOWN


def get_csv_line(line):
	return [x.strip() for x in line.split(",") if x.strip() != ""]


class PackageTreeNode:
	def __init__(self, baseDir, relative, author=None, repo=None, name=None):
		self.baseDir  = baseDir
		self.relative = relative
		self.author   = author
		self.name	 = name
		self.repo	 = repo
		self.meta	 = None
		self.children = []

		# Detect type
		self.type = detect_type(baseDir)
		self.read_meta()

		if self.type == ContentType.GAME:
			if not os.path.isdir(baseDir + "/mods"):
				raise MinetestCheckError(("Game at {} does not have a mods/ folder").format(self.relative))
			self.add_children_from_mod_dir(baseDir + "/mods")
		elif self.type == ContentType.MOD:
			if self.name and not basenamePattern.match(self.name):
				raise MinetestCheckError(("Invalid base name for mod {} at {}, names must only contain a-z0-9_.") \
					.format(self.name, self.relative))
		elif self.type == ContentType.MODPACK:
			self.add_children_from_mod_dir(baseDir)


	def getMetaFilePath(self):
		filename = None
		if self.type == ContentType.GAME:
			filename = "game.conf"
		elif self.type == ContentType.MOD:
			filename = "mod.conf"
		elif self.type == ContentType.MODPACK:
			filename = "modpack.conf"
		elif self.type == ContentType.TXP:
			filename = "texture_pack.conf"
		else:
			return None

		return self.baseDir + "/" + filename


	def read_meta(self):
		result = {}

		# .conf file
		try:
			with open(self.getMetaFilePath() or "", "r") as myfile:
				conf = parse_conf(myfile.read())
				for key, value in conf.items():
					result[key] = value
		except IOError:
			pass

		# description.txt
		if not "description" in result:
			try:
				with open(self.baseDir + "/description.txt", "r") as myfile:
					result["description"] = myfile.read()
			except IOError:
				pass

		# depends.txt
		if "depends" in result or "optional_depends" in result:
			if "depends" in result:
				result["depends"] = get_csv_line(result["depends"])

			if "optional_depends" in result:
				result["optional_depends"] = get_csv_line(result["optional_depends"])

		else:
			try:
				pattern = re.compile("^([a-z0-9_]+)\??$")

				with open(self.baseDir + "/depends.txt", "r") as myfile:
					contents = myfile.read()
					soft = []
					hard = []
					for line in contents.split("\n"):
						line = line.strip()
						if pattern.match(line):
							if line[len(line) - 1] == "?":
								soft.append( line[:-1])
							else:
								hard.append(line)

					result["depends"] = hard
					result["optional_depends"] = soft

			except IOError:
				pass


		# Fix games using "name" as "title"
		if self.type == ContentType.GAME:
			result["title"] = result["name"]
			del result["name"]

		# Calculate Title
		if "name" in result and not "title" in result:
			result["title"] = result["name"].replace("_", " ").title()

		# Calculate short description
		if "description" in result:
			desc = result["description"]
			idx = desc.find(".") + 1
			cutIdx = min(len(desc), 200 if idx < 5 else idx)
			result["short_description"] = desc[:cutIdx]

		if "name" in result:
			self.name = result["name"]
			del result["name"]

		self.meta = result

	def add_children_from_mod_dir(self, dir):
		for entry in next(os.walk(dir))[1]:
			path = os.path.join(dir, entry)
			if not entry.startswith('.') and os.path.isdir(path):
				child = PackageTreeNode(path, self.relative + entry + "/", name=entry)
				if not child.type.isModLike():
					raise MinetestCheckError(("Expecting mod or modpack, found {} at {} inside {}") \
							.format(child.type.value, child.relative, self.type.value))

				if child.name is None:
					raise MinetestCheckError(("Missing base name for mod at {}").format(self.relative))

				self.children.append(child)

	def getModNames(self):
		return self.fold("name", type=ContentType.MOD)

	# attr: Attribute name
	# key: Key in attribute
	# retval: Accumulator
	# type: Filter to type
	def fold(self, attr, key=None, retval=None, type=None):
		if retval is None:
			retval = set()

		# Iterate through children
		for child in self.children:
			child.fold(attr, key, retval, type)

		# Filter on type
		if type and type != self.type:
			return retval

		# Get attribute
		at = getattr(self, attr)
		if not at:
			return retval

		# Get value
		value = at if key is None else at.get(key)
		if isinstance(value, list):
			retval |= set(value)
		elif value:
			retval.add(value)

		return retval

	def get(self, key):
		return self.meta.get(key)

	def validate(self):
		for child in self.children:
			child.validate()
