# fastapi-aiograpi

A FastAPI wrapper for the aiograpi Instagram API client.

## Installation

[Add installation instructions here]

Usage:

[Add basic usage instructions here]

## Requests

* Login

This request will attempt to log in using the provided credentials. If successful, it will return a JSON response with a success message and a session ID.

```sh
curl -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/json" \
-d '{"username": "ahojkypet", "password": "password"}'
```

* Logout

This request will log out the current user and clear the session.

```sh
curl -X POST http://localhost:8000/auth/logout
```

* Sentry Debug (for testing error reporting)

This request will trigger a deliberate error to test Sentry integration.

```sh
curl http://localhost:8000/sentry-debug
```

* Root

This request will return a welcome message.

```sh
curl http://localhost:8000/
```

Note: The API now uses a proxy rotation system and session management. Each request will be routed through one of the configured proxy servers, and sessions will be managed automatically. There's no need to manually provide or manage session IDs in your requests.

Replace 'localhost:8000' with your actual server address and port if different.
