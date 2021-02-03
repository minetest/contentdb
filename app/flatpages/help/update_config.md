title: Git Update Detection

## Introduction

When you push a change to your Git repository, ContentDB can create a new release automatically or
send you a reminder. ContentDB will check your Git repository one per day, but you can use
webhooks or the API for faster updates.

Git Update Detection is clever enough to not create a release again if you've already created
it manually or using webhooks/the API.

## Setting up

* Set "VCS Repository URL" in your package.
* Open the "Configure Git Update Detection" page:
    * Go to the Create Release page and click "Set up" on the banner.
    * If the "How do you want to create releases?" wizard appears, choose "Automatic".
* Choose a trigger:
    * **New Commit** - this will trigger for each pushed commit on the default branch, or the branch you specify.
    * **New Tag** - this will trigger when a New Tag is created.
* Choose action to occur when the trigger happens:
    * **Notification** - All maintainers receive a notification under the Bot category, and the package
      will appear under "Outdated Packages" in [your to do list](/user/todo/).
    * **Create Release** - A new release is created.
      If New Commit, the title will be the iso date (eg: 2021-02-01).
      If New Tag, the title will the tag name.

## Marking a package as up-to-date

Git Update Detection shouldn't erroneously mark packages as outdated if it is configured currently,
so the first thing you should do is make sure the Update Settings are set correctly.

There are some situations where the settings are correct, but you want to mark a package as
up-to-date - for example, if you don't want to make a release for a particular tag.
Clicking "Save" on "Update Settings" will mark a package as up-to-date.

## Configuring Release Creation

See the [Package Configuration and Releases Guide](/help/package_config/) for
documentation on configuring the release creation.

From the Git repository, you can set the min/max Minetest versions, which files are included,
and update the package meta.
