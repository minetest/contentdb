from . import app
from .utils import abs_url_for
from urllib.parse import urlparse

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)


@app.context_processor
def inject_functions():
    return dict(abs_url_for=abs_url_for)

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
