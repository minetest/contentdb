title: Automatic Update Detection

## Introduction

When you push a change to your Git repository, ContentDB can create a new release automatically or
send you a reminder. ContentDB will check your Git repository every day, but you can use
webhooks or the API for faster updates.

## Setting up

* Set "VCS Repository URL" in your package.
* Go to the Create Release page and click "Set up" on the banner.
* If the "How do you want to create releases?" wizard appears, choose "Automatic".
* Choose a trigger:
    * New Commit - this will trigger for each pushed commit on the default branch, or the branch you specify.
    * New Tag - this will trigger when a New Tag is created.
* Choose action to occur when the trigger happens:
    * Create Release - A new release is created.
    * Notification - All maintainers receive a notification under the Bot category, and the package
      will appear under "Outdated Packages" in [your to do list](/user/todo/).

## Configuring

See the [Package Configuration and Releases Guide](/help/package_config/) for
documentation on configuring the release creation.
You can set the min/max Minetest version from the Git repository, and also
configure what files are included.
