from . import app, utils
from .models import Permission, Package, PackageState, PackageRelease
from .utils import abs_url_for, url_set_query
from flask_login import current_user
from flask_babel import format_timedelta
from urllib.parse import urlparse

@app.context_processor
def inject_debug():
	return dict(debug=app.debug)

@app.context_processor
def inject_functions():
	check_global_perm = Permission.checkPerm
	return dict(abs_url_for=abs_url_for, url_set_query=url_set_query, check_global_perm=check_global_perm)

@app.context_processor
def inject_todo():
	todo_list_count = None
	if current_user and current_user.is_authenticated and current_user.canAccessTodoList():
		todo_list_count = Package.query.filter_by(state=PackageState.READY_FOR_REVIEW).count()
		todo_list_count += PackageRelease.query.filter_by(approved=False, task_id=None).count()

	return dict(todo_list_count=todo_list_count)

@app.template_filter()
def throw(err):
	raise Exception(err)

@app.template_filter()
def domain(url):
	return urlparse(url).netloc

@app.template_filter()
def date(value):
	return value.strftime("%Y-%m-%d")

@app.template_filter()
def datetime(value):
	return value.strftime("%Y-%m-%d %H:%M") + " UTC"

@app.template_filter()
def timedelta(value):
	return format_timedelta(value)

@app.template_filter()
def abs_url(url):
	return utils.abs_url(url)
