from flask import *
from flask_user import *

app = Flask(__name__)
app.config.from_pyfile('../config.cfg')

import models, views
