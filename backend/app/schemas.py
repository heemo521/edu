"""Pydantic schemas for AI Tutoring MVP.

Defines request and response models used by the API endpoints.
"""

from pydantic import BaseModel, constr


class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    role: str = "student"


class UserCreate(UserBase):
    password: constr(min_length=4, max_length=128)


class UserOut(UserBase):
    id: int

    class Config:
        # Pydantic v2 uses 'from_attributes' instead of 'orm_mode'
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    """Request model for chat messages sent to the AI tutor."""
    user_id: int
    thread_id: int
    message: str


class ChatResponse(BaseModel):
    """Response model for chat replies from the AI tutor."""
    response: str


class HistoryItem(BaseModel):
    """Item representing a chat history entry."""
    message: str
    response: str
    timestamp: str


class SubscriptionRequest(BaseModel):
    """Request model for managing a user's subscription status."""
    user_id: int
    action: str = "activate"  # 'activate' or 'cancel'


class SubscriptionStatus(BaseModel):
    """Response model for a user's subscription status."""
    user_id: int
    status: str
    start_date: str | None = None
    end_date: str | None = None


# ------------------------ Thread Schemas ------------------------

class ThreadBase(BaseModel):
    """Base fields for a conversation thread."""
    user_id: int
    name: constr(min_length=1, max_length=100)


class ThreadCreate(ThreadBase):
    """Model for creating a new conversation thread."""
    pass


class Thread(ThreadBase):
    """Thread returned in API responses."""
    id: int
    created_at: str | None = None

    class Config:
        from_attributes = True



# ------------------------ Topic and Goal Schemas ------------------------

class TopicBase(BaseModel):
    """Base fields for a topic."""
    name: constr(min_length=1, max_length=100)
    description: str | None = None


class TopicCreate(TopicBase):
    """Model for creating a new topic."""
    pass


class Topic(TopicBase):
    """Topic returned in API responses."""
    id: int

    class Config:
        from_attributes = True


class GoalBase(BaseModel):
    """Base fields for a study goal."""
    user_id: int
    topic_id: int
    description: str | None = None
    target_sessions: int
    due_date: str | None = None


class GoalCreate(GoalBase):
    """Model for creating a new study goal."""
    pass


class Goal(GoalBase):
    """Study goal returned in API responses."""
    id: int
    completed_sessions: int
    created_at: str

    class Config:
        from_attributes = True


# ------------------------ Plan Schemas ------------------------

class PlanBase(BaseModel):
    """Base fields for a study plan."""
    user_id: int
    goal_ids: list[int]
    due_date: str | None = None
    recurrence: str | None = None


class PlanCreate(PlanBase):
    """Model for creating a new study plan."""
    pass


class Plan(BaseModel):
    """Study plan returned in API responses."""
    id: int
    user_id: int
    goals: list[Goal]
    due_date: str | None = None
    recurrence: str | None = None
    created_at: str

    class Config:
        from_attributes = True
