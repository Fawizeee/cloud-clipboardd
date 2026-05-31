# Cloud Clipboard — Complete API Documentation

> **Base URL**: `http://localhost:8000`  
> **API Prefix**: All feature routes are prefixed with `/api/v1`  
> **Auth**: Protected routes require a JWT access token in the `Authorization` header:
> ```
> Authorization: Bearer <access_token>
> ```
> The server extracts the caller's identity **exclusively from the token** — `user_id` is never required in the request body and never exposed in responses.

---

## Table of Contents

1. [Utility Endpoints](#1-utility-endpoints)
2. [Authentication](#2-authentication-endpoints)
   - [Register](#21-register-user)
   - [Login](#22-login)
   - [Refresh Token](#23-refresh-access-token)
   - [Verify Email](#24-verify-email)
   - [Resend Verification](#25-resend-verification-code)
   - [Request Password Reset](#26-request-password-reset)
   - [Confirm Password Reset](#27-confirm-password-reset)
3. [Personal Clipboard](#3-personal-clipboard-endpoints-)
   - [Create Item](#31-create-clipboard-item)
   - [List Items](#32-list-clipboard-items)
   - [Search Items](#33-search-clipboard-items)
   - [Get Single Item](#34-get-single-clipboard-item)
   - [Update Item](#35-update-clipboard-item)
   - [Delete Item](#36-delete-clipboard-item)
   - [Upload File](#37-upload-file)
4. [Team Clipboard](#4-team-clipboard-endpoints-)
   - [Get Team Items](#41-get-team-clipboard-items)
   - [Share Item](#42-share-clipboard-item)
5. [Sync](#5-sync-endpoints-)
   - [Sync Status](#51-get-sync-status)
   - [Trigger Sync](#52-trigger-sync)
6. [Device Management](#6-device-management-endpoints-)
   - [Register Device](#61-register-device)
   - [List Devices](#62-list-devices)
   - [Remove Device](#63-remove-device)
7. [WebSocket](#7-websocket-)

---

## 1. Utility Endpoints

Mapped directly in `main.py`. No authentication required.

---

### `GET /`

Returns basic server information.

**Response `200 OK`**
```json
{
  "app": "Cloud Clipboard API",
  "version": "1.0.0",
  "env": "development",
  "docs": "/docs"
}
```

---

### `GET /health`

Detailed health check that verifies database connectivity.

**Response `200 OK` — all services healthy**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy"
  },
  "version": "1.0.0",
  "env": "development"
}
```

**Response `200 OK` — degraded**
```json
{
  "status": "degraded",
  "services": {
    "database": "unhealthy: could not connect to server"
  },
  "version": "1.0.0",
  "env": "development"
}
```

---

## 2. Authentication Endpoints

All auth routes are prefixed with `/api/v1/auth`. No bearer token required unless noted.

> **Account activation flow**: After registering, an account is **inactive** until verified.
> Call [Verify Email](#24-verify-email) with the `verification_code` returned at registration before logging in.

---

### 2.1 Register User

**`POST /api/v1/auth/register`**

Creates a new user account, hashes the password with `bcrypt`, generates JWT tokens, and produces a 6-digit email verification code.

**Request Body**
```json
{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password": "StrongPass123!",
  "confirm_password": "StrongPass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | ✅ | Display username |
| `email` | string (email) | ✅ | Must be a valid email address |
| `password` | string | ✅ | Plain text — hashed server-side |
| `confirm_password` | string | ✅ | Must match `password` |
| `first_name` | string | ✅ | |
| `last_name` | string | ✅ | |

**Response `200 OK`**
```json
{
  "id": "a3f1c2d4-1234-5678-abcd-ef0123456789",
  "username": "john.doe@example.com",
  "email": "john.doe@example.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "needs_onboarding": true,
  "created_at": "2026-05-31T12:00:00.000000",
  "updated_at": "2026-05-31T12:00:01.000000"
}
```

> ⚠️ **The `verification_code` is only available in the DB row (`verification_token` column).** In production this would be emailed. For development, read it directly from the database or the `/resend-verify` response.

**Error Responses**

| Status | Detail |
|---|---|
| `400` | `"User already exists"` |
| `422` | Validation error (e.g. passwords don't match, invalid email) |

---

### 2.2 Login

**`POST /api/v1/auth/login`**

Authenticates an existing, verified user and returns a fresh token pair.

**Request Body**
```json
{
  "email": "john.doe@example.com",
  "password": "StrongPass123!",
  "device_info": {
    "device_name": "Pixel 8 Pro",
    "platform": "android",
    "version": "1.0.0"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | ✅ | |
| `password` | string | ✅ | |
| `device_info` | object | ❌ | Optional device context |

**Response `200 OK`**
```json
{
  "id": "a3f1c2d4-1234-5678-abcd-ef0123456789",
  "username": "john.doe@example.com",
  "email": "john.doe@example.com",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "needs_onboarding": false,
  "created_at": "2026-05-31T12:00:00.000000",
  "updated_at": "2026-05-31T12:05:00.000000"
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"User not found"` |
| `401` | `"Invalid password"` |
| `403` | `"Account is inactive"` or `"Please verify your email before logging in"` |

---

### 2.3 Refresh Access Token

**`POST /api/v1/auth/refresh`**

Exchange a valid refresh token for a new short-lived access token. Use this when the access token expires without prompting the user to log in again.

**Request Body**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response `200 OK`**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

> `expires_in` is in **seconds** (default: 30 minutes = 1800).

**Error Responses**

| Status | Detail |
|---|---|
| `401` | `"Invalid or expired refresh token"` |
| `401` | `"Token type mismatch. Expected a refresh token."` |

---

### 2.4 Verify Email

**`POST /api/v1/auth/verify`**

Confirm the user's email address using the 6-digit code generated at registration. On success, sets `is_verified = true` and `is_active = true`, allowing login.

**Request Body**
```json
{
  "email": "john.doe@example.com",
  "code": "482916"
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Email verified successfully. You can now log in."
}
```

**Response `200 OK`** (already verified)
```json
{
  "success": true,
  "message": "Email already verified. You can log in."
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"User not found"` |
| `400` | `"Invalid verification code."` |

---

### 2.5 Resend Verification Code

**`POST /api/v1/auth/resend-verify`**

Generate and return a new 6-digit verification code. In production this would be emailed; here it is returned directly.

**Request Body**
```json
{
  "email": "john.doe@example.com"
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "New verification code generated.",
  "verification_code": "739201"
}
```

> Always returns `200` even for unknown emails to prevent user enumeration.

---

### 2.6 Request Password Reset

**`POST /api/v1/auth/password-reset/request`**

Generate a secure URL-safe reset token for the given email. In production this is emailed; in development it is returned directly.

**Request Body**
```json
{
  "email": "john.doe@example.com"
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Password reset token generated.",
  "reset_token": "Xk2mN8pQrT..."
}
```

> Always returns `200` even for unknown emails to prevent user enumeration.

---

### 2.7 Confirm Password Reset

**`POST /api/v1/auth/password-reset/confirm`**

Validate the reset token and set a new password. The token is invalidated after use.

**Request Body**
```json
{
  "token": "Xk2mN8pQrT...",
  "new_password": "NewSecurePass456!",
  "confirm_password": "NewSecurePass456!"
}
```

**Response `200 OK`**
```json
{
  "success": true,
  "message": "Password has been reset successfully. Please log in."
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `400` | `"Invalid or expired reset token."` |
| `422` | Passwords do not match |

---

## 3. Personal Clipboard Endpoints 🔒

All routes require `Authorization: Bearer <access_token>`.  
Mapped in `api/v1/clipboard/routes.py` with prefix `/api/v1/clipboard`.

> `content_type` must be one of: `text` · `image` · `file` · `url` · `code` · `email`

---

### 3.1 Create Clipboard Item

**`POST /api/v1/clipboard/personal`**

Save a new clipboard item. The server auto-computes `content_hash` (SHA-256 for deduplication), `content_preview` (first 200 chars), and `content_size`.

**Request Body**
```json
{
  "content": "Meeting notes: discuss Q3 roadmap and OKRs.",
  "content_type": "text",
  "expires_at": null,
  "is_private": false,
  "source_device_id": "b2a3c4d5-0001-0002-0003-000400050006",
  "source_device_name": "Pixel 8 Pro",
  "folder_id": null,
  "metadata": {
    "source_app": "Google Docs",
    "format": "plain_text"
  }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `content` | string | ✅ | The clipboard text/data |
| `content_type` | string | ✅ | `text` \| `image` \| `file` \| `url` \| `code` \| `email` |
| `expires_at` | datetime \| null | ❌ | ISO 8601 expiry timestamp |
| `is_private` | boolean | ❌ | Default `false` |
| `source_device_id` | UUID string \| null | ❌ | |
| `source_device_name` | string \| null | ❌ | Human-readable device label |
| `folder_id` | UUID string \| null | ❌ | Folder to place item in |
| `metadata` | object \| null | ❌ | Arbitrary key-value metadata |

**Response `201 Created`**
```json
{
  "id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
  "content": "Meeting notes: discuss Q3 roadmap and OKRs.",
  "content_type": "text",
  "content_size": 44,
  "sync_status": "pending",
  "created_at": "2026-05-31T12:10:00.000000",
  "updated_at": "2026-05-31T12:10:00.000000"
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `401` | Invalid or missing token |
| `403` | Account inactive |
| `422` | Invalid `content_type` |

---

### 3.2 List Clipboard Items

**`GET /api/v1/clipboard/personal`**

Retrieve the authenticated user's personal clipboard items with pagination, optional type filter, and sort order.

**Query Parameters**

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | Page number (1-indexed) |
| `limit` | integer | `20` | Items per page (max `100`) |
| `sort_order` | string | `desc` | `asc` or `desc` by `created_at` |
| `content_type` | string | — | Filter by type (optional) |
| `folder_id` | UUID string | — | Filter by folder (optional) |

**Example Request**
```
GET /api/v1/clipboard/personal?page=1&limit=5&sort_order=desc&content_type=url
Authorization: Bearer <token>
```

**Response `200 OK`**
```json
{
  "items": [
    {
      "id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
      "content": "https://openai.com/research",
      "content_type": "url",
      "content_preview": "https://openai.com/research",
      "content_size": 27,
      "source_device_name": "Pixel 8 Pro",
      "source_device_id": "b2a3c4d5-0001-0002-0003-000400050006",
      "folder_id": null,
      "is_favorite": false,
      "is_pinned": false,
      "is_private": false,
      "access_count": 3,
      "shared_by": null,
      "created_at": "2026-05-31T11:00:00.000000",
      "updated_at": "2026-05-31T11:00:00.000000",
      "expires_at": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 5,
    "total": 42,
    "total_pages": 9
  }
}
```

---

### 3.3 Search Clipboard Items

**`GET /api/v1/clipboard/personal/search`**

Full-text search across the authenticated user's clipboard content using a case-insensitive `ILIKE` query.

**Query Parameters**

| Param | Type | Required | Notes |
|---|---|---|---|
| `q` | string | ✅ | Search string (min 1 character) |
| `page` | integer | ❌ | Default `1` |
| `limit` | integer | ❌ | Default `20`, max `100` |

**Example Request**
```
GET /api/v1/clipboard/personal/search?q=meeting&page=1&limit=10
Authorization: Bearer <token>
```

**Response `200 OK`** — same shape as [List Items](#32-list-clipboard-items)

---

### 3.4 Get Single Clipboard Item

**`GET /api/v1/clipboard/personal/{item_id}`**

Retrieve one clipboard item by its UUID. Increments `access_count` and updates `last_accessed`.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `item_id` | UUID string | The item's `id` |

**Response `200 OK`**
```json
{
  "id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
  "content": "Meeting notes: discuss Q3 roadmap and OKRs.",
  "content_type": "text",
  "content_preview": "Meeting notes: discuss Q3 roadmap and OKRs.",
  "content_size": 44,
  "source_device_name": "Pixel 8 Pro",
  "source_device_id": "b2a3c4d5-0001-0002-0003-000400050006",
  "folder_id": null,
  "is_favorite": true,
  "is_pinned": false,
  "is_private": false,
  "access_count": 4,
  "shared_by": null,
  "created_at": "2026-05-31T12:10:00.000000",
  "updated_at": "2026-05-31T12:10:00.000000",
  "expires_at": null
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"Clipboard item not found"` |

---

### 3.5 Update Clipboard Item

**`PATCH /api/v1/clipboard/personal/{item_id}`**

Partially update a clipboard item. Only supply the fields you want to change. If `content` is updated, `content_hash`, `content_preview`, and `content_size` are automatically recomputed.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `item_id` | UUID string | The item's `id` |

**Request Body** (all fields optional)
```json
{
  "content": "Updated meeting notes — Q3 planning confirmed.",
  "is_favorite": true,
  "is_pinned": false,
  "folder_id": "f0e1d2c3-1111-2222-3333-444455556666"
}
```

| Field | Type | Notes |
|---|---|---|
| `content` | string \| null | New content; triggers hash/preview recompute |
| `is_favorite` | boolean \| null | Toggle favourite |
| `is_pinned` | boolean \| null | Toggle pin |
| `folder_id` | UUID string \| null | Move to folder |

**Response `200 OK`** — full `ClipboardItemResponse` (same shape as [Get Single Item](#34-get-single-clipboard-item))

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"Clipboard item not found"` |

---

### 3.6 Delete Clipboard Item

**`DELETE /api/v1/clipboard/personal/{item_id}`**

Soft-delete a clipboard item. Sets `is_deleted = true` and records `deleted_at`. The item no longer appears in list or search results.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `item_id` | UUID string | The item's `id` |

**Response `200 OK`**
```json
{
  "message": "Clipboard item deleted successfully"
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"Clipboard item not found"` |

---

### 3.7 Upload File

**`POST /api/v1/clipboard/files`**

Upload a file as a clipboard item using `multipart/form-data`.

> ⚠️ **File storage (S3/MinIO) is not configured in this environment.** The endpoint accepts and reads the file, but returns a stub URL. Wire in your storage provider in `api/v1/clipboard/routes.py` when ready.

**Request** — `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `file` | binary | The file to upload |

**Response `201 Created`**
```json
{
  "id": "e5f6a7b8-cccc-dddd-eeee-ffff00001111",
  "file_url": "https://storage.example.com/files/e5f6a7b8-cccc-dddd-eeee-ffff00001111/screenshot.png",
  "content_type": "image/png",
  "filename": "screenshot.png",
  "file_size": 204800,
  "created_at": "2026-05-31T12:15:00.000000"
}
```

---

## 4. Team Clipboard Endpoints 🔒

Items you have shared with others, or that others have shared with you.

---

### 4.1 Get Team Clipboard Items

**`GET /api/v1/clipboard/team`**

Retrieve clipboard items that **other users have shared with you**. Each item includes a `shared_by` field showing the sharer's full name.

**Query Parameters**

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | |
| `limit` | integer | `20` | Max `100` |

**Response `200 OK`**
```json
{
  "items": [
    {
      "id": "d4e5f6a7-1234-5678-9abc-def012345678",
      "content": "API key for staging: sk-staging-abc123",
      "content_type": "text",
      "content_preview": "API key for staging: sk-staging-abc123",
      "content_size": 38,
      "source_device_name": "MacBook Pro",
      "source_device_id": null,
      "folder_id": null,
      "is_favorite": false,
      "is_pinned": false,
      "is_private": false,
      "access_count": 0,
      "shared_by": "Alice Smith",
      "created_at": "2026-05-31T10:00:00.000000",
      "updated_at": "2026-05-31T10:00:00.000000",
      "expires_at": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "total_pages": 1
  }
}
```

---

### 4.2 Share Clipboard Item

**`POST /api/v1/clipboard/team/share`**

Share one of your personal clipboard items with another user by their email address. The recipient will see it in their team clipboard.

**Request Body**
```json
{
  "clipboard_item_id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
  "share_with_email": "alice@example.com",
  "permission": "read"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `clipboard_item_id` | UUID string | ✅ | Must belong to the caller |
| `share_with_email` | string | ✅ | Recipient's email address |
| `permission` | string | ❌ | `"read"` (default) or `"write"` |

**Response `200 OK`**
```json
{
  "message": "Item shared with alice@example.com successfully"
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"Clipboard item not found"` |
| `404` | `"Recipient user not found"` |
| `400` | `"Cannot share with yourself"` |
| `409` | `"Item already shared with this user"` |

---

## 5. Sync Endpoints 🔒

REST-based device synchronisation. For real-time sync use the [WebSocket endpoint](#7-websocket-).

---

### 5.1 Get Sync Status

**`GET /api/v1/sync/status`**

Returns the current sync state for the authenticated user: last successful sync timestamp, count of pending events, and a list of all registered devices with their online/offline status.

> A device is considered **online** if its `last_seen` timestamp is within the last **5 minutes**.

**Response `200 OK`**
```json
{
  "last_sync": "2026-05-31T11:55:00.000000",
  "pending_items": 2,
  "conflict_items": 0,
  "devices": [
    {
      "id": "b2a3c4d5-0001-0002-0003-000400050006",
      "name": "Pixel 8 Pro",
      "last_seen": "2026-05-31T12:30:00.000000",
      "status": "online"
    },
    {
      "id": "c3b4a5d6-0002-0003-0004-000500060007",
      "name": "MacBook Pro 16\"",
      "last_seen": "2026-05-30T18:00:00.000000",
      "status": "offline"
    }
  ]
}
```

---

### 5.2 Trigger Sync

**`POST /api/v1/sync/trigger`**

Returns all clipboard items that were **created or updated after** `last_sync_timestamp` for the calling device to process. A `sync` event is recorded as completed.

**Request Body**
```json
{
  "device_id": "b2a3c4d5-0001-0002-0003-000400050006",
  "last_sync_timestamp": "2026-05-31T11:55:00.000000"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `device_id` | UUID string | ✅ | The requesting device |
| `last_sync_timestamp` | datetime | ✅ | ISO 8601 — return items changed after this |

**Response `200 OK`**
```json
{
  "sync_id": "f1e2d3c4-5555-6666-7777-888899990000",
  "items_to_sync": [
    {
      "id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
      "action": "create",
      "content_type": "text",
      "content": "Meeting notes: discuss Q3 roadmap and OKRs.",
      "created_at": "2026-05-31T12:10:00.000000"
    },
    {
      "id": "a9b8c7d6-1111-2222-3333-444455556666",
      "action": "delete",
      "content_type": "url",
      "content": null,
      "created_at": "2026-05-31T09:00:00.000000"
    }
  ],
  "sync_timestamp": "2026-05-31T12:35:00.000000"
}
```

> - `action` is `"create"` for new/updated items and `"delete"` for soft-deleted ones.  
> - Up to **200 items** are returned per sync batch.

---

## 6. Device Management Endpoints 🔒

Manage the devices linked to the authenticated user's account.

---

### 6.1 Register Device

**`POST /api/v1/device`**

Register a new device. If a device with the same `device_name` + `platform` already exists for this user, it is **upserted** — `last_seen`, `device_token`, and `app_version` are updated and the existing record is returned.

**Request Body**
```json
{
  "device_name": "Pixel 8 Pro",
  "device_type": "mobile",
  "platform": "android",
  "os_version": "Android 14",
  "app_version": "1.2.0",
  "device_token": "fcm-token-abc123...",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBg..."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `device_name` | string | ✅ | Human-readable name |
| `device_type` | string | ✅ | `mobile` \| `desktop` \| `web` |
| `platform` | string | ✅ | `ios` \| `android` \| `windows` \| `linux` \| `macos` \| `web` |
| `os_version` | string | ❌ | e.g. `"Android 14"` |
| `app_version` | string | ❌ | e.g. `"1.2.0"` |
| `device_token` | string | ❌ | FCM / APNs push notification token |
| `public_key` | string | ❌ | PEM public key for E2E encryption |

**Response `201 Created`**
```json
{
  "id": "b2a3c4d5-0001-0002-0003-000400050006",
  "device_name": "Pixel 8 Pro",
  "device_type": "mobile",
  "platform": "android",
  "os_version": "Android 14",
  "app_version": "1.2.0",
  "last_seen": "2026-05-31T12:30:00.000000",
  "is_active": true,
  "created_at": "2026-05-20T08:00:00.000000"
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `422` | Invalid `platform` value |

---

### 6.2 List Devices

**`GET /api/v1/device`**

List all active (non-deleted) devices registered under the authenticated user's account, ordered by `last_seen` descending.

**Response `200 OK`**
```json
[
  {
    "id": "b2a3c4d5-0001-0002-0003-000400050006",
    "device_name": "Pixel 8 Pro",
    "device_type": "mobile",
    "platform": "android",
    "os_version": "Android 14",
    "app_version": "1.2.0",
    "last_seen": "2026-05-31T12:30:00.000000",
    "is_active": true,
    "created_at": "2026-05-20T08:00:00.000000"
  },
  {
    "id": "c3b4a5d6-0002-0003-0004-000500060007",
    "device_name": "MacBook Pro 16\"",
    "device_type": "desktop",
    "platform": "macos",
    "os_version": "macOS 14.5",
    "app_version": "1.1.0",
    "last_seen": "2026-05-30T18:00:00.000000",
    "is_active": true,
    "created_at": "2026-05-15T09:00:00.000000"
  }
]
```

---

### 6.3 Remove Device

**`DELETE /api/v1/device/{device_id}`**

Soft-delete (de-register) a device. Sets `is_deleted = true` and `is_active = false`. The device no longer appears in the device list or sync status.

**Path Parameters**

| Param | Type | Notes |
|---|---|---|
| `device_id` | UUID string | The device's `id` |

**Response `200 OK`**
```json
{
  "message": "Device removed successfully"
}
```

**Error Responses**

| Status | Detail |
|---|---|
| `404` | `"Device not found"` |

---

## 7. WebSocket 🔒

**`WS /api/v1/ws?token=<access_token>`**

Full-duplex real-time connection for live clipboard sync across devices.

> **Auth**: The JWT access token is passed as a **query parameter** (not a header) because the WebSocket protocol does not support custom headers in browsers.
>
> Disconnect code `4001` = unauthorized (invalid or expired token).

---

### Connecting

```javascript
const socket = new WebSocket(
  `ws://localhost:8000/api/v1/ws?token=${accessToken}`
);
```

On successful connection the server immediately sends:

```json
{
  "event": "connected",
  "data": {
    "user_id": "a3f1c2d4-1234-5678-abcd-ef0123456789",
    "message": "WebSocket connection established",
    "server_time": "2026-05-31T12:30:00.000000",
    "active_connections": 2
  }
}
```

---

### Client → Server Events

All messages must be valid JSON with `event` and `data` fields:

```json
{
  "event": "<event_name>",
  "data": { ... }
}
```

#### `clipboard_update`

Push a new clipboard item to the server. The server saves it to the database and broadcasts a `clipboard_updated` event to **all of the user's other connected devices**.

```json
{
  "event": "clipboard_update",
  "data": {
    "content": "npm install react-native-paper",
    "content_type": "code",
    "source_device_name": "Pixel 8 Pro"
  }
}
```

#### `sync_request`

Request all clipboard items changed since a given timestamp. The server responds with a `sync_response` event.

```json
{
  "event": "sync_request",
  "data": {
    "last_sync_timestamp": "2026-05-31T11:55:00.000000"
  }
}
```

---

### Server → Client Events

#### `clipboard_updated`

Broadcast when any of the user's devices pushes a new clipboard item. Received by **all other connected sessions** for that user.

```json
{
  "event": "clipboard_updated",
  "data": {
    "id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
    "content": "npm install react-native-paper",
    "content_type": "code",
    "source_device_name": "Pixel 8 Pro",
    "created_at": "2026-05-31T12:30:05.000000"
  }
}
```

#### `sync_response`

Response to a `sync_request`. Contains all items modified after the requested timestamp.

```json
{
  "event": "sync_response",
  "data": {
    "items": [
      {
        "id": "c1d2e3f4-aaaa-bbbb-cccc-ddddeeee1111",
        "content": "npm install react-native-paper",
        "content_type": "code",
        "created_at": "2026-05-31T12:10:00.000000",
        "updated_at": "2026-05-31T12:10:00.000000"
      }
    ],
    "sync_timestamp": "2026-05-31T12:30:10.000000"
  }
}
```

#### `error`

Returned for any invalid message, bad event type, or server-side error.

```json
{
  "event": "error",
  "data": {
    "message": "Unknown event type: 'unknown_event'"
  }
}
```

---

## Common Error Response Format

All error responses follow this shape:

```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (`422 Unprocessable Entity`):

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

Auth endpoints (`/api/v1/auth/*`) are rate-limited to **10 requests per minute per IP**.

Exceeding the limit returns:

```json
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "success": false,
  "error": {
    "message": "Too many requests. Please wait before retrying.",
    "code": "RATE_LIMITED"
  }
}
```

---

## Request Tracing

Every response includes an `X-Request-ID` header containing a UUID for log correlation:

```
X-Request-ID: 7f3a9b2c-1111-2222-3333-444455556666
```

---

## Interactive Docs

The Swagger UI and ReDoc are available while the server is running:

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — interactive try-it-out |
| `http://localhost:8000/redoc` | ReDoc — clean read-only reference |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3.1 schema |
