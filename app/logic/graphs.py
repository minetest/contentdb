from app.models import Package, PackageDailyStats, db


def flatten_data(package: Package):
	stats = package.daily_stats.order_by(db.asc(PackageDailyStats.date)).all()
	if len(stats) == 0:
		return None

	result = {
		"dates": [stat.date.isoformat() for stat in stats],
	}

	for key in ["platform_minetest", "platform_other", "reason_new",
			"reason_dependency", "reason_update"]:
		result[key] = [getattr(stat, key) for stat in stats]

	return result
