title: Featured Packages

<p class="alert alert-warning">
	<b>Note:</b> This is a draft, and is likely to change
</p>

## What are Featured Packages?

Featured Packages are shown at the top of the ContentDB homepage. In the future,
featured packages may be shown inside the Minetest client.

The purpose is to promote content that demonstrates a high quality of what is
possible in Minetest. The selection should be varied, and should vary over time.
The featured content should be content that we are comfortable recommending to
a first time player.

## How are the packages chosen?

Before a package can be considered, it must fulfil the criteria in the below lists.
There are three types of criteria:

* "MUST": These must absolutely be fulfilled, no exceptions!
* "SHOULD": Most of them should be fulfilled, if possible. Some of them can be
  left out if there's a reason.
* "CAN": Can be fulfilled for bonus points, they are entirely optional.

For a chance to get featured, a package must fulfil all "MUST" criteria and
ideally as many "SHOULD" criteria as possible. The more, the better. Thankfully,
many criteria are trivial to fulfil. Note that ticking off all the boxes is not
enough: Just because a package completes the checklist does not make it good.
Other aspects of the package should be rated as well. See this list as a
starting point, not as an exhaustive quality control.

Editors are responsible for maintaining the list of featured packages. Authors
can request that their package be considered by opening a thread titled
"Feature Package" on their package. To speed things up, they should justify
why they meet (or don't meet) the below criteria. Editors must abstain from
voting on packages where they have a conflict of interest.

A package being featured does not mean that it will be featured forever. A
package may be unfeatured if it no longer meets the criteria, to make space for
other packages to be featured, or for another reason.

## General Requirements

### General

* MUST: Be 100% free and open source (as marked as Free on ContentDB).
* MUST: Work out-of-the-box (no weird setup or settings required).
* MUST: Be compatible with the latest stable Minetest release.
* SHOULD: Use public source control (such as Git).
* SHOULD: Have at least 3 reviews, and be largely positive.

### Stability

* MUST: Be well maintained (author is present and active).
* MUST: Be reasonably stable, with no game-breaking or major bugs.
* MUST: The author does not consider the package to be in an
  experimental/development/alpha state. Beta and "unfinished" packages are fine.
* MUST: No error messages from the engine (e.g. missing textures).
* SHOULD: No major map breakages (including unknown nodes, corruption, loss of inventories).
  Map breakages are a sign that the package isn't sufficiently stable.

Note: Any map breakage will be excused if "disaster relief" (i.e. tools to repair the damage)
is available.

### Meta and packaging

* MUST: `screenshot.png` is present and up-to-date, with a correct aspect ratio (3:2, at least 300x200).
* MUST: Have a high resolution cover image on ContentDB (at least 1280x768 pixels).
  It may be shown cropped to 16:9 aspect ratio, or shorter.
* MUST: mod.conf/game.conf/texture_pack.conf present with:
    * name (if mod or game)
    * description
    * dependencies (if relevant)
    * `min_minetest_version` and `max_minetest_version` (if relevant)
* MUST: Contain a README file and a LICENSE file. These may be `.md` or `.txt`.
    * README files typically contain helpful links (download, manual, bugtracker, etc), and other
      information that players or (potential) contributors may need.
* SHOULD: All important settings are in settingtypes.txt with description.

## Game-specific Requirements

### Meta and packaging

* MUST: Have a main menu icon and header image.

### Stability

* MUST: If any major setting (like `enable_damage`) is unsupported, the game must disable it
  using `disabled_settings` in the `game.conf`, and deal with it appropritely in the code
  (e.g. force-disable the setting, as the user may still set the setting in `minetest.conf`)

### Usability

* MUST: Unsupported mapgens are disabled in game.conf.
* SHOULD: Passes the Beginner Test: A newbie to the game (but not Minetest) wouldn't get completely
  stuck within the first 5 minutes of playing.
* SHOULD: Have good documentation. This may include one or more of:
    * A craftguide, or other in-game learning system
    * A manual
    * A wiki
    * Something else

### Gameplay

* CAN: Passes the Six Hour Test (only applies to sandbox games): The game doesn't run out of new
  content before the first 6 hours of playing.
* CAN: Players don't feel that something in the game is "lacking".

### Audiovisuals

* MUST: Audiovisual design should be of good quality.
* MUST: No obvious GUI/HUD breakages.
* MUST: Sounds have no obvious artifacts like clicks or unintentional noise.
* SHOULD: Graphical design is mostly consistent.
* SHOULD: Sounds are used.
* SHOULD: Sounds are normalized (more or less).

### Quality Assurance

* MUST: No flooding the console/log file with warnings.
* MUST: No duplicate crafting recipes.
* MUST: Highly experimental game features are disabled by default.
* MUST: Experimental game features are clearly marked as such.
* SHOULD: No unknown nodes/items/objects appear.
* SHOULD: No dependency on legacy API calls.
* SHOULD: No console warnings.

### Writing

* MUST: All items that can be obtained in normal gameplay have `description` set (whether in the definition or meta).
* MUST: Game is not littered with typos or bad grammar (a few typos are OK but should be fixed, when found).
* SHOULD: All items have unique names (items which disguise themselves as another item are exempt).
* SHOULD: The writing style of all item names is grammatical and consistent.
* SHOULD: Descriptions of things convey useful and meaningful information (if applicable).
* CAN: Text is written in clear and (if possible) simple language.
