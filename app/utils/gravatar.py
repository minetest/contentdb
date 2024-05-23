import hashlib


def get_gravatar(email: str):
	size = 64
	rating = "g"
	default = "retro"
	url = "https://secure.gravatar.com/avatar/"
	email_hash = hashlib.md5(email.encode("utf-8")).hexdigest()
	link = f"{url}{email_hash}?s={size}&d={default}&r={rating}"
	return link
