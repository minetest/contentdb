title: Feeds

You can follow updates from ContentDB in your RSS feed reader. If in doubt, copy the Atom URL.

* All events: [Atom]({{ url_for('feeds.all_atom') }}) | [JSONFeed]({{ url_for('feeds.all_json') }})
* New packages: [Atom]({{ url_for('feeds.packages_all_atom') }}) | [JSONFeed]({{ url_for('feeds.packages_all_json') }})
* New releases: [Atom]({{ url_for('feeds.releases_all_atom') }}) | [JSONFeed]({{ url_for('feeds.releases_all_json') }})

## Package feeds

Follow new releases for a package:

```
https://content.minetest.net/packages/AUTHOR/NAME/releases_feed.atom
https://content.minetest.net/packages/AUTHOR/NAME/releases_feed.json
```
