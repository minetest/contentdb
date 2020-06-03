title: Creating Releases using Webhooks

## What does this mean?

A webhook is a notification from one service to another. Put simply, a webhook
is used to notify ContentDB that the git repository has changed.

ContentDB offers the ability to automatically create releases using webhooks
from either Github or Gitlab. If you're not using either of those services,
you can also use the [API](../api) to create releases.

The process is as follows:

1. The user creates an API Token and a webhook to use it. This can be done automatically
   for Github.
2. The user pushes a commit to the git host (Gitlab or Github).
3. The git host posts a webhook notification to ContentDB, using the API token assigned to it.
4. ContentDB checks the API token and issues a new release.

## Setting up

### GitHub (automatic)

1. Go to your package's page.
2. Make sure that the repository URL is set to a Github repository.
   Only github.com is supported.
3. Go to "Releases" > "+", and click "Setup webhook" at the top of the create release
   page.
   If you do not see this, either the repository isn't using Github or you do
   not have permission to use webhook releases (ie: you're not a Trusted Member).
4. Grant ContentDB the ability to manage Webhooks.
5. Set the event to either "New tag or Github Release" (highly recommended) or "Push".

   N.B.: GitHub uses tags to power GitHub Releases, meaning that creating a webhook
   on "New tag" will sync GitHub and ContentDB releases.

### GitHub (manual)

1. Create a ContentDB API Token at [Profile > API Tokens: Manage](/user/tokens/).
2. Copy the access token that was generated.
3. Go to the GitLab repository's settings > Webhooks > Add Webhook.
4. Set the payload URL to `https://content.minetest.net/github/webhook/`
5. Set the content type to JSON.
6. Set the secret to the access token that you copied.
7. Set the events
  * If you want a rolling release, choose "just the push event".
  * Or if you want a stable release cycle based on tags,
    choose "Let me select" > Branch or tag creation.
8. Create.

### GitLab (manual)

1. Create a ContentDB API Token at [Profile > API Tokens: Manage](/user/tokens/).
2. Copy the access token that was generated.
3. Go to the GitLab repository's settings > Webhooks.
4. Set the URL to `https://content.minetest.net/gitlab/webhook/`
6. Set the secret token to the ContentDB access token that you copied.
7. Set the events
    * If you want a rolling release, choose "Push events".
    * Or if you want a stable release cycle based on tags,
      choose "Tag push events".
8. Add webhook.

## Configuring

### Setting minimum and maximum Minetest versions

1. Open up the conf file for the package.
   This will be `game.conf`, `mod.conf`, `modpack.conf`, or `texture_pack.conf`
   depending on the content type.
2. Set `min_minetest_version` and `max_minetest_version` to the respective Minetest versions.

     Eg:

         min_minetest_version = 5.0
