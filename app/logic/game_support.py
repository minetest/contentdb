# ContentDB
# Copyright (C) 2022 rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys

from typing import List, Dict, Optional, Iterator, Iterable, Tuple

from app.logic.LogicError import LogicError
from app.models import Package, MetaPackage, PackageType, PackageState, PackageGameSupport, db

"""
get_game_support(package):
	if package is a game:
		return [ package ]

	for all hard dependencies:
		support = support AND get_meta_package_support(dep)

	return support

get_meta_package_support(meta):
	for package implementing meta package:
		support = support OR get_game_support(package)

	return support
"""


minetest_game_mods = {
	"beds", "boats", "bucket", "carts", "default", "dungeon_loot", "env_sounds", "fire", "flowers",
	"give_initial_stuff", "map", "player_api", "sethome", "spawn", "tnt", "walls", "wool",
	"binoculars", "bones", "butterflies", "creative", "doors", "dye", "farming", "fireflies", "game_commands",
	"keys", "mtg_craftguide", "screwdriver", "sfinv", "stairs", "vessels", "weather", "xpanes",
}


mtg_mod_blacklist = {
	"repixture", "tutorial", "runorfall", "realtest_mt5", "mevo", "xaenvironment",
	"survivethedays"
}


class PackageSet:
	packages: Dict[str, Package]

	def __init__(self, packages: Optional[Iterable[Package]] = None):
		self.packages = {}
		if packages:
			self.update(packages)

	def update(self, packages: Iterable[Package]):
		for package in packages:
			key = package.getId()
			if key not in self.packages:
				self.packages[key] = package

	def intersection_update(self, other):
		keys = set(self.packages.keys())
		keys.difference_update(set(other.packages.keys()))
		for key in keys:
			del self.packages[key]

	def __len__(self):
		return len(self.packages)

	def __iter__(self):
		return self.packages.values().__iter__()


class GameSupportResolver:
	checked_packages = set()
	checked_metapackages = set()
	resolved_packages: Dict[str, PackageSet] = {}
	resolved_metapackages: Dict[str, PackageSet] = {}

	def resolve_for_meta_package(self, meta: MetaPackage, history: List[str]) -> PackageSet:
		print(f"Resolving for {meta.name}", file=sys.stderr)

		key = meta.name
		if key in self.resolved_metapackages:
			return self.resolved_metapackages.get(key)

		if key in self.checked_metapackages:
			print(f"Error, cycle found: {','.join(history)}", file=sys.stderr)
			return PackageSet()

		self.checked_metapackages.add(key)

		retval = PackageSet()

		for package in meta.packages:
			if package.state != PackageState.APPROVED:
				continue

			if meta.name in minetest_game_mods and package.name in mtg_mod_blacklist:
				continue

			ret = self.resolve(package, history)
			if len(ret) == 0:
				retval = PackageSet()
				break

			retval.update(ret)

		self.resolved_metapackages[key] = retval
		return retval

	def resolve(self, package: Package, history: List[str]) -> PackageSet:
		db.session.merge(package)

		key = package.getId()
		print(f"Resolving for {key}", file=sys.stderr)

		history = history.copy()
		history.append(key)

		if package.type == PackageType.GAME:
			return PackageSet([package])

		if key in self.resolved_packages:
			return self.resolved_packages.get(key)

		if key in self.checked_packages:
			print(f"Error, cycle found: {','.join(history)}", file=sys.stderr)
			return PackageSet()

		self.checked_packages.add(key)

		if package.type != PackageType.MOD:
			raise LogicError(500, "Got non-mod")

		retval = PackageSet()

		for dep in package.dependencies.filter_by(optional=False).all():
			ret = self.resolve_for_meta_package(dep.meta_package, history)
			if len(ret) == 0:
				continue
			elif len(retval) == 0:
				retval.update(ret)
			else:
				retval.intersection_update(ret)
				if len(retval) == 0:
					raise LogicError(500, f"Detected game support contradiction, {key} may not be compatible with any games")

		self.resolved_packages[key] = retval
		return retval

	def update_all(self) -> None:
		for package in Package.query.filter(Package.type == PackageType.MOD, Package.state != PackageState.DELETED).all():
			retval = self.resolve(package, [])
			for game in retval:
				support = PackageGameSupport(package, game, 1, True)
				db.session.add(support)

	"""
	Update game supported package on a package, given the confidence.
	
	Higher confidences outweigh lower ones.
	"""
	def set_supported(self, package: Package, game_is_supported: List[Tuple[Package, bool]], confidence: int):
		previous_supported: Dict[int, PackageGameSupport] = {}
		for support in package.supported_games.all():
			db.session.merge(support.game)
			previous_supported[support.game.id] = support

		seen_game = {}
		for game, supports in game_is_supported:
			if seen_game.get(game.id):
				continue

			seen_game[game.id] = True
			lookup = previous_supported.pop(game.id, None)
			if lookup is None:
				support = PackageGameSupport(package, game, confidence, supports)
				db.session.add(support)
			elif lookup.confidence <= confidence:
				lookup.supports = supports
				lookup.confidence = confidence
				db.session.merge(lookup)

		for game, support in previous_supported.items():
			if support.confidence == confidence:
				db.session.delete(support)

	def update(self, package: Package) -> None:
		retval = self.resolve(package, [])

		game_is_supported = []
		for game in retval:
			game_is_supported.append((game, True))

		self.set_supported(package, game_is_supported, 1)
