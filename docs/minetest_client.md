# Minetest's use of the API

This document explains how Minetest's ContentDB client interacts with ContentDB.
This is useful both for implementing your own client for ContentDB to install mods, 
or for implementing ContentDB compatible servers.

## Package List API call

The client makes a single [API](https://content.minetest.net/help/api/) request to `/api/packages/`.

The query arguments will include a list of supported types, the current
[engine version](https://content.minetest.net/api/minetest_versions/),
and any hidden [Content Flags](https://content.minetest.net/help/content_flags/).

Example URL:
<https://content.minetest.net/api/packages/?type=mod&type=game&type=txp&protocol_version=39&engine_version=5.3.0&hide=nonfree&hide=desktop_default>

Example response:

```json
[
    {
        "author": "Wuzzy",
        "name": "mineclone2",
        "release": 4209,
        "short_description": "A short description",
        "thumbnail": "https://content.minetest.net/thumbnails/1/tgbH5CwlAZ.jpg",
        "title": "MineClone 2",
        "type": "game"
    }
]
```

`thumbnail` is optional, but all other fields are required. 

`type` is one of `mod`, `game`, or `txp`.

`release` is the release ID. Newer releases have higher IDs.
Minetest compares this ID to a locally stored version to detect whether a package has updates.

Because the client specifies the engine version information, the response must contain a release
number and the package must be downloadable.

## Screenshots

The client can simply download the URL mentioned in `thumbnail`.

## Downloading and installing

The client downloads packages by constructing a URL for the release and downloading it:

```
https://content.minetest.net/packages/<author>/<name>/releases/<release>/download/
```

This supports redirects.

The client will edit the .conf of the installed content to add `author`, `name`, and `release` to
track the installed release to detect updates in the future.

## View in browser

The client will open the package in a browser by constructing the following URL

```
https://content.minetest.net/packages/<author>/<name>/
```
