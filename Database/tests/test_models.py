"""Pytest integration tests for schema and basic operations.

These tests expect a PostgreSQL database available via TEST_DATABASE_URL env var.
By default tests use: postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd_test
"""
import os
import subprocess

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from python.models import Base, User, SocialMediaPost, Result


TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', 'postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd_test')


@pytest.fixture(scope='session')
def db_engine():
    # Ensure migrations are applied first
    os.environ['DATABASE_URL'] = TEST_DATABASE_URL
    subprocess.check_call(['alembic', 'upgrade', 'head'])
    engine = create_engine(TEST_DATABASE_URL, future=True)
    yield engine
    engine.dispose()


def test_basic_insert_and_query(db_engine):
    with Session(db_engine) as session:
        # Create a user and a post and attach a result
        user = User(name='Test User', email='test@example.org', password_hash='hash', role='analyst')
        session.add(user)
        post = SocialMediaPost(post_text='Test', platform='twitter')
        session.add(post)
        session.flush()
        res = Result(post=post, accuracy=0.9, disaster_label='fire', model_type='demo', confidence_score=0.85)
        session.add(res)
        user.results.append(res)
        session.commit()

        # Query back
        u = session.query(User).filter_by(email='test@example.org').one()
        assert u.name == 'Test User'
        assert len(u.results) == 1
        r = u.results[0]
        assert r.confidence_score == pytest.approx(0.85)


def test_constraints(db_engine):
    with Session(db_engine) as session:
        # Confidence out of range should fail
        with pytest.raises(Exception):
            bad = Result(post=None, accuracy=1.1, disaster_label='x', model_type='m', confidence_score=1.5)
            session.add(bad)
            session.commit()
