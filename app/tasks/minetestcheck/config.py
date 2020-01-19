def parse_conf(string):
	retval = {}
	for line in string.split("\n"):
		idx = line.find("=")
		if idx > 0:
			key   = line[:idx].strip()
			value = line[idx+1:].strip()
			retval[key] = value

	return retval
