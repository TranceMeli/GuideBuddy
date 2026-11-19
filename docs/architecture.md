# Architecture

```text
Browser  ->  Nuxt (port 3000)  ->  Django + DRF (port 8000)  ->  SQLite
             serves pages and      checks token, roles,
             forwards /api/...     rate limits
             and adds the token
             from the cookie
```

The browser only talks to Nuxt. The Nuxt server forwards `/api/...` requests to Django and attaches the access token from the HttpOnly cookie `gb_access` as `Authorization: Bearer`. Write requests from foreign origins are rejected (origin check plus `SameSite=Lax`).

## Authentication

- **Login** returns a short-lived access JWT (default 10 minutes) and a refresh JWT (default 14 days). The Nuxt server stores both in HttpOnly cookies (`gb_access`, `gb_refresh`, `SameSite=Lax`, `Secure` with https). The browser never sees the tokens, not even in a response body.
- **Silent renewal:** a Nuxt server middleware exchanges the refresh token for a new pair whenever the access cookie has expired. Parallel requests share one renewal.
- **Rotation:** every refresh issues a new refresh token and blocklists the old one (django-rest-framework-simplejwt blacklist).
- **Revocation:** logout blocklists the refresh token. A password change, password reset or ban invalidates all existing tokens at once (the access token carries a hash of the password, inactive accounts are rejected).
- **Public pages** stay readable even with an expired or revoked token; only write requests return 401.

The older Django-template frontend (HTMX) still runs on port 8000 and follows the same permission rules. It can be removed later.

## Content

A guide is an ordered list of typed elements (`GuideElement`, guide type `page`); a finished file or text is a guide of type `free`. One fixed template renders every guide, so authors never choose colours, fonts or layout. The elements and their fields are described in [guide-types.md](guide-types.md).

## Status and moderation

A guide has one of three statuses: `published`, `outdated` and `archived`. Drafts live in the author's browser until publishing. Archived guides leave the overview, search and sitemap, but their link keeps working and shows a note. A status change is recorded in the history with a reason but counts neither as a new version nor as a contribution, and it does not move the "updated" date. Everyone who may edit a guide can mark it outdated; the author and moderators archive and restore it. Open reports with the reason "outdated" are counted on the guide and shown to readers as a note.

A moderator can hide a comment with a reason. Readers then get an empty text and the reason, while moderators still see the text and who hid it. Who hid it, when and why stays on record in the comment history.
