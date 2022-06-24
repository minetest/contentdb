title: Supported Games

<p class="alert alert-warning">
    This feature is experimental
</p>

## Why?

The supported/compatible games feature allows mods to specify the games that they work with, which improves
user experience.


## Support sources

### mod.conf

You can use `supported_games` to specify games that your mod is compatible with.

You can use `unsupported_games` to specify games that your mod doesn't work with, which is useful for overriding
ContentDB's automatic detection.

Both of these are comma-separated lists of game technical ids. Any `_game` suffixes are ignored, just like in Minetest.

    supported_games = minetest_game, repixture
    unsupported_games = lordofthetest, nodecore, whynot

### Dependencies

ContentDB will analyse hard dependencies and work out which games a mod supports.

This uses a recursive algorithm that works out whether a dependency can be installed independently, or if it requires
a certain game.


## Combining all the sources

mod.conf will override anything ContentDB detects.
