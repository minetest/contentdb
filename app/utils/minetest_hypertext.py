# ContentDB
# Copyright (C) rubenwardy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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


def make_indent(w):
	return f"<img name=blank.png width={16*w} height=1>"


class MinetestHTMLParser(HTMLParser):
	def __init__(self, include_images):
		super().__init__()
		self.include_images = include_images

		self.completed_text = ""
		self.current_line = ""
		self.links = {}
		self.images = {}
		self.image_tooltips = {}
		self.is_preserving = False
		self.remove_until = None
		self.indent_level = 0

	def finish_line(self):
		self.completed_text += self.current_line.rstrip() + "\n"
		self.current_line = ""

	def handle_starttag(self, tag, attrs):
		if self.is_preserving or self.remove_until:
			return

		if tag == "p":
			pass
		elif tag == "pre":
			self.current_line += "<code>"
			self.is_preserving = True
		elif tag == "table":
			# Tables are currently unsupported and removed
			self.remove_until = "table"
			self.current_line += "<i>(table removed)</i>"
			self.finish_line()
		elif tag == "br":
			self.finish_line()
		elif tag == "h1" or tag == "h2":
			self.finish_line()
			self.current_line += "<big>"
		elif tag == "h3" or tag == "h4" or tag == "h5":
			self.finish_line()
			self.current_line += "<b>"
		elif tag == "a":
			for attr in attrs:
				if attr[0] == "href":
					name = f"link_{len(self.links)}"
					self.links[name] = attr[1]
					self.current_line += f"<action name={name}><u>"
					break
			else:
				self.current_line += "<action><u>"
		elif tag == "img":
			attr_by_value = get_attributes(attrs)
			if "src" in attr_by_value and self.include_images:
				name = f"image_{len(self.images)}"
				self.images[name] = attr_by_value["src"]
				width = attr_by_value.get("width", 128)
				height = attr_by_value.get("height", 128)
				self.current_line += f"<img name={name} width={width} height={height}>"

				if "alt" in attr_by_value:
					self.image_tooltips[name] = attr_by_value["alt"]
		elif tag == "b" or tag == "strong":
			self.current_line += "<b>"
		elif tag == "i" or tag == "em":
			self.current_line += "<i>"
		elif tag == "u":
			self.current_line += "<u>"
		elif tag == "li":
			if self.current_line.strip() != "":
				self.finish_line()
			else:
				self.current_line = ""

			self.current_line += make_indent(self.indent_level) + "• "
		elif tag == "code":
			self.current_line += "<code>"
		elif tag == "span":
			pass
		elif tag == "ul":
			self.indent_level += 1
		else:
			print("UNKNOWN TAG ", tag, attrs, file=sys.stderr)

	def handle_endtag(self, tag):
		if self.remove_until:
			if self.remove_until == tag:
				self.remove_until = None
			return

		if tag == "pre":
			self.current_line = self.current_line.rstrip() + "</code>"
			self.finish_line()
			self.is_preserving = False
		elif self.is_preserving:
			return
		elif tag == "p":
			self.current_line = self.current_line.rstrip()
			self.finish_line()
		elif tag == "h1" or tag == "h2":
			self.current_line += "</big>"
			self.finish_line()
		elif tag == "h3" or tag == "h4" or tag == "h5":
			self.current_line += "</b>"
			self.finish_line()
		elif tag == "a":
			self.current_line += "</u></action>"
		elif tag == "code":
			self.current_line += "</code>"
		elif tag == "b" or tag == "strong":
			self.current_line += "</b>"
		elif tag == "i" or tag == "em":
			self.current_line += "</i>"
		elif tag == "u":
			self.current_line += "</u>"
		elif tag == "li":
			self.finish_line()
		elif tag == "ul":
			self.indent_level = max(self.indent_level - 1, 0)

	def handle_data(self, data):
		if self.remove_until:
			return

		if not self.is_preserving:
			data = normalize_whitespace(data)
			if self.current_line.strip() == "":
				data = data.lstrip()

		self.current_line += data

	def handle_entityref(self, name):
		to_value = {
			"lt": "\\<",
			"gr": "\\>",
			"amp": "&",
			"quot": "\"",
			"apos": "'",
		}

		if name in to_value:
			self.current_line += to_value[name]
		else:
			self.current_line += f"&{name};"


def html_to_minetest(html, formspec_version=6, include_images=True):
	parser = MinetestHTMLParser(include_images)
	parser.feed(html)
	parser.finish_line()

	return {
		"head": HEAD,
		"body": parser.completed_text.strip() + "\n",
		"links": parser.links,
		"images":  parser.images,
		"image_tooltips": parser.image_tooltips,
	}
