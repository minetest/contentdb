def parse_conf(string):
	retval = {}
	lines = string.split("\n")
	i = 0	
	while i < len(lines):
		line = lines[i].lstrip()
		def syntax_error(message):
			raise SyntaxError("Line " + (i + 1) + ": " + message)
		if line.startswith("#") or line == "":
			i += 1
			continue
		key_value = line.split("=", 2)
		if len(key_value) < 2:
			syntax_error("No value given")
		key = key_value[0].rstrip()
		if key == "":
			syntax_error("Empty key")
		value = key_value[1].lstrip()
		if value == "":
			syntax_error("Empty value")
		if value.startswith('"""'):
			value = value[3:]
			value_lines = []
			closed = False
			while i < len(lines):
				if value.endswith('"""'):
					closed = True
					value = value[:-3]
					break
				value_lines.append(value)
				i += 1
				value = lines[i]
			if not closed:
				i -= 1
				syntax_error("Unclosed multiline value")
			value_lines.push(value)
			value = "\n".join(value_lines)
		else:
			value = value.rstrip()
		if key in retval:
			syntax_error("Duplicate key")
		retval[key] = value
		print(i)
		i += 1
	return retval