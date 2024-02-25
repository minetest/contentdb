import os
from app.tasks.minetestcheck.translation import parse_tr


def test_parses_tr():
	dirname = os.path.dirname(__file__)
	filepath = os.path.join(dirname, "test_file.fr.tr")
	out = parse_tr(filepath)

	assert out.language == "fr"
	assert out.textdomain == "foobar"
	assert len(out.entries) == 1
	assert out.entries["Hello, World!"] == "Bonjour, Monde!"
