from enum import Enum

class MinetestCheckError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr("Error validating package: " + self.value)

class ContentType(Enum):
	UNKNOWN = "unknown"
	MOD = "mod"
	MODPACK = "modpack"
	GAME = "game"
	TXP = "texture pack"

	def isModLike(self):
		return self == ContentType.MOD or self == ContentType.MODPACK

	def validate_same(self, other):
		"""
		Whether or not `other` is an acceptable type for this
		"""
		assert(other)

		if self == ContentType.MOD:
			if not other.isModLike():
				raise MinetestCheckError("expected a mod or modpack, found " + other.value)

		elif self == ContentType.TXP:
			if other != ContentType.UNKNOWN and other != ContentType.TXP:
				raise MinetestCheckError("expected a " + self.value + ", found a " + other.value)

		elif other != self:
			raise MinetestCheckError("expected a " + self.value + ", found a " + other.value)


from .tree import PackageTreeNode, get_base_dir

def build_tree(path, expected_type=None, author=None, repo=None, name=None):
	path = get_base_dir(path)

	root = PackageTreeNode(path, "/", author=author, repo=repo, name=name)
	assert(root)

	if expected_type:
		expected_type.validate_same(root.type)

	return root
