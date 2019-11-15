from . import app
from urllib.parse import urlparse

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

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
