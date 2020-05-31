title: API

## Authentication

Not all endpoints require authentication.
Authentication is done using Bearer tokens:

	Authorization: Bearer YOURTOKEN

You can use the `/api/whoami` to check authentication.

Tokens can be attained by visiting "API Tokens" on your profile page.

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

### Releases

* GET `/api/packages/<username>/<name>/releases/`
* POST `/api/packages/<username>/<name>/releases/new/`
	* Requires authentication.
	* `title`: human-readable name of the release.
	* `method`: Release-creation method, only `git` is supported.
	* `min_protocol`: (Optional) minimum Minetest protocol version. See [Minetest](#minetest).
	* `min_protocol`: (Optional) maximum Minetest protocol version. See [Minetest](#minetest).
	* If `git` release-creation method:
		* `ref` - git reference, eg: `master`.


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
* `q` - Query string
* `random` - When present, enable random ordering and ignore `sort`.
* `hide` - Hide content based on [Content Flags](/help/content_flags/).
* `sort` - Sort by (`name`, `views`, `date`, `score`).
* `order` - Sort ascending (`Asc`) or descending (`desc`).
* `protocol_version` - Only show packages supported by this Minetest protocol version.
