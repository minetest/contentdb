title: Creating Releases using Webhooks

## What does this mean?

A webhook is a notification from one service to another. Put simply, a webhook
is used to notify ContentDB that the git repository has changed.

ContentDB offers the ability to automatically create releases using webhooks
from either Github or Gitlab. If you're not using either of those services,
you can also use the [API](../api) to create releases.

The process is as follows:

1. The user creates an API Token and a webhook to use it.
2. The user pushes a commit to the git host (Gitlab or Github).
3. The git host posts a webhook notification to ContentDB, using the API token assigned to it.
4. ContentDB checks the API token and issues a new release.

## Setting up

### GitHub

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

### GitLab

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

See the [Package Configuration and Releases Guide](/help/package_config/) for
documentation on configuring the release creation.
You can set the min/max Minetest version from the Git repository, and also
configure what files are included.
