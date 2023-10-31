title: OAuth2 API

<p class="alert alert-warning">
    The OAuth2 applications API is currently experimental and invite only.
</p>

ContentDB allows you to create an OAuth2 Application and obtain access tokens
for users.


## Create an OAuth2 Client

Go to Settings > [OAuth2 Applications](/user/apps/) > Create

Note: If you don't see this then you don't have access to OAuth2 yet.


## Obtaining access tokens

ContentDB supports the Authorization Code OAuth2 method.

### Authorize

Get the user to open the following URL in a web browser:

```
https://content.minetest.net/oauth/authorize/
    ?response_type=code
    &client_id={CLIENT_ID}
    &redirect_uri={REDIRECT_URL}
```

The redirect_url must much the value set in your oauth client. Make sure to URL encode it.
ContentDB also supports `state`.

Afterwards, the user will be redirected to your callback URL.
If the user accepts the authorization, you'll receive an authorization code (`code`).
Otherwise, the redirect_url will not be modified.

For example, with `REDIRECT_URL` set as `https://example.com/callback/`:

* If the user accepts: `https://example.com/callback/?code=abcdef`
* If the user cancels: `https://example.com/callback/`

### Exchange auth code for access token

Next, you'll need to exchange the auth for an access token.

Do this by making a POST request to the `/oauth/token/` API:

```bash
curl -X POST https://content.minetest.net/oauth/token/ \
    -F grant_type=authorization_code
    -F client_id="CLIENT_ID" \
    -F client_secret="CLIENT_SECRET" \
    -F code="abcdef" 
```

<p class="alert alert-warning">
    <i class="fas fa-exclamation-circle me-2"></i>
    You should make this request on a server to prevent the user
    from getting access to your client secret.
</p>

If successful, you'll receive:

```json
{
    "access_token": "access_token",
    "token_type": "Bearer"
}
```

If there's an error, you'll receive a standard API error message:

```json
{
    "success": false,
    "error": "The error message"
}
```

Possible errors:

* Unsupported grant_type, only authorization_code is supported
* Missing client_id
* Missing client_secret
* Missing code
* client_id and/or client_secret is incorrect
* Incorrect code. It may have already been redeemed
