# Content DB
# Copyright (C) 2018  rubenwardy
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


from flask import render_template, redirect, request, session, url_for, abort
from flask_user import login_required, current_user
from . import bp
from app.models import db, User, APIToken, Package, Permission
from app.utils import randomString
from app.querybuilder import QueryBuilder

from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *
from wtforms.ext.sqlalchemy.fields import QuerySelectField

class CreateAPIToken(FlaskForm):
	name	     = StringField("Name", [InputRequired(), Length(1, 30)])
	package      = QuerySelectField("Limit to package", allow_blank=True, \
			get_pk=lambda a: a.id, get_label=lambda a: a.title)
	submit	     = SubmitField("Save")


@bp.route("/user/tokens/")
@login_required
def list_tokens_redirect():
	return redirect(url_for("api.list_tokens", username=current_user.username))


@bp.route("/users/<username>/tokens/")
@login_required
def list_tokens(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	if not user.checkPerm(current_user, Permission.CREATE_TOKEN):
		abort(403)

	return render_template("api/list_tokens.html", user=user)


@bp.route("/users/<username>/tokens/new/", methods=["GET", "POST"])
@bp.route("/users/<username>/tokens/<int:id>/edit/", methods=["GET", "POST"])
@login_required
def create_edit_token(username, id=None):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	if not user.checkPerm(current_user, Permission.CREATE_TOKEN):
		abort(403)

	is_new = id is None

	token = None
	access_token = None
	if not is_new:
		token = APIToken.query.get(id)
		if token is None:
			abort(404)
		elif token.owner != user:
			abort(403)

		access_token = session.pop("token_" + str(token.id), None)

	form = CreateAPIToken(formdata=request.form, obj=token)
	form.package.query_factory = lambda: Package.query.filter_by(author=user).all()

	if request.method == "POST" and form.validate():
		if is_new:
			token = APIToken()
			token.owner = user
			token.access_token = randomString(32)

		form.populate_obj(token)
		db.session.add(token)
		db.session.commit() # save

		if is_new:
			# Store token so it can be shown in the edit page
			session["token_" + str(token.id)] = token.access_token

		return redirect(url_for("api.create_edit_token", username=username, id=token.id))

	return render_template("api/create_edit_token.html", user=user, form=form, token=token, access_token=access_token)


@bp.route("/users/<username>/tokens/<int:id>/reset/", methods=["POST"])
@login_required
def reset_token(username, id):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	if not user.checkPerm(current_user, Permission.CREATE_TOKEN):
		abort(403)

	token = APIToken.query.get(id)
	if token is None:
		abort(404)
	elif token.owner != user:
		abort(403)

	token.access_token = randomString(32)

	db.session.commit() # save

	# Store token so it can be shown in the edit page
	session["token_" + str(token.id)] = token.access_token

	return redirect(url_for("api.create_edit_token", username=username, id=token.id))


@bp.route("/users/<username>/tokens/<int:id>/delete/", methods=["POST"])
@login_required
def delete_token(username, id):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)

	if not user.checkPerm(current_user, Permission.CREATE_TOKEN):
		abort(403)

	is_new = id is None

	token = APIToken.query.get(id)
	if token is None:
		abort(404)
	elif token.owner != user:
		abort(403)

	db.session.delete(token)
	db.session.commit()

	return redirect(url_for("api.list_tokens", username=username))
