title: API

## Authentication

Not all endpoints require authentication.
Authentication is done using Bearer tokens:

```bash
curl -H "Authorization: Bearer YOURTOKEN" https://content.minetest.net/api/whoami/
```

Tokens can be attained by visiting [Settings > API Tokens](/user/tokens/).

* GET `/api/whoami/` - JSON dictionary with the following keys:
    * `is_authenticated` - True on successful API authentication
    * `username` - Username of the user authenticated as, null otherwise.
    * 4xx status codes will be thrown on unsupported authentication type, invalid access token, or other errors.

## Packages

* GET `/api/packages/` (List)
    * See [Package Queries](#package-queries)
* GET `/api/packages/<username>/<name>/` (Read)
* PUT `/api/packages/<author>/<name>/` (Update)
    * JSON dictionary with any of these keys (all are optional):
        * `title`: Human-readable title.
        * `short_desc`
        * `desc`
        * `type`: One of `GAME`, `MOD`, `TXP`.
        * `license`: A license name.
        * `media_license`: A license name.
        * `repo`: Git repo URL.
        * `website`: Website URL.
        * `issue_tracker`: Issue tracker URL.
* GET `/api/packages/<username>/<name>/dependencies/`
    * If query argument `only_hard` is present, only hard deps will be returned.
* GET `/api/scores/`
    * See [Package Queries](#package-queries)
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

### Package Queries

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


## Releases

* GET `/api/packages/<username>/<name>/releases/` (List)
    * Returns array of release dictionaries with keys:
        * `id`: release ID
        * `title`: human-readable title
        * `release_date`: Date released
        * `url`: download URL
        * `commit`: commit hash or null
        * `downloads`: number of downloads
        * `min_minetest_version`: dict or null, minimum supported minetest version (inclusive).
        * `max_minetest_version`: dict or null, minimum supported minetest version (inclusive).
* GET `/api/packages/<username>/<name>/releases/<id>/` (Read)
* POST `/api/packages/<username>/<name>/releases/new/` (Create)
    * Requires authentication.
    * Body can be JSON or multipart form data. Zip uploads must be multipart form data.
    * `title`: human-readable name of the release.
    * For Git release creation:
        * `method`: must be `git`.
        * `ref`: (Optional) git reference, eg: `master`.
    * For zip upload release creation: 
        * `file`: multipart file to upload, like `<input type=file>`.
    * You can set min and max Minetest Versions [using the content's .conf file](/help/package_config/).
* DELETE `/api/packages/<username>/<name>/releases/<id>/` (Delete)
    * Requires authentication.
    * Deletes release.
  
Examples:

```bash
# Create release from Git
curl -X POST https://content.minetest.net/api/packages/username/name/releases/new/ \
    -H "Authorization: Bearer YOURTOKEN" -H "Content-Type: application/json" \
    -d "{\"method\": \"git\", \"title\": \"My Release\", \"ref\": \"master\" }"

# Create release from zip upload
curl -X POST https://content.minetest.net/api/packages/username/name/releases/new/ \
    -H "Authorization: Bearer YOURTOKEN" \
    -F title="My Release" -F file=@path/to/file.zip

# Delete release
curl -X DELETE https://content.minetest.net/api/packages/username/name/releases/3/ \
    -H "Authorization: Bearer YOURTOKEN" 
```


## Screenshots

* GET `/api/packages/<username>/<name>/screenshots/` (List)
    * Returns array of screenshot dictionaries with keys:
        * `id`: screenshot ID
        * `approved`: true if approved and visible.
        * `title`: human-readable name for the screenshot, shown as a caption and alt text.
        * `url`: absolute URL to screenshot.
        * `created_at`: ISO time.
        * `order`: Number used in ordering.
* GET `/api/packages/<username>/<name>/screenshots/<id>/` (Read)
    * Returns screenshot dictionary like above.
* POST `/api/packages/<username>/<name>/screenshots/new/` (Create)
    * Requires authentication.
    * Body is multipart form data.
    * `title`: human-readable name for the screenshot, shown as a caption and alt text.
    * `file`: multipart file to upload, like `<input type=file>`.
* DELETE `/api/packages/<username>/<name>/screenshots/<id>/` (Delete)
    * Requires authentication.
    * Deletes screenshot.
* POST `/api/packages/<username>/<name>/screenshots/order/`
    * Requires authentication.
    * Body is a JSON array containing the screenshot IDs in their order.

Examples:

```bash
# Create screenshots
curl -X POST https://content.minetest.net/api/packages/username/name/screenshots/new/ \
    -H "Authorization: Bearer YOURTOKEN" \
    -F title="My Release" -F file=@path/to/screnshot.png

# Delete screenshot
curl -X DELETE https://content.minetest.net/api/packages/username/name/screenshots/3/ \
    -H "Authorization: Bearer YOURTOKEN" 
    
# Reorder screenshots
curl -X POST https://content.minetest.net/api/packages/username/name/screenshots/order/ \
    -H "Authorization: Bearer YOURTOKEN" -H "Content-Type: application/json" \
    -d "[13, 2, 5, 7]"
```


## Topics

* GET `/api/topics/` - Supports [Package Queries](#package-queries), and the following two options:
    * `show_added` - Show topics which exist as packages, default true.
    * `show_discarded` - Show topics which have been marked as outdated, default false.

### Topic Queries

Example:

    /api/topics/?q=mobs

Supported query parameters:

* `q` - Query string.
* `sort` - Sort by (`name`, `views`, `date`).
* `order` - Sort ascending (`asc`) or descending (`desc`).
* `show_added` - Show topics that have an existing package.
* `show_discarded` - Show topics marked as discarded.
* `limit` - Return at most `limit` topics.


## Minetest

* GET `/api/minetest_versions/`
