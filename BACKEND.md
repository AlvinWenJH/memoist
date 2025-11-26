# Backend
Memoist backend using FastAPI

## Authentication

### Overview
- Provides user registration, login, and user querying backed by Postgres (async SQLAlchemy).
- Authentication uses JWT Bearer tokens; downstream routes can require `Depends(get_current_user)` to enforce auth.

### Endpoints
- `POST /api/v1/auth/` registers a user with `{email, username, password, full_name?}` and returns the user object.
- `POST /api/v1/auth/login` authenticates with `{username, password}` and returns `{access_token, refresh_token, token_type}`.
- `POST /api/v1/auth/refresh` exchanges a valid `refresh_token` for new `{access_token, refresh_token}`.
- `GET /api/v1/auth/stats` returns `{total_users, active_users, inactive_users}`.
- `GET /api/v1/auth/{user_id}` returns a user by UUID.
- `GET /api/v1/auth/` lists users with optional `is_active`, `skip`, `limit`.
- `PUT /api/v1/auth/{user_id}` updates user fields.
- `DELETE /api/v1/auth/{user_id}` deletes a user.

Implementation references:
- JWT dependency and endpoints: `backend/app/api/v1/auth.py:71–96`, `backend/app/api/v1/auth.py:138–148`, `backend/app/api/v1/auth.py:153–168`.

### Hashing Strategy
- Passwords are hashed using `pbkdf2_sha256` with 310k iterations; legacy verification supports `bcrypt_sha256` and `bcrypt`.
- PBKDF2 avoids bcrypt’s 72‑byte limit and is widely adopted.
- Hashing and verification:
  - `backend/app/core/security.py:13` creates a hash for a plaintext password.
  - `backend/app/core/security.py:10–12` verifies a plaintext against the stored hash.
- No manual salt management is required; salts are embedded in hashes.
- Hashes are stored in the `users.password_hash` column.

### JWT Tokens
- Tokens are signed with HS256 using `SECRET_KEY`.
- Claims:
  - `sub`: user UUID (string)
  - `exp`: expiry computed from `ACCESS_TOKEN_EXPIRE_MINUTES` (access) or `REFRESH_TOKEN_EXPIRE_DAYS` (refresh)
  - `type`: present and set to `refresh` for refresh tokens
  - plus optional fields like `username`
- Creation and decode:
  - Access: `backend/app/core/security.py:36–45`
  - Decode: `backend/app/core/security.py:48–49`
  - Refresh: `backend/app/core/security.py:50–56`
- OAuth2 integration:
  - `OAuth2PasswordBearer(tokenUrl="/auth/login")` is defined in `backend/app/api/v1/auth.py:71`.
  - `get_current_user` decodes the token and loads the user: `backend/app/api/v1/auth.py:74–96`.
  - Routers can protect endpoints by adding `current_user = Depends(get_current_user)`.

### Database Schema
- Table: `users` with columns: `id UUID PK`, `email UNIQUE`, `username UNIQUE`, `full_name`, `is_active`, `password_hash`, `created_at`, `updated_at`, `last_login`.
- Init SQL: `backend/db/init.sql`.
- SQLAlchemy model: `backend/app/models/auth.py:9–19`.

### Configuration
- Env vars in `.env`:
  - `DATABASE_URL=postgresql+asyncpg://postgres:password123@postgredb:5432/memoist`
  - `SECRET_KEY` and `ALGORITHM` (default `HS256`)
  - `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30)
  - `REFRESH_TOKEN_EXPIRE_DAYS` (default 7)
  - `DEBUG=true` to expose `/docs` and `/redoc`
- Compose mounts the init SQL:
  - `compose.yml` → `postgredb` → `volumes`: `./backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro`.

### Usage Examples
- Register:
  - `curl -X POST http://localhost:8001/api/v1/auth/ -H "Content-Type: application/json" -d '{"email":"a@b.c","username":"alice","password":"secret"}'`
- Login and call a protected route:
  - `curl -s -X POST http://localhost:8001/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"alice","password":"secret"}' > tokens.json`
  - `ACCESS=$(jq -r .access_token tokens.json)`
  - `REFRESH=$(jq -r .refresh_token tokens.json)`
  - `curl -H "Authorization: Bearer $ACCESS" http://localhost:8001/api/v1/auth/stats`
- Refresh tokens:
  - `curl -s -X POST http://localhost:8001/api/v1/auth/refresh -H "Content-Type: application/json" -d '{"refresh_token":"'$REFRESH'"}' > new_tokens.json`
  - `ACCESS=$(jq -r .access_token new_tokens.json)`
  - `REFRESH=$(jq -r .refresh_token new_tokens.json)`

### Frontend Token Flow

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as Backend

    FE->>API: POST /api/v1/auth/login (username, password)
    API-->>FE: access_token (short exp), refresh_token (long exp)

    FE->>API: GET /protected (Authorization: Bearer access_token)
    API-->>FE: 200 OK

    FE->>FE: Access token expires
    FE->>API: POST /api/v1/auth/refresh (refresh_token)
    API-->>FE: new access_token + new refresh_token

    FE->>API: GET /protected (Authorization: Bearer new access_token)
    API-->>FE: 200 OK

    note over FE,API: Store tokens securely (e.g., httpOnly cookies or secure storage). Avoid sending refresh token except to /refresh.
```
