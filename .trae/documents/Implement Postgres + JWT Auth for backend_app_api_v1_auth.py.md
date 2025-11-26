## Objectives

* Migrate `auth.py` to Postgres (async SQLAlchemy)

* Implement secure password hashing (bcrypt via Passlib)

* Implement JWT issuance and verification

* Provide reusable `Depends(get_current_user)` for all routers

* Provide `init.sql` to create the `users` table (without query/document count columns)

## Changes

### 1) Database Layer

* Add `app/core/db.py` with async SQLAlchemy engine/session and `get_db()` dependency

* Add SQLAlchemy `User` model (in `app/core/models.py` or inside `auth.py`):

  * `id UUID PK`, `email UNIQUE`, `username UNIQUE`, `full_name`, `is_active`, `password_hash`, `created_at`, `updated_at`, `last_login`

### 2) Initial SQL

* Add `backend/db/init.sql`:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL UNIQUE,
  username TEXT NOT NULL UNIQUE,
  full_name TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
```

### 3) Security Utilities

* Add `app/core/security.py`:

  * `CryptContext(schemes=["bcrypt"], deprecated="auto")`

  * `verify_password`, `get_password_hash`

  * JWT helpers using `python-jose`: `create_access_token`, `decode_token`

  * Use `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` from settings

### 4) Update `auth.py`

* Replace Mongo usage with Postgres via `AsyncSession`

* Pydantic models:

  * Remove `query_count` and `document_count` from responses

  * Provide `Token` model for JWT outputs

* Endpoints:

  * `POST /auth/register` (or keep `POST /auth/`): create user with hashed password

  * `POST /auth/login`: authenticate, update `last_login`, return `{access_token, token_type}`

  * `GET /auth/stats`: keep only `total_users`, `active_users`, `inactive_users`

  * `GET /auth/{user_id}`, `GET /auth/`, `PUT /auth/{user_id}`, `DELETE /auth/{user_id}` using SQLAlchemy

* Add shared dependency:

  * `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")`

  * `get_current_user(db, token)` → decode JWT, load user by `sub`, raise 401 if invalid; export for other routers

### 5) Settings

* Extend `app/core/settings.py` with `DATABASE_URL` string; continue using existing security fields

## Libraries

* `sqlalchemy[asyncio]`, `asyncpg`, `passlib[bcrypt]`, `python-jose`

## Verification

* Register → login → call a protected sample endpoint using `Depends(get_current_user)`

## Notes

* Admin fallback is removed; login is via DB

* All references to `query_count`/`document_count` are removed in schema and API

