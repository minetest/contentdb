import os

import pytest

from app.tasks.minetestcheck.translation import parse_tr


def test_parses_tr():
	dirname = os.path.dirname(__file__)
	filepath = os.path.join(dirname, "foo.bar.fr.tr")
	out = parse_tr(filepath)

	assert out.language == "fr"
	assert out.textdomain == "foo.bar"
	assert len(out.entries) == 5
	assert out.entries["Hello, World!"] == "Bonjour, Monde!"
	assert out.entries["Hello @1!"] == "@1, salut!"
	assert out.entries["Cats = cool"] == "Chats = cool"
	assert out.entries["A \n newline"] == "Une \nnouvelle ligne"
	assert out.entries["Maybe @\n@=@"] == "Peut être @\n@=@"


def test_parses_tr_infers_textdomain():
	dirname = os.path.dirname(__file__)
	filepath = os.path.join(dirname, "no_textdomain_comment.fr.tr")
	out = parse_tr(filepath)

	assert out.language == "fr"
	assert out.textdomain == "no_textdomain_comment"
	assert len(out.entries) == 1
	assert out.entries["Hello, World!"] == "Bonjour, Monde!"


def test_parses_tr_error_on_textdomain_mismatch():
	dirname = os.path.dirname(__file__)
	filepath = os.path.join(dirname, "textdomain_mismatch.fr.tr")

	with pytest.raises(SyntaxError) as e:
		parse_tr(filepath)

	assert str(e.value) == "Line 1: The filename's textdomain (textdomain_mismatch) should match the comment (foobar)"


def test_parses_tr_error_on_missing_eq():
	dirname = os.path.dirname(__file__)
	filepath = os.path.join(dirname, "err_missing_eq.fr.tr")

	with pytest.raises(SyntaxError) as e:
		parse_tr(filepath)

	assert str(e.value) == "Line 4: Missing = in line"


def test_parses_tr_error_on_bad_escape():
	dirname = os.path.dirname(__file__)
	filepath = os.path.join(dirname, "bad_escape.fr.tr")

	with pytest.raises(SyntaxError) as e:
		parse_tr(filepath)

	assert str(e.value) == "Line 1: Unknown escape character: x"
