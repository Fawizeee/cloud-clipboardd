# Cloud Clipboard - API Documentation

This document lists the available API endpoints implemented in the Cloud Clipboard backend, their HTTP methods, exact paths, usage, request payloads, and expected response models.

All API routes (except basic health/root endpoints) are prefixed with `/api/v1`.

---

## 1. Root & Utility Endpoints

These are basic health-check and status endpoints mapped directly in `main.py`.

### Root Endpoint
- **Path**: `/`
- **Method**: `GET`
- **Use**: Verifies that the FastAPI server is running and accessible.
- **Response Example (200 OK)**:
  ```json
  {
    "message": "Hello World"
  }
  ```

### Health Check
- **Path**: `/health`
- **Method**: `GET`
- **Use**: Simple health probe for monitoring.
- **Response Example (200 OK)**:
  ```json
  {
    "status": "healthy"
  }
  ```

---

## 2. Authentication Endpoints

These endpoints manage user accounts and session generation. They are prefixed with `/api/v1/auth`.

> The JWT access token returned here must be sent as a **Bearer token** in the `Authorization` header for all protected endpoints.

### User Registration
- **Path**: `/api/v1/auth/register`
- **Method**: `POST`
- **Use**: Registers a new user, hashes the password using `bcrypt`, generates JWT access and refresh tokens (with the user's UUID stored in the `sub` claim), and provisions a verification code.
- **Request Body (JSON)**:
  ```json
  {
    "username": "johndoe",
    "email": "john.doe@example.com",
    "password": "strongpassword123",
    "confirm_password": "strongpassword123",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response Example (200 OK)**:
  ```json
  {
    "username": "john.doe@example.com",
    "email": "john.doe@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "needs_onboarding": true,
    "created_at": "2026-05-19T04:50:53.585003",
    "updated_at": "2026-05-19T04:50:54.312322"
  }
  ```

### User Login
- **Path**: `/api/v1/auth/login`
- **Method**: `POST`
- **Use**: Logs in an existing user by verifying credentials against the stored hash and returns a fresh JWT access and refresh token pair. The user's UUID is stored in the token `sub` claim.
- **Request Body (JSON)**:
  ```json
  {
    "email": "john.doe@example.com",
    "password": "strongpassword123"
  }
  ```
- **Response Example (200 OK)**:
  ```json
  {
    "username": "john.doe@example.com",
    "email": "john.doe@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "needs_onboarding": true,
    "created_at": "2026-05-19T04:50:53.585003",
    "updated_at": "2026-05-19T04:50:54.312322"
  }
  ```

---

## 3. Clipboard Endpoints 🔒

These endpoints are **protected** and require a valid JWT access token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

The server extracts the user's identity exclusively from the token — `user_id` is **never** required in the request body or query parameters, and is **never** exposed in responses.

Mapped in `api/v1/clipboard/routes.py` with the `/clipboard` router prefix.

### Save Clipboard Item
- **Path**: `/api/v1/clipboard/personal`
- **Method**: `POST`
- **Auth**: Required — Bearer token
- **Use**: Saves a new clipboard text, image, URL, or file metadata entry linked to the authenticated user.
- **Request Headers**:
  ```
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
- **Request Body (JSON)**:
  ```json
  {
    "content": "This is text saved to the cloud clipboard!",
    "content_type": "text",
    "expires_at": null,
    "is_private": false,
    "source_device_id": null
  }
  ```
  *(Note: `content_type` must be one of: `text`, `image`, `file`, `url`)*
- **Response Example (200 OK)**:
  ```json
  {
    "content": "This is text saved to the cloud clipboard!",
    "created_at": "2026-05-19T04:50:55.798256",
    "updated_at": "2026-05-19T04:50:55.798265"
  }
  ```
- **Error Responses**:
  - `401 Unauthorized` — Missing or invalid Bearer token
  - `403 Forbidden` — Account is inactive

### Get Clipboard Items
- **Path**: `/api/v1/clipboard/personal`
- **Method**: `GET`
- **Auth**: Required — Bearer token
- **Use**: Retrieves all saved clipboard items belonging to the authenticated user.
- **Request Headers**:
  ```
  Authorization: Bearer <access_token>
  ```
- **Query Parameters**: None required.
- **Response Example (200 OK)**:
  ```json
  [
    {
      "content": "This is text saved to the cloud clipboard!",
      "created_at": "2026-05-19T04:50:55.798256",
      "updated_at": "2026-05-19T04:50:55.798265"
    }
  ]
  ```
- **Error Responses**:
  - `401 Unauthorized` — Missing or invalid Bearer token
  - `403 Forbidden` — Account is inactive
