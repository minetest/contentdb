title: Editors

## What should editors do?

Editors are users of rank Editor or above.
They are responsible for ensuring that the package listings of ContentDB are useful.
For this purpose, they can/will:

* Review and approve packages.
* Edit any package - including tags, releases, screenshots, and maintainers.
* Create packages on behalf of authors who aren't present.

Editors should make sure they are familiar with the
[Package Inclusion Policy and Guidance](/policy_and_guidance/).

## ContentDB is not a curated platform

It's important to note that ContentDB isn't a curated platform, but it also does have some
requirements on minimum usefulness. See 2.2 in the [Policy and Guidance](/policy_and_guidance/).

## Editor Work Queue

The [Editor Work Queue](/todo/) and related pages contain useful information for editors, such as:

* The package, release, and screenshot approval queues.
* Packages which are outdated or are missing tags.
* A list of forum topics without packages.
  Editors can create the packages or "discard" them if they don't think it's worth adding them.

## Editor Notifications

Editors currently receive notifications for any new thread opened on a package, so that they
know when a user is asking for help. These notifications are shown separately in the notifications
interface, and can be configured separately in Emails and Notifications.

## Crash Course to being an Editor

* [Policy and Guidance](/policy_and_guidance/) is our goto resource for making decisions in 
  changes needed like lua_api.txt is the doc for modders to consult
* In the Editor console, the two most important tabs are the Editor Work Queue and the Forum 
  Topics tab. On the Forums Topics tab when you have some free time, feel free to scroll 
  through and import old mods in contentdb. Primarily you will be focusing on the Editor 
  Work Queue tab, where a list of packages to review is. if the queue is empty, and there 
  still is a counter, look under releases to see if something needs approval, or if images 
  are present
* A simplied process from reviewing a package is as follows:
  1. scan the package image if present for any obvious closed source assets.
  2. if right to a name warning is present, check its validity and if the package meets 
     the exceptions.
  3. if the forums topic missing warning is present, feel free to check it, but its 
     usually incorrect.
  4. check source, etc links to make sure they work and are correct.
  5. verify that the package has license file that matches what is on the contentdb fields
  6. verify that all assets and code are licensed correctly
  7. if the above steps pass, approve the package, else request changes needed from the author
