"""
auth_demo.py
Simple demonstration of sign-up, login, and password reset flows (application-side responsibilities).
Uses Argon2id for password hashing and SHA-256 to store token hashes.

Note: This is a demo only — in production, add rate-limiting, logging, account lockout, email verification delivery, and MFA.
"""
import os
import secrets
import hashlib
import datetime
from argon2 import PasswordHasher, exceptions as argon2_exceptions
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'rtmd')
DB_USER = os.getenv('DB_USER', 'rtmd_user')
DB_PASS = os.getenv('DB_PASS', 'change_me')

ph = PasswordHasher()


def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def signup(email: str, password: str):
    pwd_hash = ph.hash(password)
    verification_token = secrets.token_urlsafe(32)
    v_hash = hash_token(verification_token)
    expires = datetime.datetime.utcnow() + datetime.timedelta(days=1)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash, verification_token_hash, verification_expires, status) VALUES (%s,%s,%s,%s,'pending') RETURNING user_id;",
                (email, pwd_hash, v_hash, expires)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            print('User created (pending verification):', user_id)
            print('Verification token (send via email):', verification_token)
            return user_id, verification_token
    finally:
        conn.close()


def verify_email(token: str):
    v_hash = hash_token(token)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email_verified = true, verification_token_hash = NULL, verification_expires = NULL, status = 'active' WHERE verification_token_hash = %s AND verification_expires > now() RETURNING user_id;",
                (v_hash,)
            )
            r = cur.fetchone()
            if r:
                conn.commit()
                print('Email verified for user:', r[0])
                return True
            else:
                print('Verification failed or token expired')
                return False
    finally:
        conn.close()


def login(email: str, password: str):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_id, password_hash, status FROM users WHERE email = %s;", (email,))
            user = cur.fetchone()
            if not user:
                print('User not found')
                return False
            if user['status'] != 'active':
                print('User not active:', user['status'])
                return False
            try:
                ph.verify(user['password_hash'], password)
                # optionally rehash if needed
                if ph.check_needs_rehash(user['password_hash']):
                    new_hash = ph.hash(password)
                    cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s;", (new_hash, user['user_id']))
                cur.execute("UPDATE users SET last_login = now() WHERE user_id = %s;", (user['user_id'],))
                conn.commit()
                print('Login successful for:', user['user_id'])
                return True
            except argon2_exceptions.VerifyMismatchError:
                print('Incorrect password')
                return False
    finally:
        conn.close()


def create_password_reset(email: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
            r = cur.fetchone()
            if not r:
                print('User not found')
                return None
            user_id = r[0]
            raw_token = secrets.token_urlsafe(32)
            t_hash = hash_token(raw_token)
            expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            cur.execute("INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (%s,%s,%s) RETURNING token_id;", (user_id, t_hash, expires))
            conn.commit()
            print('Password reset token (send via email):', raw_token)
            return raw_token
    finally:
        conn.close()


def consume_password_reset(token: str, new_password: str):
    t_hash = hash_token(token)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT token_id, user_id FROM password_reset_tokens WHERE token_hash = %s AND expires_at > now() AND used = false;", (t_hash,))
            r = cur.fetchone()
            if not r:
                print('Invalid or expired token')
                return False
            token_id, user_id = r
            new_hash = ph.hash(new_password)
            cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s;", (new_hash, user_id))
            cur.execute("UPDATE password_reset_tokens SET used = true WHERE token_id = %s;", (token_id,))
            conn.commit()
            print('Password reset for user:', user_id)
            return True
    finally:
        conn.close()


if __name__ == '__main__':
    print('Auth demo starting...')
    # Demo: sign up, verify, login, password reset
    email = f"demo+{secrets.token_hex(3)}@example.com"
    pwd = 'S3cureP@ssw0rd!'
    user_id, vtoken = signup(email, pwd)
    verify_email(vtoken)
    login(email, pwd)
    token = create_password_reset(email)
    if token:
        consume_password_reset(token, 'N3wS3cureP@ss!')
        login(email, 'N3wS3cureP@ss!')
    print('Auth demo complete.')
