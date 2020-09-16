title: Content Flags

Content flags allow you to hide content based on your preferences.
The filtering is done server-side, which means that you don't need to update
your client to use new flags.

## Flags

Minetest allows you to specify a comma-separated list of flags to hide in the
client:

```
contentdb_flag_blacklist = nonfree, bad_language, drugs
```

A flag can be:

* `nonfree` - can be used to hide packages which do not qualify as
	'free software', as defined by the Free Software Foundation.
* A content warning, given below.
* `android_default` - meta-flag that filters out any content with a content warning.
* `desktop_default` - meta-flag that doesn't filter anything out for now.

## Content Warnings

Packages with mature content will be tagged with a content warning based
on the content type.

* `bad_language` - swearing.
* `drugs` - drugs or alcohol.
* `gambling`
* `gore` - blood, etc.
* `horror` - shocking and scary content.
* `violence` - non-cartoon violence.
