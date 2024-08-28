# fastapi-aiograpi

A FastAPI wrapper for the aiograpi Instagram API client.

## Installation

[Add installation instructions here]

Usage:

[Add basic usage instructions here]

## Requests

* Login

```sh
curl -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/json" \
-d '{"username": "your_username", "password": "your_password"}'
```

* Logout

```sh
curl -X POST http://localhost:8000/auth/logout \
-H "Content-Type: application/json" \
-d '{"session_id": "your_session_id"}'
```

* Root

```sh
curl http://localhost:8000/
```

Replace 'localhost:8000' with your actual server address and port if different.
