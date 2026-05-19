# ☁️ Cloud Clipboard Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=python&logoColor=white)](https://www.sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)](https://jwt.io)

A highly secure, robust, and optimized backend engine for **Cloud Clipboard**, allowing users to seamlessly synchronize clipboard items (texts, URLs, files, images) across all their devices in real-time. Built with **FastAPI**, **SQLAlchemy 2.0**, and integrated with **Supabase PostgreSQL**.

---

## ✨ Features

- **🔐 Secure Authentication**: Full JWT-based authorization (Access and Refresh tokens) with robust password hashing using native `bcrypt`.
- **📋 Clipboard Synchronization**: Instantly save, categorize, and fetch clipboard histories. Supports `text`, `url`, `image`, and `file` types.
- **🛡️ Protected Endpoints**: Clipboard endpoints are JWT-gated — the user's identity is extracted exclusively from the bearer token, never from the request body.
- **⚡ Connection Pooling**: Custom-tailored database pooling engineered to sustain optimal performance and low latency with remote PostgreSQL instances (Supabase).
- **🛡️ Data Integrity**: Validates UUID models, content lengths, and formats safely using standard Pydantic models.
- **🚀 Live-Reload Server**: Built-in development setup with Uvicorn.

---

## 🛠️ Tech Stack & Core Libraries

