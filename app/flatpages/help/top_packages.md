title: Top Packages Algorithm

## Pseudo rolling average

Every package loses 5% of its score every day.

An open source package will gain 1 score for each unique download,
whereas a non-free package will only gain 0.1 score.

A package currently only gains score through downloads.
In the future, a package will also gain score through reviews.

## Seed using a legacy heuristic

The scoring system was seeded (ie: the scores were initially set to) 20% of an
arbitrary legacy heuristic that was previously used to rank packages.

This legacy heuristic is as follows:

	forum_score = views / max(years_since_creation, 2 weeks) + 80*clamp(months, 0.5, 6)
	forum_bonus = views + posts

	multiplier = 1
	if no screenshot:
		multiplier *= 0.8
	if not foss:
		multiplier *= 0.1

	score = multiplier * (max(downloads, forum_score * 0.6) + forum_bonus)

As said, this legacy score is no longer used when ranking mods.
It was only used to provide an initial score for the rolling average,
which was 20% of the above value.

## Transparency and Feedback

You can see all scores using the [scores REST API](/api/scores/).

Consider [suggesting improvements](https://github.com/minetest/contentdb/issues/new?assignees=&labels=Policy&template=policy.md&title=).
