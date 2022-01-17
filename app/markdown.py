from functools import partial

import bleach
from bleach import Cleaner
from bleach.linkifier import LinkifyFilter
from bs4 import BeautifulSoup
from markdown import Markdown
from flask import Markup, url_for
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.inlinepatterns import Pattern
from xml.etree import ElementTree

# Based on
# https://github.com/Wenzil/mdx_bleach/blob/master/mdx_bleach/whitelist.py
#
# License: MIT

ALLOWED_TAGS = [
	"h1", "h2", "h3", "h4", "h5", "h6", "hr",
	"ul", "ol", "li",
	"p",
	"br",
	"pre",
	"code",
	"blockquote",
	"strong",
	"em",
	"a",
	"img",
	"table", "thead", "tbody", "tr", "th", "td",
	"div", "span", "del", "s",
]

ALLOWED_CSS = [
	"highlight", "codehilite",
	"hll", "c", "err", "g", "k", "l", "n", "o", "x", "p", "ch", "cm", "cp", "cpf", "c1", "cs",
	"gd", "ge", "gr", "gh", "gi", "go", "gp", "gs", "gu", "gt", "kc", "kd", "kn", "kp", "kr",
	"kt", "ld", "m", "s", "na", "nb", "nc", "no", "nd", "ni", "ne", "nf", "nl", "nn", "nx",
	"py", "nt", "nv", "ow", "w", "mb", "mf", "mh", "mi", "mo", "sa", "sb", "sc", "dl", "sd",
	"s2", "se", "sh", "si", "sx", "sr", "s1", "ss", "bp", "fm", "vc", "vg", "vi", "vm", "il",
]


def allow_class(_tag, name, value):
	return name == "class" and value in ALLOWED_CSS


ALLOWED_ATTRIBUTES = {
	"h1": ["id"],
	"h2": ["id"],
	"h3": ["id"],
	"h4": ["id"],
	"a": ["href", "title", "data-username"],
	"img": ["src", "title", "alt"],
	"code": allow_class,
	"div": allow_class,
	"span": allow_class,
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

md = None


def render_markdown(source):
	html = md.convert(source)

	cleaner = Cleaner(
		tags=ALLOWED_TAGS,
		attributes=ALLOWED_ATTRIBUTES,
		protocols=ALLOWED_PROTOCOLS,
		filters=[partial(LinkifyFilter, callbacks=bleach.linkifier.DEFAULT_CALLBACKS)])
	return cleaner.clean(html)


class DelInsExtension(Extension):
	def extendMarkdown(self, md):
		del_proc = SimpleTagInlineProcessor(r"(\~\~)(.+?)(\~\~)", "del")
		md.inlinePatterns.register(del_proc, "del", 200)

		ins_proc = SimpleTagInlineProcessor(r"(\+\+)(.+?)(\+\+)", "ins")
		md.inlinePatterns.register(ins_proc, "ins", 200)


RE_PARTS = dict(
	USER=r"[A-Za-z0-9._-]*\b",
	REPO=r"[A-Za-z0-9_]+\b"
)


class MentionPattern(Pattern):
	ANCESTOR_EXCLUDES = ("a",)

	def __init__(self, config, md):
		MENTION_RE = r"(@({USER})(?:\/({REPO}))?)".format(**RE_PARTS)
		super(MentionPattern, self).__init__(MENTION_RE, md)
		self.config = config

	def handleMatch(self, m):
		from app.models import User

		label = m.group(2)
		user = m.group(3)
		package_name = m.group(4)
		if package_name:
			el = ElementTree.Element("a")
			el.text = label
			el.set("href", url_for("packages.view", author=user, name=package_name))
			return el
		else:
			if User.query.filter_by(username=user).count() == 0:
				return None

			el = ElementTree.Element("a")
			el.text = label
			el.set("href", url_for("users.profile", username=user))
			el.set("data-username", user)
			return el


class MentionExtension(Extension):
	def __init__(self, *args, **kwargs):
		super(MentionExtension, self).__init__(*args, **kwargs)

	def extendMarkdown(self, md):
		md.ESCAPED_CHARS.append("@")
		md.inlinePatterns.register(MentionPattern(self.getConfigs(), md), "mention", 20)


MARKDOWN_EXTENSIONS = ["fenced_code", "tables", "codehilite", "toc", DelInsExtension(), MentionExtension()]
MARKDOWN_EXTENSION_CONFIG = {
	"fenced_code": {},
	"tables": {},
	"codehilite": {
		"guess_lang": False,
	}
}


def init_markdown(app):
	global md

	md = Markdown(extensions=MARKDOWN_EXTENSIONS,
			extension_configs=MARKDOWN_EXTENSION_CONFIG,
			output_format="html5")

	@app.template_filter()
	def markdown(source):
		return Markup(render_markdown(source))


def get_headings(html: str):
	soup = BeautifulSoup(html, "html.parser")
	headings = soup.find_all(["h1", "h2", "h3"])

	root = []
	stack = []
	for heading in headings:
		this = {"link": heading.get("id") or "", "text": heading.text, "children": []}
		this_level = int(heading.name[1:]) - 1

		while this_level <= len(stack):
			stack.pop()

		if len(stack) > 0:
			stack[-1]["children"].append(this)
		else:
			root.append(this)

		stack.append(this)

	return root


def get_user_mentions(html: str) -> set:
	soup = BeautifulSoup(html, "html.parser")
	links = soup.select("a[data-username]")
	return set([x.get("data-username") for x in links])
