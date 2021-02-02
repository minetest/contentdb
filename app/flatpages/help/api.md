title: API

## Authentication

Not all endpoints require authentication.
Authentication is done using Bearer tokens:

```bash
curl -H "Authorization: Bearer YOURTOKEN" https://content.minetest.net/api/whoami/
```

Tokens can be attained by visiting [Settings > API Tokens](/user/tokens/).

## Endpoints

### Misc

* GET `/api/whoami/` - Json dictionary with the following keys:
	* `is_authenticated` - True on successful API authentication
	* `username` - Username of the user authenticated as, null otherwise.
	* 4xx status codes will be thrown on unsupported authentication type, invalid access token, or other errors.

### Packages

* GET `/api/packages/` - See [Package Queries](#package-queries)
* GET `/api/scores/` - See [Package Queries](#package-queries)
* GET `/api/packages/<username>/<name>/`
* GET `/api/packages/<username>/<name>/dependencies/`
	* If query argument `only_hard` is present, only hard deps will be returned.
* GET `/api/tags/` - List of:
	* `name` - technical name
	* `title` - human-readable title
	* `description` - tag description or null
* GET `/api/homepage/`
	* `count` - number of packages
	* `downloads` - get number of downloads
	* `new` - new packages
	* `updated` - recently updated packages
	* `pop_mod` - popular mods
	* `pop_txp` - popular textures
	* `pop_game` - popular games
	* `high_reviewed` - highest reviewed

### Releases

* GET `/api/packages/<username>/<name>/releases/` (List)
* POST `/api/packages/<username>/<name>/releases/new/` (Create)
	* Requires authentication.
	* Body is multipart form if zip upload, JSON otherwise.
	* `title`: human-readable name of the release.
	* For Git release creation:
		* `method`: must be `git`.
		* `ref`: (Optional) git reference, eg: `master`.
	* For zip upload release creation: 
		* `file`: multipart file to upload, like `<input type=file>`.
	* You can set min and max Minetest Versions [using the content's .conf file](/help/package_config/).

Examples:

```bash
# Create release from Git
curl -X POST https://content.minetest.net/api/packages/username/name/releases/new/ \
	-H "Authorization: Bearer YOURTOKEN" -H "Content-Type: application/json" \
	-d "{\"method\": \"git\", \"title\": \"My Release\", \"ref\": \"master\" }"

# Create release from zip upload
curl https://content.minetest.net/api/packages/username/name/releases/new/ \
	-H "Authorization: Bearer YOURTOKEN" \
	-F title="My Release" -F file=@path/to/file.zip
```

### Topics

* GET `/api/topics/` - Supports [Package Queries](#package-queries), and the following two options:
	* `show_added` - Show topics which exist as packages, default true.
	* `show_discarded` - Show topics which have been marked as outdated, default false.

### Minetest

* GET `/api/minetest_versions/`


## Package Queries

Example:

	/api/packages/?type=mod&type=game&q=mobs+fun&hide=nonfree&hide=gore

Supported query parameters:

* `type` - Package types (`mod`, `game`, `txp`).
* `q` - Query string.
* `author` - Filter by author.
* `tag` - Filter by tags.
* `random` - When present, enable random ordering and ignore `sort`.
* `limit` - Return at most `limit` packages.
* `hide` - Hide content based on [Content Flags](/help/content_flags/).
* `sort` - Sort by (`name`, `title`, `score`, `reviews`, `downloads`, `created_at`, `approved_at`, `last_release`).
* `order` - Sort ascending (`asc`) or descending (`desc`).
* `protocol_version` - Only show packages supported by this Minetest protocol version.
* `engine_version` - Only show packages supported by this Minetest engine version, eg: `5.3.0`.
* `fmt` - How the response is formated.
	* `keys` - author/name only.
	* `short` - stuff needed for the Minetest client. 


## Topic Queries

Example:

	/api/topics/?q=mobs

Supported query parameters:

* `q` - Query string.
* `sort` - Sort by (`name`, `views`, `date`).
* `order` - Sort ascending (`asc`) or descending (`desc`).
* `show_added` - Show topics that have an existing package.
* `show_discarded` - Show topics marked as discarded.
* `limit` - Return at most `limit` topics.
