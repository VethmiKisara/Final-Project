# Authentication & Security Notes

This document explains the authentication design choices, recommended password hashing parameters, token handling, and best practices for secure account flows.

## Design
- Local auth is supported via the `users` table (email/password) and `user_identities` for external providers (OAuth/OIDC).
- Passwords are **never** stored in plaintext. Use a strong KDF (Argon2id recommended) on the application side and store only the resulting hash in `users.password_hash`.
- Email verification uses a verification token whose **hash** is stored in `users.verification_token_hash`. The raw token is sent once to the user's email.
- Password reset tokens are stored hashed in `password_reset_tokens` and are one-time use (field `used`) with an expiry (`expires_at`).

## Password Hashing
- Recommended: Argon2id with conservative parameters depending on hardware. Example parameters (adjust per environment):
  - time_cost = 3
  - memory_cost = 65536 (64 MB)
  - parallelism = 4
- Use `argon2-cffi` or a secure library in your language for hashing and verification.

## Token Handling
- Use secure RNG for tokens (e.g., `secrets.token_urlsafe(32)` in Python).
- Store only a fast digest (SHA-256) of the token in DB (never the raw token).
- Use short TTLs for tokens (email verification: 24 hours; password reset: 1 hour).
- Invalidate tokens on use (set `used = true`) and audit uses.

## Account Security
- Implement rate limiting and exponential backoff for login attempts.
- Lock accounts after several failed attempts and provide secure unlock/verification flows.
- Encourage/require MFA (TOTP or hardware keys) for high-privilege accounts.
- Log auth events (success/failure) for monitoring and detection of brute-force or suspicious activity.

## Transport & Secret Management
- Use TLS for all connections (DB and application endpoints).
- Store credential and token secrets in a proper secret manager (e.g., AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, or GitHub Secrets for CI).
- Rotate keys and credentials periodically, and ensure backups are encrypted.

## Auditing & Compliance
- Retain auth logs for an appropriate duration depending on compliance requirements.
- Ensure PII handling complies with applicable laws (GDPR, CCPA) particularly if storing email addresses.

## Additional Recommendations
- Prefer delegation to trusted identity providers for user-facing auth (OAuth / OIDC) when possible.
- For federated identities, limit the amount of profile data stored and use `user_identities.raw_profile` for non-sensitive provider data.
- Periodically review hashing parameters and rehash passwords on next login if parameters change (use `check_needs_rehash`).

