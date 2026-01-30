-- V2__add_auth.sql
-- Add authentication-related tables: users, user_identities, password_reset_tokens

-- users table
CREATE TABLE IF NOT EXISTS users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT, -- store Argon2/Bcrypt hashes only; NULL when using external identity only
  status TEXT NOT NULL CHECK (status IN ('pending','active','suspended','disabled')) DEFAULT 'pending',
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verification_token_hash TEXT, -- store hashed verification tokens
  verification_expires TIMESTAMPTZ,
  roles TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- user_identities for external auth (OAuth/OpenID Connect)
CREATE TABLE IF NOT EXISTS user_identities (
  identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  provider TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  raw_profile JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  UNIQUE (provider, provider_user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_identities_user ON user_identities (user_id);

-- Password reset tokens (store token hashes, and expire/one-time use enforcement)
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  token_hash TEXT NOT NULL, -- store sha256 or similar of the token (not the raw token)
  expires_at TIMESTAMPTZ NOT NULL,
  used BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires ON password_reset_tokens (expires_at);

-- Sample usage notes (application side responsibilities) -----
-- 1) Sign-up (application should):
--    - validate email format and rate limit attempts
--    - hash password using Argon2id (or bcrypt/Argon2) with secure parameters
--    - insert into users(email, password_hash, status='pending', verification_token_hash, verification_expires)
--    - send verification email containing the raw verification token (store only hashed token)

-- Example (pseudo-SQL; hashing done by app):
-- INSERT INTO users (email, password_hash, verification_token_hash, verification_expires) VALUES ('user@example.com', '<argon2_hash>', '<sha256_of_token>', now() + interval '1 day');

-- 2) Email verification (application):
--    - receive token from link, hash token, and look for user with matching verification_token_hash and expires > now(); set email_verified = true, verification_token_hash = NULL, status = 'active'
--    - Example: UPDATE users SET email_verified = true, verification_token_hash = NULL, status = 'active' WHERE verification_token_hash = '<sha256>' AND verification_expires > now();

-- 3) Login (application):
--    - fetch user by email, verify Argon2 hash matches provided password, update last_login on success, enforce rate-limits and lockouts on repeated failure

-- 4) Password reset flow (application):
--    - create a secure random token, store hash in password_reset_tokens for the user with expiry (e.g., 1 hour)
--    - send raw token via email to user
--    - when user presents token, hash it and search token record with used = false and expires_at > now(); on success set used = true and update user's password_hash with new Argon2 hash

-- Security notes: see AUTH.md in repo for details on hashing parameters, token handling, MFA recommendations, and secret management.
