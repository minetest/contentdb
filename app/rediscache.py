from . import r

# This file acts as a facade between the releases code and redis,
# and also means that the releases code avoids knowing about `app`

def make_download_key(ip, package):
	return "{}/{}/{}".format(ip, package.author.username, package.name)

def set_key(key, v):
	r.set(key, v)

def has_key(key):
	return r.exists(key)