- **Core Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Web Framework)
- **Database Engine & ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) (Migrations)
- **Database Hosting**: [Supabase PostgreSQL](https://supabase.com/)
- **Authentication & Security**: [PyJWT](https://pyjwt.readthedocs.io/), [bcrypt](https://github.com/pyca/bcrypt)
- **Settings & Validation**: [Pydantic v2](https://docs.pydantic.dev/)

---

## 📂 Project Structure

```text
Backend/
├── api/                  # API routes (V1)
│   └── v1/
│       ├── auth/         # Login, Register endpoints + JWT dependency
│       ├── clipboard/    # Clipboard management routes (JWT-protected)
│       └── router.py     # Main API router registry
├── core/                 # App configurations and security primitives
│   ├── config.py         # Pydantic Settings (Environment variables)
│   └── security.py       # Password hashing and JWT generation
├── db/                   # Database config, models, and sessions
│   ├── models/           # SQLAlchemy DB Models (User, ClipboardItem, etc.)
│   └── session.py        # Database connection pool settings (psycopg2)
├── alembic/              # Database migration history
├── schemas/              # Pydantic schemas for request/response serialization
├── main.py               # Application entry point
├── test_clipboard.py     # Automated integration test suite
└── requirements.txt      # Project dependencies
```

---

## 🚀 Getting Started

### Prerequisites
- Python `3.10+`
- [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`
- A remote Supabase database instance (or a local PostgreSQL server)

### 1. Environment Setup

Clone the repository, navigate to the `Backend` directory, and copy the environment configuration file:

```bash
# In the Backend directory
cp .env.example .env
```

Open `.env` and fill out your configuration details:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db_name>
SECRET_KEY=your-secure-random-jwt-signing-key
```

### 2. Install Dependencies

Using `uv` (recommended for rapid installs):
```bash
# Create virtual environment
uv venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install requirements
uv pip install -r requirements.txt
```

### 3. Run Database Migrations

Apply current Alembic schemas to your database:
```bash
alembic upgrade head
```

### 4. Start the Server

Start Uvicorn with reloading enabled for development:
```bash
uvicorn main:app --port 8001 --reload
```
The server will start at `http://127.0.0.1:8001`. Interactive API docs will be available at `http://127.0.0.1:8001/docs`.

---

## 🧪 Testing the API

A test integration script `test_clipboard.py` is included to automatically verify user registration, JWT generation, and clipboard save routes.

To run the automated tests against your local server:
```bash
# Make sure the Uvicorn server is running on port 8001
.venv\Scripts\python test_clipboard.py
```

---

## 📡 API Reference

This section details all available API endpoints, their HTTP methods, usage, request payloads, and expected response models.

---

### 1. Root & Utility Endpoints

These are basic health-check and status endpoints mapped directly in `main.py`.

#### **Welcome Endpoint**
* **URL**: `/`
* **Method**: `GET`
* **Use**: Verifies that the FastAPI server is running.
* **Request Headers**: None
* **Request Body**: None
* **Response (200 OK)**:
  ```json
  {
    "message": "Hello World"
  }
  ```

#### **Health Check**
* **URL**: `/health`
* **Method**: `GET`
* **Use**: Simple health probe for monitoring.
* **Request Headers**: None
* **Request Body**: None
* **Response (200 OK)**:
  ```json
  {
    "status": "healthy"
  }
  ```

---

### 2. Authentication Endpoints (`/api/v1/auth`)

These endpoints manage user accounts and session generation.

#### **User Registration**
* **URL**: `/api/v1/auth/register`
* **Method**: `POST`
* **Use**: Registers a new user, hashes the password using raw `bcrypt`, generates initial JWT access and refresh tokens, and provisions a verification code.
* **Request Body (JSON)**:
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
- **Response (200 OK)**:
  ```json
  {
    "id": "b71a2a44-1806-4393-bd77-1b86e7278a61",
    "username": "john.doe@example.com",
    "email": "john.doe@example.com",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "needs_onboarding": true,
    "created_at": "2026-05-19T04:50:53.585003",
    "updated_at": "2026-05-19T04:50:54.312322"
  }
  ```

#### **User Login**
* **URL**: `/api/v1/auth/login`
* **Method**: `POST`
* **Use**: Logs in an existing user by verifying credentials and returning a fresh JWT token pair.
* **Request Body (JSON)**:
  ```json
  {
    "email": "john.doe@example.com",
    "password": "strongpassword123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": "b71a2a44-1806-4393-bd77-1b86e7278a61",
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

### 3. Clipboard Endpoints (`/api/v1/clipboard`)

These endpoints manage items pushed to or pulled from the cloud clipboard.

#### **Save Clipboard Item**
* **URL**: `/api/v1/clipboard/personal`
* **Method**: `POST`
* **Use**: Saves a new clipboard text, image, url, or file metadata reference.
* **Request Headers**:
  ```
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
* **Request Body (JSON)**:
  ```json
  {
    "content": "This is text saved to the cloud clipboard!",
    "content_type": "text",
    "expires_at": null,
    "is_private": false,
    "source_device_id": null
  }
  ```
  *(Note: `content_type` must be one of: `text`, `image`, `file`, `url`. `user_id` is no longer required — it is read from the JWT token.)*
- **Response (200 OK)**:
  ```json
  {
    "content": "This is text saved to the cloud clipboard!",
    "created_at": "2026-05-19T04:50:55.798256",
    "updated_at": "2026-05-19T04:50:55.798265"
  }
  ```

#### **Get Clipboard Items**
* **URL**: `/api/v1/clipboard/personal`
* **Method**: `GET`
* **Use**: Retrieves saved clipboard items for the authenticated user.
* **Request Headers**:
  ```
  Authorization: Bearer <access_token>
  ```
* **Query Parameters**: None required. User identity is determined from the JWT token.
- **Response (200 OK)**:
  ```json
  [
    {
      "content": "This is text saved to the cloud clipboard!",
      "created_at": "2026-05-19T04:50:55.798256",
      "updated_at": "2026-05-19T04:50:55.798265"
    }
  ]
  ```

---

## 🔒 Security Practices

- **Zero Passlib Dependency**: Mitigates Python 3.12+ crash loops by replacing deprecated `passlib` with native `bcrypt` wrappers.
- **One-Way Hash**: Passwords are securely salted and hashed before storing.
- **Stateless Auth**: Validates client access strictly via custom cryptographically-signed JWT keys.
- **User Identity in JWT**: The user's UUID is stored in the token `sub` claim. Clipboard endpoints extract the caller's identity from the token — `user_id` is never sent in request bodies or exposed in responses.
- **Variable Protection**: Prevents credential leaks by utilizing standard strict `.gitignore` patterns.
