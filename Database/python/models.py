"""SQLAlchemy ORM models for RTMD project.

Defines tables and relationships for:
- SocialMediaPost, Disaster, User, Result, Location, Credibility, DataStream
- Association tables: disaster_location, user_result

Run: used by create_db.py and seed_data.py
"""
from datetime import datetime
import enum
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    Table,
    CheckConstraint,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DisasterStatus(enum.Enum):
    pending = "pending"
    active = "active"
    resolved = "resolved"
    investigating = "investigating"
    archived = "archived"


# Association tables
disaster_location = Table(
    "disaster_location",
    Base.metadata,
    Column(
        "disaster_id",
        UUID(as_uuid=True),
        ForeignKey("disasters.disaster_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "location_id",
        UUID(as_uuid=True),
        ForeignKey("locations.location_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_result = Table(
    "user_result",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "result_id",
        UUID(as_uuid=True),
        ForeignKey("results.result_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class DataStream(Base):
    __tablename__ = "data_streams"

    stream_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_platform = Column(String(128), nullable=False)
    last_update_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Optional pointer to last processed post
    last_post_id = Column(UUID(as_uuid=True), ForeignKey("social_media_posts.post_id", ondelete="SET NULL"), nullable=True)

    posts = relationship("SocialMediaPost", back_populates="data_stream")

    def __repr__(self):
        return f"<DataStream(id={self.stream_id} platform={self.source_platform})>"


class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"

    post_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_text = Column(Text, nullable=True)
    post_image = Column(String(512), nullable=True)
    language = Column(String(8), nullable=True, index=True)
    platform = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    # A post may produce many results and many credibility assessments
    results = relationship("Result", back_populates="post", cascade="all, delete-orphan")
    credibility = relationship("Credibility", back_populates="post", cascade="all, delete-orphan")

    # Many posts belong to one disaster (N:1)
    disaster_id = Column(UUID(as_uuid=True), ForeignKey("disasters.disaster_id", ondelete="SET NULL"), nullable=True, index=True)
    disaster = relationship("Disaster", back_populates="posts")

    # Data stream relationship (1:N: DataStream -> SocialMediaPost)
    data_stream_id = Column(UUID(as_uuid=True), ForeignKey("data_streams.stream_id", ondelete="SET NULL"), nullable=True, index=True)
    data_stream = relationship("DataStream", back_populates="posts")

    def __repr__(self):
        return f"<Post(id={self.post_id} platform={self.platform} ts={self.timestamp})>"


class Disaster(Base):
    __tablename__ = "disasters"

    disaster_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disaster_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=True)
    confidence_score = Column(Float, nullable=False)
    date_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status = Column(String(32), nullable=False, default=DisasterStatus.pending.value)

    # Posts related to this disaster (one-to-many)
    posts = relationship("SocialMediaPost", back_populates="disaster")

    # Many-to-many with locations
    locations = relationship("Location", secondary=disaster_location, back_populates="disasters")

    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_disaster_confidence_range"),
    )

    def __repr__(self):
        return f"<Disaster(id={self.disaster_id} type={self.disaster_type} conf={self.confidence_score})>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(64), nullable=False, default="analyst")

    results = relationship("Result", secondary=user_result, back_populates="users")

    def __repr__(self):
        return f"<User(id={self.user_id} email={self.email})>"


class Result(Base):
    __tablename__ = "results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to the originating post
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_media_posts.post_id", ondelete="CASCADE"), nullable=False, index=True)
    post = relationship("SocialMediaPost", back_populates="results")

    accuracy = Column(Float, nullable=False)
    disaster_label = Column(String(64), nullable=True)
    model_type = Column(String(128), nullable=False)
    confidence_score = Column(Float, nullable=False)

    users = relationship("User", secondary=user_result, back_populates="results")

    __table_args__ = (
        CheckConstraint("accuracy >= 0 AND accuracy <= 1", name="ck_result_accuracy_range"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_result_confidence_range"),
    )

    def __repr__(self):
        return f"<Result(id={self.result_id} post={self.post_id} conf={self.confidence_score})>"


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False)
    district = Column(String(128), nullable=True)
    province = Column(String(128), nullable=True)

    disasters = relationship("Disaster", secondary=disaster_location, back_populates="locations")

    def __repr__(self):
        return f"<Location(id={self.location_id} name={self.name})>"


class Credibility(Base):
    __tablename__ = "credibility"

    credibility_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_media_posts.post_id", ondelete="CASCADE"), nullable=False, index=True)
    post = relationship("SocialMediaPost", back_populates="credibility")

    score = Column(Float, nullable=False)
    source_verification_status = Column(Boolean, nullable=False, default=False)
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 1", name="ck_cred_score_range"),
    )

    def __repr__(self):
        return f"<Credibility(id={self.credibility_id} score={self.score})>"


# Additional indexes for common queries
Index("ix_results_post_confidence", Result.post_id, Result.confidence_score)
Index("ix_disasters_date_time", Disaster.date_time)
Index("ix_social_posts_ts_platform", SocialMediaPost.timestamp, SocialMediaPost.platform)
