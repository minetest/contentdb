title: Creating Releases using Webhooks

## What does this mean?

ContentDB offers the ability to automatically create releases using webhooks
from either Github or Gitlab. If you're not using either of those services,
you can also use the [API](../api) to create releases.

The process is as follows:

1. The user creates an API Token and a webhook to use it. This can be done automatically
   for Github.
2. The user pushes a commit to the git host (Gitlab or Github).
3. The git host posts a webhook notification to ContentDB, using the API token assigned to it.
4. ContentDB checks the API token and issues a new releases.

<p class="alert alert-info">
	This feature is in beta, and is only available for Trusted Members.
</p>

## Setting up

### Github (automatic)

1. Go to your package page.
2. Make sure that the repository URL is set to a Github repository.
   Only github.com is supported.
3. Click "Set up a webhook to create releases automatically" below the releases
   panel on the side bar.
4. Grant ContentDB the ability to manage Webhooks

### GitHub (manual)

1. Create an API Token by visiting your profile and clicking "API Tokens: Manage".
2. Copy the access token that was generated.
3. Go to the repository's settings > Webhooks > Add Webhook.
4. Set the payload URL to `https://content.minetest.net/github/webhook/`
5. Set the content type to JSON.
6. Set the secret to the access token that you copied.
7. Set the events
  * If you want a rolling release, choose "just the push event".
  * Or if you want a stable release cycle based on tags,
   choose "Let me select" > Branch or tag creation.

### GitLab (manual)

1. Create an API Token by visiting your profile and clicking "API Tokens: Manage".
2. Copy the access token that was generated.
3. Go to the repository's settings > Integrations.
4. Set the URL to `https://content.minetest.net/gitlab/webhook/`
6. Set the secret token to the access token that you copied.
7. Set the events
    * If you want a rolling release, choose "Push events".
    * Or if you want a stable release cycle based on tags,
      choose "Tag push events".

## Configuring

### Setting minimum and maximum Minetest versions

<p class="alert alert-info">
	This feature is unimplemented.
</p>

1. Open up the conf file for the package.
   This will be `game.conf`, `mod.conf`, `modpack.conf`, or `texture_pack.conf`
   depending on the content type.
2. Set `min_protocol` and `max_protocol` to the respective protocol numbers
   of the Minetest versions.
     * 0.4 = 32
     * 5.0 = 37
     * 5.1 = 38
