title: Frequently Asked Questions

## Users and Logins

### How do I create an account?

How you create an account depends on whether you have a forum account.

If you have a forum account, then you'll need to prove that you are the owner of the account. This can
be done using a GitHub account or a random string in your forum account signature.

If you don't, then you can just sign up using an email address and password.

GitHub can only be used to login, not to register.

<a class="btn btn-primary" href="/user/claim/">Register</a>


### My verification email never arrived

There are a number of reasons this may have happened:

* Incorrect email address entered.
* Temporary problem with ContentDB. 
* Email has been unsubscribed.

If the email doesn't arrive after registering by email, then you'll need to try registering again in 12 hours.
Unconfirmed accounts are deleted every 12 hours.

If the email verification was sent using the Email settings tab, then you can just set a new email.

If you have previously unsubscribed this email, then ContentDB is completely prevented from sending emails to that
address. You'll need to use a different email address, or [contact an admin](https://rubenwardy.com/contact/) to
remove your email from the blacklist.


## Packages

### How can I create releases automatically?

There are a number of methods:

* [Git Update Detection](update_config): ContentDB will check your Git repo daily, and create updates or send you notifications.
* [Webhooks](release_webhooks): you can configure your Git host to send a webhook to ContentDB, and create an update immediately.
* the [API](api): This is especially powerful when combined with CI/CD and other API endpoints. 


## How do I get help?

Please [contact rubenwardy](https://rubenwardy.com/contact/).