title: Package Configuration and Releases Guide

## Introduction

ContentDB will read configuration files in your package when doing a number of
tasks, including package and release creation.
This page details the ways in which you can use this to your advantage.

## .conf files

Every type of content can have a `.conf` file that contains the metadata.

The filename of the `.conf` file depends on the content type:

* `mod.conf` for mods.
* `modpack.conf` for mod packs.
* `game.conf` for games.
* `texture_pack.conf` for texture packs.

The `.conf` uses a key-value format, separated using equals. Here's a simple example:

	name = mymod
	description = A short description to show in the client.

ContentDB understands the following information:

* `description` - A short description to show in the client.
* `depends` - Comma-separated hard dependencies.
* `optional_depends` - Comma-separated hard dependencies.
* `min_minetest_version` - The minimum Minetest version this runs on.
* `min_minetest_version` - The minimum Minetest version this runs on.

and for mods only:

* `name` - the mod technical name.

## Controlling Release Creation

### Automatic Release Creation

The preferred way is to use [webhooks from GitLab or GitHub](/help/release_webhooks/).
You can also use the [API](/help/api/) to create releases.

### Min and Max Minetest Versions

When creating a release, the `.conf` file will be read to determine what Minetest
versions the release supports. If the `.conf` doesn't specify, then it is assumed
that is supports all versions.

This happens when you create a release via the ContentDB web interface, the
[API](/help/api/), or using a [GitLab/GitHub webhook](/help/release_webhooks/).

### Excluding files

You can exclude files from a release by using [gitattributes](https://git-scm.com/docs/gitattributes):


	.*		export-ignore
	sources		export-ignore
	*.zip		export-ignore


This will prevent any files from being included if they:

* Beginning with `.`
* or are named `sources` or are inside any directory named `sources`.
* or have an extension of "zip".
