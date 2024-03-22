# ContentDB
# Copyright (C) rubenwardy
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

import datetime

from app.logic.graphs import flatten_data


class DailyStat:
	date: datetime.date
	platform_minetest: int
	platform_other: int
	reason_new: int
	reason_dependency: int
	reason_update: int
	
	def __init__(self, date: str, x: int):
		self.date = datetime.date.fromisoformat(date)
		self.platform_minetest = x
		self.platform_other = 0
		self.reason_new = 0
		self.reason_dependency = 0
		self.reason_update = 0


def test_flatten_data():
	res = flatten_data([
		DailyStat("2022-03-28", 3),
		DailyStat("2022-03-29", 10),
		DailyStat("2022-04-01", 5),
		DailyStat("2022-04-02", 1)
	])

	assert res["start"] == "2022-03-28"
	assert res["end"] == "2022-04-02"
	assert res["platform_minetest"] == [3, 10, 0, 0, 5, 1]
