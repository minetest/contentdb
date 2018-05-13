import flask
from flask.ext.sqlalchemy import SQLAlchemy
from celery import Celery
from app import app
from app.models import *

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

from . import importtasks, forumtasks
