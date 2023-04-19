from html.parser import HTMLParser
import re
import sys


def normalize_whitespace(x):
	return re.sub(r"\s+", " ", x)


assert normalize_whitespace(" one  three\nfour\n\n") == " one three four "


# Styles and custom tags
HEAD = normalize_whitespace("""
	<tag name=code color=#7bf font=mono>
	<tag name=action color=#77f hovercolor=#aaf>
""").strip()


def get_attributes(attrs):
	retval = {}
	for attr in attrs:
		retval[attr[0]] = attr[1]
	return retval


class MinetestHTMLParser(HTMLParser):
	def __init__(self, include_images):
		super().__init__()
		self.include_images = include_images

		self.text_buffer = ""
		self.has_line_started = False
		self.links = {}
		self.images = {}
		self.image_tooltips = {}
		self.is_preserving = False
		self.remove_until = None

	def handle_starttag(self, tag, attrs):
		if self.is_preserving or self.remove_until:
			return

		print("OPEN", tag, file=sys.stderr)

		self.has_line_started = True
		if tag == "p":
			self.has_line_started = False
		elif tag == "pre":
			self.text_buffer += "<code>"
			self.is_preserving = True
			self.has_line_started = False
		elif tag == "table":
			# Tables are currently unsupported and removed
			self.remove_until = "table"
			self.text_buffer += "<i>(table removed)</i>\n"
		elif tag == "br":
			self.text_buffer += "\n"
			self.has_line_started = False
		elif tag == "h1" or tag == "h2":
			self.text_buffer += "\n<big>"
		elif tag == "h3" or tag == "h4" or tag == "h5":
			self.text_buffer += "\n<b>"
		elif tag == "a":
			for attr in attrs:
				if attr[0] == "href":
					name = f"link_{len(self.links)}"
					self.links[name] = attr[1]
					self.text_buffer += f"<action name={name}><u>"
					break
			else:
				self.text_buffer += "<action><u>"
		elif tag == "img":
			attr_by_value = get_attributes(attrs)
			if "src" in attr_by_value and self.include_images:
				name = f"image_{len(self.images)}"
				self.images[name] = attr_by_value["src"]
				width = attr_by_value.get("width", 128)
				height = attr_by_value.get("height", 128)
				self.text_buffer += f"<img name={name} width={width} height={height}>"

				if "alt" in attr_by_value:
					self.image_tooltips[name] = attr_by_value["alt"]
		elif tag == "b" or tag == "strong":
			self.text_buffer += "<b>"
		elif tag == "i" or tag == "em":
			self.text_buffer += "<i>"
		elif tag == "u":
			self.text_buffer += "<u>"
		elif tag == "li":
			self.has_line_started = False
			self.text_buffer += "• "
		elif tag == "code":
			self.text_buffer += "<code>"
		elif tag == "span" or tag == "ul":
			pass
		else:
			print("UNKNOWN TAG ", tag, attrs, file=sys.stderr)

	def handle_endtag(self, tag):
		if self.remove_until:
			if self.remove_until == tag:
				self.remove_until = None
			return

		print("CLOSE", tag, file=sys.stderr)

		if tag == "pre":
			self.text_buffer = self.text_buffer.rstrip()
			self.text_buffer += "</code>\n"
			self.is_preserving = False
			self.has_line_started = False
		elif self.is_preserving:
			return
		elif tag == "p":
			self.text_buffer = self.text_buffer.rstrip()
			self.text_buffer += "\n"
			self.has_line_started = False
		elif tag == "h1" or tag == "h2":
			self.text_buffer += "</big>\n"
			self.has_line_started = False
		elif tag == "h3" or tag == "h4" or tag == "h5":
			self.text_buffer += "</b>\n"
			self.has_line_started = False
		elif tag == "a":
			self.text_buffer += "</u></action>"
		elif tag == "code":
			self.text_buffer += "</code>"
		elif tag == "b" or tag == "strong":
			self.text_buffer += "</b>"
		elif tag == "i" or tag == "em":
			self.text_buffer += "</i>"
		elif tag == "u":
			self.text_buffer += "</u>"
		elif tag == "li":
			self.text_buffer += "\n"
		# else:
		# 	print("END", tag, file=sys.stderr)

	def handle_data(self, data):
		print(f"DATA \"{data}\"", file=sys.stderr)
		if self.remove_until:
			return

		if not self.is_preserving:
			data = normalize_whitespace(data)
			if not self.has_line_started:
				data = data.lstrip()

		self.text_buffer += data
		self.has_line_started = True

	def handle_entityref(self, name):
		to_value = {
			"lt": "\\<",
			"gr": "\\>",
			"amp": "&",
			"quot": "\"",
			"apos": "'",
		}

		if name in to_value:
			self.text_buffer += to_value[name]
		else:
			self.text_buffer += f"&{name};"


def html_to_minetest(html, formspec_version=6, include_images=True):
	parser = MinetestHTMLParser(include_images)
	parser.feed(html)
	return {
		"head": HEAD,
		"body": parser.text_buffer.strip() + "\n\n",
		"links": parser.links,
		"images":  parser.images,
		"image_tooltips": parser.image_tooltips,
	}
