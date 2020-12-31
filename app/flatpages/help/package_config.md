title: Package Configuration and Releases Guide

## Introduction

ContentDB will read configuration files in your package when doing several
tasks, including package and release creation. This page details how you can use
this to your advantage.

## .conf files

### What is a content .conf file?

Every type of content can have a `.conf` file that contains the metadata.

The filename of the `.conf` file depends on the content type:

* `mod.conf` for mods.
* `modpack.conf` for mod packs.
* `game.conf` for games.
* `texture_pack.conf` for texture packs.

The `.conf` uses a key-value format, separated using equals. Here's a simple example:

	name = mymod
	description = A short description to show in the client.

### Understood values

ContentDB understands the following information:

* `description` - A short description to show in the client.
* `depends` - Comma-separated hard dependencies.
* `optional_depends` - Comma-separated soft dependencies.
* `min_minetest_version` - The minimum Minetest version this runs on, see [Min and Max Minetest Versions](#min_max_versions).
* `max_minetest_version` - The maximum Minetest version this runs on, see [Min and Max Minetest Versions](#min_max_versions).

and for mods only:

* `name` - the mod technical name.

## Controlling Release Creation

### Git-based Releases and Submodules

ContentDB can create releases from a Git repository.
It will include submodules in the resulting archive.
Simply set VCS Repository in the package's meta to a Git repository, and then
choose Git as the method when creating a release.

### Automatic Release Creation

The preferred way is to use [webhooks from GitLab or GitHub](/help/release_webhooks/).
You can also use the [API](/help/api/) to create releases.

### Min and Max Minetest Versions

<a name="min_max_versions" />

When creating a release, the `.conf` file will be read to determine what Minetest
versions the release supports. If the `.conf` doesn't specify, then it is assumed
that it supports all versions.

This happens when you create a release via the ContentDB web interface, the
[API](/help/api/), or using a [GitLab/GitHub webhook](/help/release_webhooks/).

Here's an example config:

	name = mymod
	min_minetest_version = 5.0
	max_minetest_version = 5.3

Leaving out min or max to have them set as "None".

### Excluding files

When using Git to create releases,
you can exclude files from a release by using [gitattributes](https://git-scm.com/docs/gitattributes):


	.*		export-ignore
	sources		export-ignore
	*.zip		export-ignore


This will prevent any files from being included if they:

* Beginning with `.`
* or are named `sources` or are inside any directory named `sources`.
* or have an extension of "zip".
