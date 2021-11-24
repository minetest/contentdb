# ContentDB
# Copyright (C) 2018-21 rubenwardy
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

from logging import Filter

import flask
from celery import Celery, signals
from celery.schedules import crontab
from app import app


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
		BaseTask : celery.Task = self.Task
		_celery = self

		class ContextTask(BaseTask):
			abstract = True

			def __call__(self, *args, **kwargs):
				if flask.has_app_context():
					return super(BaseTask, self).__call__(*args, **kwargs)
				else:
					with _celery.app.app_context():
						return super(BaseTask, self).__call__(*args, **kwargs)

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
		'schedule': crontab(minute=1, hour=1), # 0101
	},
	'package_score_update': {
		'task': 'app.tasks.pkgtasks.updatePackageScores',
		'schedule': crontab(minute=10, hour=1), # 0110
	},
	'check_for_updates': {
		'task': 'app.tasks.importtasks.check_for_updates',
		'schedule': crontab(minute=10, hour=1), # 0110
	},
	'send_pending_notifications': {
		'task': 'app.tasks.emails.send_pending_notifications',
		'schedule': crontab(minute='*/5'), # every 5 minutes
	},
	'send_notification_digests': {
		'task': 'app.tasks.emails.send_pending_digests',
		'schedule': crontab(minute=0, hour=14), # 1400
	},
	'delete_inactive_users': {
		'task': 'app.tasks.users.delete_inactive_users',
		'schedule': crontab(minute=15), # every hour at quarter past
	},
}
celery.conf.beat_schedule = CELERYBEAT_SCHEDULE

from . import importtasks, forumtasks, emails, pkgtasks, celery


# noinspection PyUnusedLocal
@signals.after_setup_logger.connect
def on_after_setup_logger(**kwargs):
	from app.maillogger import build_handler

	class ExceptionFilter(Filter):
		def filter(self, record):
			if record.exc_info:
				exc, _, _ = record.exc_info
				if exc == TaskError:
					return False

			return True

	logger = celery.log.get_default_logger()
	handler = build_handler(app)
	handler.addFilter(ExceptionFilter())
	logger.addHandler(handler)
