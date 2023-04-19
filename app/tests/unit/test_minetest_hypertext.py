from app.utils.minetest_hypertext import html_to_minetest


conquer_html = """
<p>
Welcome to <b>Conquer</b>, a mod that adds RTS gameplay. It allows players to start
Conquer sub-games, where they can place buildings, train units, and
fight other players.
</p>

<h2>Starting or joining a session</h2>

<p>
You can list running sessions by typing:
</p>

<pre><code>/conquer list
new line

another new line</code></pre>

<p>
You'll switch into Conquer playing mode, where you will be given buildings that you can place.
You'll need to place a keep, which you must protect at all costs.
</p>

<p>
You may leave a game and return to normal playing mode at anytime by typing:
</p>

<h2>Conquer GUI</h2>

<p>
The Conquer GUI is the central place for monitoring your kingdom.
Once in a session, you can view it by pressing the inventory key (I),
or by punching/right-clicking the keep node.
</p>
"""


conquer_expected = """
Welcome to <b>Conquer</b>, a mod that adds RTS gameplay. It allows players to start Conquer sub-games, where they can place buildings, train units, and fight other players.

<big>Starting or joining a session</big>
You can list running sessions by typing:
<code>/conquer list
new line

another new line</code>
You'll switch into Conquer playing mode, where you will be given buildings that you can place. You'll need to place a keep, which you must protect at all costs.
You may leave a game and return to normal playing mode at anytime by typing:

<big>Conquer GUI</big>
The Conquer GUI is the central place for monitoring your kingdom. Once in a session, you can view it by pressing the inventory key (I), or by punching/right-clicking the keep node.
"""


def test_conquer():
	assert html_to_minetest(conquer_html)["body"].strip() == conquer_expected.strip()


def test_images():
	html = """
		<img src="/path/to/img.png">
	"""

	expected = "<img name=image_0 width=128 height=128>"
	result = html_to_minetest(html)
	assert result["body"].strip() == expected.strip()
	assert len(result["images"]) == 1
	assert result["images"]["image_0"] == "/path/to/img.png"


def test_bullets():
	html = """
		<ul>
			<li>One</li>
			<li>two three<ul><li>sub one</li><li>sub two</li></ul></li>
			<li>four</li>
		</ul>
	"""

	expected = "<img name=blank.png width=16 height=1>• One\n" \
		"<img name=blank.png width=16 height=1>• two three\n" \
		"<img name=blank.png width=32 height=1>• sub one\n" \
		"<img name=blank.png width=32 height=1>• sub two\n\n" \
		"<img name=blank.png width=16 height=1>• four\n"

	result = html_to_minetest(html)
	assert result["body"].strip() == expected.strip()


def test_inline():
	html = """
		<b>One <i>two</i> three</b>
	"""

	expected = "<b>One <i>two</i> three</b>"
	result = html_to_minetest(html)
	assert result["body"].strip() == expected.strip()
