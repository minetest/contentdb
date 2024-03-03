# ContentDB
# Copyright (C) 2024 rubenwardy
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


from flask import Blueprint, render_template, request
from sqlalchemy import or_

from app.models import Package, PackageState, db, PackageTranslation

bp = Blueprint("translate", __name__)


@bp.route("/translate/")
def translate():
	query = Package.query.filter(
			Package.state == PackageState.APPROVED,
			or_(
				Package.translation_url.is_not(None),
				Package.translations.any(PackageTranslation.language_id != "en")
			))

	has_langs = request.args.getlist("has_lang")
	for lang in has_langs:
		query = query.filter(Package.translations.any(PackageTranslation.language_id == lang))

	not_langs = request.args.getlist("not_lang")
	for lang in not_langs:
		query = query.filter(~Package.translations.any(PackageTranslation.language_id == lang))

	supports_translation = (query
			.order_by(Package.translation_url.is_(None), db.desc(Package.score))
			.all())

	return render_template("translate/index.html",
			supports_translation=supports_translation, has_langs=has_langs, not_langs=not_langs)
