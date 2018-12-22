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


import flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from celery.schedules import crontab
from app import app
from app.models import *

class TaskError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr("TaskError: " + self.value)

class FlaskCelery(Celery):
	def __init__(self, *args, **kwargs):
		super(FlaskCelery, self).__init__(*args, **kwargs)
		self.patch_task()

		if 'app' in kwargs:
			self.init_app(kwargs['app'])

	def patch_task(self):
		TaskBase = self.Task
		_celery = self

		class ContextTask(TaskBase):
			abstract = True

			def __call__(self, *args, **kwargs):
				if flask.has_app_context():
					return TaskBase.__call__(self, *args, **kwargs)
				else:
					with _celery.app.app_context():
						return TaskBase.__call__(self, *args, **kwargs)

		self.Task = ContextTask

	def init_app(self, app):
		self.app = app
		self.config_from_object(app.config)

def make_celery(app):
	celery = FlaskCelery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
					broker=app.config['CELERY_BROKER_URL'])

	celery.init_app(app)
	return celery

celery = make_celery(app)

CELERYBEAT_SCHEDULE = {
	'topic_list_import': {
		'task': 'app.tasks.forumtasks.importTopicList',
		'schedule': crontab(minute=1, hour=1),
	}
}
celery.conf.beat_schedule = CELERYBEAT_SCHEDULE

from . import importtasks, forumtasks, emails
