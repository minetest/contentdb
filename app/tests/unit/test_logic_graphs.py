import datetime

from app.logic.graphs import _flatten_data


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
	res = _flatten_data([
		DailyStat("2022-03-28", 3),
		DailyStat("2022-03-29", 10),
		DailyStat("2022-04-01", 5),
		DailyStat("2022-04-02", 1)
	])

	assert res["start"] == datetime.date.fromisoformat("2022-03-28")
	assert res["end"] == datetime.date.fromisoformat("2022-04-02")
	assert res["platform_minetest"] == [3, 10, 0, 0, 5, 1]
