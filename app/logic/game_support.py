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
from typing import List, Dict, Optional, Iterable

import sqlalchemy.orm

from app.logic.LogicError import LogicError
from app.models import Package, MetaPackage, PackageType, PackageState, PackageGameSupport

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


class GameSupportResolver:
	session: sqlalchemy.orm.Session
	checked_packages = set()
	checked_metapackages = set()
	resolved_packages: Dict[int, set[int]] = {}
	resolved_metapackages: Dict[int, set[int]] = {}

	def __init__(self, session):
		self.session = session

	def resolve_for_meta_package(self, meta: MetaPackage, history: List[str]) -> set[int]:
		print(f"Resolving for {meta.name}", file=sys.stderr)

		key = meta.name
		if key in self.resolved_metapackages:
			return self.resolved_metapackages.get(key)

		if key in self.checked_metapackages:
			print(f"Error, cycle found: {','.join(history)}", file=sys.stderr)
			return set()

		self.checked_metapackages.add(key)

		retval = set()

		for package in meta.packages:
			if package.state != PackageState.APPROVED:
				continue

			if meta.name in minetest_game_mods and package.name in mtg_mod_blacklist:
				continue

			ret = self.resolve(package, history)
			if len(ret) == 0:
				retval = set()
				break

			retval.update(ret)

		self.resolved_metapackages[key] = retval
		return retval

	def resolve(self, package: Package, history: List[str]) -> set[int]:
		key = package.id
		print(f"Resolving for {key}", file=sys.stderr)

		history = history.copy()
		history.append(key)

		if package.type == PackageType.GAME:
			return {package.id}

		if key in self.resolved_packages:
			return self.resolved_packages.get(key)

		if key in self.checked_packages:
			print(f"Error, cycle found: {','.join(history)}", file=sys.stderr)
			return set()

		self.checked_packages.add(key)

		if package.type != PackageType.MOD:
			raise LogicError(500, "Got non-mod")

		retval = set()

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
		for package in self.session.query(Package).filter(Package.type == PackageType.MOD, Package.state != PackageState.DELETED).all():
			retval = self.resolve(package, [])
			for game_id in retval:
				game = self.session.query(Package).get(game_id)
				support = PackageGameSupport(package, game, 1, True)
				self.session.add(support)

	"""
	Update game supported package on a package, given the confidence.
	
	Higher confidences outweigh lower ones.
	"""
	def set_supported(self, package: Package, game_is_supported: Dict[int, bool], confidence: int):
		previous_supported: Dict[int, PackageGameSupport] = {}
		for support in package.supported_games.all():
			previous_supported[support.game.id] = support

		for game_id, supports in game_is_supported.items():
			game = self.session.query(Package).get(game_id)
			lookup = previous_supported.pop(game_id, None)
			if lookup is None:
				support = PackageGameSupport(package, game, confidence, supports)
				self.session.add(support)
			elif lookup.confidence <= confidence:
				lookup.supports = supports
				lookup.confidence = confidence

		for game, support in previous_supported.items():
			if support.confidence == confidence:
				self.session.delete(support)

	def update(self, package: Package) -> None:
		game_is_supported = {}
		if package.enable_game_support_detection:
			retval = self.resolve(package, [])
			for game_id in retval:
				game_is_supported[game_id] = True

		self.set_supported(package, game_is_supported, 1)
