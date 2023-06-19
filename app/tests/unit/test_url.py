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

from app.utils.url import clean_youtube_url


def test_clean_youtube_url():
	assert clean_youtube_url(
		"https://www.youtube.com/watch?v=AABBCC") == "https://www.youtube.com/watch?v=AABBCC"
	assert clean_youtube_url(
		"https://www.youtube.com/watch?v=boGcB4H5-WA&other=1") == "https://www.youtube.com/watch?v=boGcB4H5-WA"
	assert clean_youtube_url("https://www.youtube.com/watch?kk=boGcB4H5-WA&other=1") is None
	assert clean_youtube_url("https://www.bob.com/watch?v=AABBCC") is None

	assert clean_youtube_url("https://youtu.be/boGcB4H5-WA") == "https://www.youtube.com/watch?v=boGcB4H5-WA"
	assert clean_youtube_url("https://youtu.be/boGcB4H5-WA?this=1") == "https://www.youtube.com/watch?v=boGcB4H5-WA"
