"""Insert example seed data for testing the RTMD schema."""
from datetime import datetime
from argon2 import PasswordHasher
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import (
    Base,
    SocialMediaPost,
    Disaster,
    User,
    Result,
    Location,
    Credibility,
    DataStream,
)


DB_URL = "postgresql+psycopg2://rtmd_user:change_me@localhost:5432/rtmd"


def seed():
    engine = create_engine(DB_URL, future=True)
    # assume tables exist
    ph = PasswordHasher()

    with Session(engine) as session:
        # create a data stream
        stream = DataStream(source_platform="twitter")
        session.add(stream)
        session.flush()

        # create locations
        loc1 = Location(name="Riverbank", district="Central", province="ProvinceA")
        loc2 = Location(name="Uptown", district="North", province="ProvinceB")
        session.add_all([loc1, loc2])

        # create a disaster
        disaster = Disaster(disaster_type="fire", severity="high", confidence_score=0.87, status="active")
        disaster.locations.append(loc1)
        session.add(disaster)

        # create posts
        post1 = SocialMediaPost(post_text="Smoke seen near riverbank", platform="twitter", data_stream=stream, disaster=disaster)
        post2 = SocialMediaPost(post_text="Buildings evacuated in uptown", platform="facebook", data_stream=stream)
        session.add_all([post1, post2])
        session.flush()

        # credibility
        cred1 = Credibility(post=post1, score=0.15, source_verification_status=False)
        cred2 = Credibility(post=post2, score=0.92, source_verification_status=True)
        session.add_all([cred1, cred2])

        # results
        res1 = Result(post=post1, accuracy=0.88, disaster_label="fire", model_type="text+image", confidence_score=0.85)
        res2 = Result(post=post2, accuracy=0.93, disaster_label="evacuation", model_type="text", confidence_score=0.9)
        session.add_all([res1, res2])

        # user and user-result assignment
        user = User(name="Alice Analyst", email="alice@datadreamers.org", password_hash=ph.hash("S3cureP@ss"), role="analyst")
        user.results.append(res1)
        session.add(user)

        session.commit()
        print("Seed data inserted")


if __name__ == "__main__":
    seed()
