# Minetest's use of the API

This document explains how Minetest's ContentDB client interacts with ContentDB.
This is useful both for implementing your own client for ContentDB to install mods, 
or for implementing ContentDB compatible servers.

## Package List API call

The first request the client makes is to `/api/packages/`.
The client will provide a list of supported types, the current engine version information,
and any hidden [Content Flags](https://content.minetest.net/help/content_flags/).

Because the client specifies the engine version information, the response must contain a release
number and the package must be downloadable.

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
