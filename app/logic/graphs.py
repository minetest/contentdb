from datetime import timedelta
from app.models import User, Package, PackageDailyStats, db
from sqlalchemy import func


def daterange(start_date, end_date):
	for n in range(int((end_date - start_date).days) + 1):
		yield start_date + timedelta(n)


keys = ["platform_minetest", "platform_other", "reason_new",
		"reason_dependency", "reason_update"]


def _flatten_data(stats):
	if len(stats) == 0:
		return None

	start_date = stats[0].date
	end_date = stats[-1].date
	result = {
		"start": start_date.isoformat(),
		"end": end_date.isoformat(),
	}

	for key in keys:
		result[key] = []

	i = 0
	for date in daterange(start_date, end_date):
		stat = stats[i]
		if stat.date == date:
			for key in keys:
				result[key].append(getattr(stat, key))

			i += 1
		else:
			for key in keys:
				result[key].append(0)

	return result


def get_package_stats(package: Package):
	stats = package.daily_stats.order_by(db.asc(PackageDailyStats.date)).all()
	return _flatten_data(stats)


def get_package_stats_for_user(user: User):
	stats = db.session \
		.query(PackageDailyStats.date,
			func.sum(PackageDailyStats.platform_minetest).label("platform_minetest"),
			func.sum(PackageDailyStats.platform_other).label("platform_other"),
			func.sum(PackageDailyStats.reason_new).label("reason_new"),
			func.sum(PackageDailyStats.reason_dependency).label("reason_dependency"),
			func.sum(PackageDailyStats.reason_update).label("reason_update")) \
		.filter(PackageDailyStats.package.has(author_id=user.id)) \
		.order_by(db.asc(PackageDailyStats.date)) \
		.group_by(PackageDailyStats.date) \
		.all()

	return _flatten_data(stats)
