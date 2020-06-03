import os
from . import MinetestCheckError, ContentType
from .config import parse_conf

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


class PackageTreeNode:
	def __init__(self, baseDir, relative, author=None, repo=None, name=None):
		print(baseDir)
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
				raise MinetestCheckError(("game at {} does not have a mods/ folder").format(self.relative))
			self.add_children_from_mod_dir(baseDir + "/mods")
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
			with open(self.getMetaFilePath(), "r") as myfile:
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
		import re
		pattern = re.compile("^([a-z0-9_]+)\??$")
		if not "depends" in result and not "optional_depends" in result:
			try:
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

		else:
			if "depends" in result:
				result["depends"] = [x.strip() for x in result["depends"].split(",")]
			if "optional_depends" in result:
				result["optional_depends"] = [x.strip() for x in result["optional_depends"].split(",")]

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

				self.children.append(child)


	def fold(self, attr, key=None, acc=None):
		if acc is None:
			acc = set()

		if self.meta is None:
			return acc

		at = getattr(self, attr)
		value = at if key is None else at.get(key)

		if isinstance(value, list):
			acc |= set(value)
		elif value is not None:
			acc.add(value)

		for child in self.children:
			child.fold(attr, key, acc)

		return acc

	def get(self, key):
		return self.meta.get(key)

	def validate(self):
		for child in self.children:
			child.validate()
