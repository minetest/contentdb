# ContentDB
# Copyright (C) 2020  rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import Blueprint, make_response
from sqlalchemy.sql.expression import func

from app.models import Package, db, User, UserRank, PackageState

bp = Blueprint("metrics", __name__)

def generate_metrics(full=False):
	def write_single_stat(name, help, type, value):
		fmt = "# HELP {name} {help}\n# TYPE {name} {type}\n{name} {value}\n\n"

		return fmt.format(name=name, help=help, type=type, value=value)

	def gen_labels(labels):
		pieces = [key + "=" + str(val) for key, val in labels.items()]
		return ",".join(pieces)


	def write_array_stat(name, help, type, data):
		ret = "# HELP {name} {help}\n# TYPE {name} {type}\n" \
			.format(name=name, help=help, type=type)

		for entry in data:
			assert(len(entry) == 2)
			ret += "{name}{{{labels}}} {value}\n" \
				.format(name=name, labels=gen_labels(entry[0]), value=entry[1])

		return ret + "\n"

	downloads_result = db.session.query(func.sum(Package.downloads)).one_or_none()
	downloads = 0 if not downloads_result or not downloads_result[0] else downloads_result[0]

	packages = Package.query.filter_by(state=PackageState.APPROVED).count()
	users = User.query.filter(User.rank != UserRank.NOT_JOINED).count()

	ret = ""
	ret += write_single_stat("contentdb_packages", "Total packages", "counter", packages)
	ret += write_single_stat("contentdb_users", "Number of registered users", "counter", users)
	ret += write_single_stat("contentdb_downloads", "Total downloads", "counter", downloads)

	if full:
		scores = Package.query.join(User).with_entities(User.username, Package.name, Package.score) \
			.filter(Package.state==PackageState.APPROVED).all()

		ret += write_array_stat("contentdb_package_score", "Package score", "gauge",
				[({ "author": score[0], "name": score[1] }, score[2])  for score in scores])
	else:
		score_result = db.session.query(func.sum(Package.score)).one_or_none()
		score = 0 if not score_result or not score_result[0] else score_result[0]
		ret += write_single_stat("contentdb_score", "Total package score", "gauge", score)

	return ret

@bp.route("/metrics")
def metrics():
	response = make_response(generate_metrics(), 200)
	response.mimetype = "text/plain"
	return response
