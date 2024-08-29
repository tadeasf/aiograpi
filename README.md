# fastapi-aiograpi

A FastAPI wrapper for the aiograpi Instagram API client.

## Installation

[Add installation instructions here]

## Usage

[Add basic usage instructions here]

## Requests

* **Login**

This request will attempt to log in using the provided credentials. If successful, it will return a JSON response with a success message and a session ID.

```sh
curl -X POST "http://localhost:5569/auth/login/ahojkypet" \
-H "Content-Type: application/json" \
-d '{"password": "your_password"}'

```

* **Logout**

This request will log out the current user and clear the session.

```sh
curl -X POST "http://localhost:5569/auth/logout/{username}"
```

* **Get Profile Stats**

This request will return the number of posts, reels, and highlights for a given public Instagram profile.

```sh
curl http://localhost:5569/profile_stats/{username}
```

* **Get Highlight Media**

This request will return a list of highlight media URLs for a given public Instagram profile. You can use the `limit` query parameter to control the number of highlights returned (default is 5, maximum is 20).

```sh
    curl http://localhost:5569/profiles/{username}/highlight_media?limit=10
```

* **Sentry Debug** (for testing error reporting)

This request will trigger a deliberate error to test Sentry integration.

```sh
    curl http://localhost:5569/sentry-debug
```

* **Root**

This request will return a welcome message.

```sh
curl http://localhost:5569/
```

Note: The API now uses a proxy rotation system and session management. Each request will be routed through one of the configured proxy servers, and sessions will be managed automatically. There's no need to manually provide or manage session IDs in your requests.

Replace 'localhost:8000' with your actual server address and port if different.
