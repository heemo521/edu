"""SQLAlchemy models for AI Tutoring MVP.

Defines database models representing the entities used by the application.
"""

from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):
    """User model storing authentication and role information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")  # student, parent, teacher, admin


class Feedback(Base):
    """User feedback on study materials."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comments = Column(String, nullable=True)