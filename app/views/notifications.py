from flask import *
from flask_user import current_user, login_required
from app import app
from app.models import *

@app.route("/notifications/")
@login_required
def notifications_page():
    return render_template("notifications/list.html")
