# ContentDB
# Copyright (C) 2022 rubenwardy
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

import urllib.parse as urlparse
from typing import Optional, Dict, List


def url_set_query(url: str, params: Dict[str, str]) -> str:
	url_parts = list(urlparse.urlparse(url))
	query = dict(urlparse.parse_qsl(url_parts[4]))
	query.update(params)

	url_parts[4] = urlparse.urlencode(query)
	return urlparse.urlunparse(url_parts)


def url_get_query(parsed_url: urlparse.ParseResult) -> Dict[str, List[str]]:
	return urlparse.parse_qs(parsed_url.query)


def clean_youtube_url(url: str) -> Optional[str]:
	parsed = urlparse.urlparse(url)
	print(parsed)
	if (parsed.netloc == "www.youtube.com" or parsed.netloc == "youtube.com") and parsed.path == "/watch":
		print(url_get_query(parsed))
		video_id = url_get_query(parsed).get("v", [None])[0]
		if video_id:
			return url_set_query("https://www.youtube.com/watch", {"v": video_id})

	elif parsed.netloc == "youtu.be":
		return url_set_query("https://www.youtube.com/watch", {"v": parsed.path[1:]})

	return None
