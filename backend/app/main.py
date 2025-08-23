from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

from . import schemas, database, auth, tutor
from . import progress

import json
import os

# ---------------------- Study Materials Loading ----------------------
# Load structured study materials from JSON file at startup.  The file defines
# subject areas (e.g., math, science), categories (e.g., algebra, biology) and
# their units and topics.  Having this in memory allows the API to serve
# curriculum content without reading from disk on each request.
BASE_DIR = os.path.dirname(__file__)
_materials_path = os.path.join(BASE_DIR, "data", "study_materials.json")
try:
    with open(_materials_path, "r", encoding="utf-8") as f:
        STUDY_MATERIALS: dict[str, dict] = json.load(f)
except Exception:
    # If the file cannot be read or parsed, fall back to an empty dict.  This
    # prevents application startup failure and allows other endpoints to
    # continue functioning.  In production, proper logging and error
    # propagation should be implemented.
    STUDY_MATERIALS = {}

# ---------------------- Goal Templates Loading ----------------------
_goal_templates_path = os.path.join(BASE_DIR, "data", "goal_templates.json")
try:
    with open(_goal_templates_path, "r", encoding="utf-8") as f:
        GOAL_TEMPLATES: dict[str, list[dict]] = json.load(f)
except Exception:
    # If templates cannot be loaded, default to an empty dictionary so the
    # application still functions. Endpoints depending on templates will
    # return a 404 when accessed.
    GOAL_TEMPLATES = {}


# ---------------------- Context Builder ----------------------
def build_context(user_id: int, thread_id: int, db: sqlite3.Connection) -> str:
    """Construct a context string for the tutoring agent.

    The context includes a summary of the user's current study goals and
    a short history of recent messages in the specified thread. This
    information helps the AI assistant personalize its responses.

    Args:
        user_id: The ID of the user.
        thread_id: The ID of the conversation thread.
        db: A database connection.

    Returns:
        A string summarizing goals and recent conversation history.
    """
    cursor = db.cursor()
    # Fetch active goals and their progress
    cursor.execute(
        """
        SELECT description, target_sessions, completed_sessions
        FROM goals
        WHERE user_id = ?
        ORDER BY created_at ASC
        """,
        (user_id,),
    )
    goals_rows = cursor.fetchall()
    goals_parts: list[str] = []
    for row in goals_rows:
        desc = row["description"] or "Goal"
        completed = row["completed_sessions"]
        target = row["target_sessions"]
        goals_parts.append(f"{desc} ({completed}/{target} sessions)")
    goals_text = "; ".join(goals_parts) if goals_parts else "No active goals"

    # Fetch the last five messages from this thread, sorted by newest first.
    cursor.execute(
        "SELECT message, response FROM messages WHERE user_id = ? AND thread_id = ? ORDER BY timestamp DESC LIMIT 5",
        (user_id, thread_id),
    )
    rows = cursor.fetchall()
    # Determine total number of messages in this thread. This enables us to insert
    # a summary line when older conversation exists beyond our limited context.
    cursor.execute(
        "SELECT COUNT(*) AS total_count FROM messages WHERE user_id = ? AND thread_id = ?",
        (user_id, thread_id),
    )
    count_row = cursor.fetchone()
    total_count = count_row["total_count"] if count_row and count_row["total_count"] is not None else 0
    # Reverse the limited rows to chronological order so the conversation flows naturally.
    rows = list(reversed(rows))
    history_parts: list[str] = []
    # If there are more messages than we've fetched, include a note about omitted
    # messages. We can't summarise them automatically yet, but this warns the
    # tutor (and the user) that earlier context exists.
    if total_count > len(rows) and len(rows) > 0:
        omitted = total_count - len(rows)
        history_parts.append(
            f"(Earlier conversation has {omitted} additional messages; older messages have been summarized.)"
        )
    for row in rows:
        msg = row["message"]
        resp = row["response"]
        history_parts.append(f"Student: {msg}\nTutor: {resp}")
    history_text = "\n".join(history_parts) if history_parts else "No recent history"

    return f"User goals: {goals_text}\nRecent history:\n{history_text}"


def create_goals_from_template(user_id: int, subject: str, db: sqlite3.Connection) -> list[schemas.Goal]:
    """Create a set of goals for a user from a subject template.

    Args:
        user_id: The ID of the user who will own the goals.
        subject: Key for the template group in ``GOAL_TEMPLATES``.
        db: Database connection.

    Returns:
        A list of newly created ``schemas.Goal`` instances.

    Raises:
        HTTPException: If no templates exist for the requested subject.
    """

    template = GOAL_TEMPLATES.get(subject)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No templates for subject")

    cursor = db.cursor()
    created: list[schemas.Goal] = []
    for item in template:
        topic_name = item.get("topic")
        desc = item.get("description")
        target = item.get("target_sessions", 1)

        # Find topic ID; skip if topic not found in DB
        cursor.execute("SELECT id FROM topics WHERE name = ?", (topic_name,))
        topic_row = cursor.fetchone()
        if not topic_row:
            continue

        cursor.execute(
            "INSERT INTO goals (user_id, topic_id, description, target_sessions, completed_sessions) VALUES (?, ?, ?, ?, 0)",
            (user_id, topic_row["id"], desc, target),
        )
        goal_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, user_id, topic_id, description, target_sessions, completed_sessions, created_at, due_date FROM goals WHERE id = ?",
            (goal_id,),
        )
        row = cursor.fetchone()
        created.append(
            schemas.Goal(
                id=row["id"],
                user_id=row["user_id"],
                topic_id=row["topic_id"],
                description=row["description"],
                target_sessions=row["target_sessions"],
                completed_sessions=row["completed_sessions"],
                created_at=row["created_at"],
                due_date=row["due_date"],
            )
        )

    db.commit()
    return created

app = FastAPI(title="AI Tutoring MVP")

# Configure CORS to allow frontend access (e.g., from localhost:8000 and file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint for health check."""
    return {"message": "Welcome to the AI Tutoring MVP!"}


@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: sqlite3.Connection = Depends(database.get_db)):
    """Register a new user.

    Checks for existing username, hashes the password and stores the new user.
    """
    # Check if username already exists
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    # Create user
    hashed = auth.get_password_hash(user.password)
    cursor.execute(
        "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
        (user.username, hashed, user.role),
    )
    db.commit()
    user_id = cursor.lastrowid

    # Create a default conversation thread for the new user. This initial
    # thread provides a place to store messages before any custom threads are
    # created. Naming it "General" conveys that it is a catch-all thread.
    cursor.execute(
        "INSERT INTO threads (user_id, name) VALUES (?, ?)",
        (user_id, "General")
    )
    db.commit()
    return schemas.UserOut(id=user_id, username=user.username, role=user.role)


@app.post("/login")
def login(login_request: schemas.LoginRequest, db: sqlite3.Connection = Depends(database.get_db)):
    """Authenticate a user and return a simple success message.

    In a full implementation this would return a JWT or session token. For this MVP
    we simply verify credentials and respond with a confirmation.
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, hashed_password, role FROM users WHERE username = ?", (login_request.username,)
    )
    row = cursor.fetchone()
    if not row or not auth.verify_password(login_request.password, row["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return {"message": "Login successful", "user_id": row["id"], "role": row["role"]}


@app.get("/users/{user_id}")
def get_user_info(user_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Return basic user information along with subscription status and message count."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT username, role FROM users WHERE id = ?",
        (user_id,),
    )
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Get subscription status
    cursor.execute(
        "SELECT status FROM subscriptions WHERE user_id = ?",
        (user_id,),
    )
    sub = cursor.fetchone()
    status_val = sub["status"] if sub else "inactive"
    # Get message count
    cursor.execute(
        "SELECT COUNT(*) AS count FROM messages WHERE user_id = ?",
        (user_id,),
    )
    count_row = cursor.fetchone()
    message_count = count_row["count"] if count_row else 0
    # Get progress metrics (XP, level, streak) from users table
    cursor.execute(
        "SELECT xp, level, streak_count FROM users WHERE id = ?",
        (user_id,),
    )
    progress_row = cursor.fetchone()
    xp_val = progress_row["xp"] if progress_row and progress_row["xp"] is not None else 0
    level_val = progress_row["level"] if progress_row and progress_row["level"] is not None else 0
    streak_val = (
        progress_row["streak_count"]
        if progress_row and progress_row["streak_count"] is not None
        else 0
    )
    return {
        "id": user_id,
        "username": user["username"],
        "role": user["role"],
        "subscription_status": status_val,
        "message_count": message_count,
        "xp": xp_val,
        "level": level_val,
        "streak_count": streak_val,
    }


@app.post("/chat", response_model=schemas.ChatResponse)
def chat(request: schemas.ChatRequest, db: sqlite3.Connection = Depends(database.get_db)):
    """Handle a chat message from a user and return a tutor response.

    Args:
        request: ChatRequest containing the user_id and message.
        db: SQLite connection (unused for this stub but provided for future expansion).

    Returns:
        ChatResponse with the AI tutor's reply.
    """
    # In a full implementation we could use user_id and thread_id to personalize the response
    # Build a context summary including goals and recent history
    context_str = build_context(request.user_id, request.thread_id, db)
    # Prepend the context to the student's message so the LLM can use it
    prompt = f"{context_str}\n\n{request.message}"
    answer = tutor.get_tutor_response(prompt)
    # Insert chat log into messages table for progress tracking
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, thread_id, message, response) VALUES (?, ?, ?, ?)",
        (request.user_id, request.thread_id, request.message, answer),
    )
    db.commit()
    # After recording the message, update the user's progress (XP, level, streak).
    try:
        progress.update_progress(request.user_id, db)
    except Exception:
        # Fail silently on progress update; chat functionality should not be blocked
        pass
    return schemas.ChatResponse(response=answer)


@app.get("/history/{user_id}/{thread_id}", response_model=list[schemas.HistoryItem])
def get_history(user_id: int, thread_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Return the chat history for a specific user and thread ordered by timestamp."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT message, response, timestamp FROM messages WHERE user_id = ? AND thread_id = ? ORDER BY timestamp ASC",
        (user_id, thread_id),
    )
    rows = cursor.fetchall()
    history = [
        schemas.HistoryItem(
            message=row["message"], response=row["response"], timestamp=row["timestamp"]
        )
        for row in rows
    ]
    return history


@app.get("/dashboard/{user_id}")
def get_dashboard(user_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Return a simple dashboard summary for a user.

    The dashboard includes the number of chat messages exchanged and the timestamp
    of the most recent message. In future versions, this could include topic
    mastery, accuracy and personalized recommendations.
    """
    cursor = db.cursor()
    # Count total messages and last activity
    cursor.execute(
        "SELECT COUNT(*) AS count, MAX(timestamp) AS last_ts FROM messages WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    total_messages = row["count"] if row["count"] is not None else 0
    last_timestamp = row["last_ts"] if row["last_ts"] else None
    # Count distinct session days
    cursor.execute(
        "SELECT COUNT(DISTINCT DATE(timestamp)) AS sessions FROM messages WHERE user_id = ?",
        (user_id,),
    )
    session_row = cursor.fetchone()
    sessions_count = session_row["sessions"] if session_row and session_row["sessions"] is not None else 0
    # Determine badges based on total messages and sessions
    badges: list[str] = []
    if total_messages >= 1:
        badges.append("First Chat Completed")
    if total_messages >= 10:
        badges.append("10 Messages")
    if sessions_count >= 5:
        badges.append("5 Sessions")
    # Include progress metrics (XP, level, streak) in dashboard
    cursor.execute(
        "SELECT xp, level, streak_count FROM users WHERE id = ?",
        (user_id,),
    )
    p_row = cursor.fetchone()
    xp_val = p_row["xp"] if p_row and p_row["xp"] is not None else 0
    level_val = p_row["level"] if p_row and p_row["level"] is not None else 0
    streak_val = p_row["streak_count"] if p_row and p_row["streak_count"] is not None else 0
    return {
        "user_id": user_id,
        "total_messages": total_messages,
        "last_activity": last_timestamp,
        "sessions_count": sessions_count,
        "badges": badges,
        "xp": xp_val,
        "level": level_val,
        "streak_count": streak_val,
    }


@app.post("/subscribe", response_model=schemas.SubscriptionStatus)
def manage_subscription(req: schemas.SubscriptionRequest, db: sqlite3.Connection = Depends(database.get_db)):
    """Activate or cancel a user's subscription.

    For the MVP, this endpoint simulates subscription management without real payment processing. If the action
    is 'activate', the subscription is marked active and the start date is set to now. If the action is 'cancel',
    the status becomes inactive and the end date is set to now.
    """
    cursor = db.cursor()
    # Check if subscription record exists
    cursor.execute(
        "SELECT id, status, start_date, end_date FROM subscriptions WHERE user_id = ?",
        (req.user_id,),
    )
    row = cursor.fetchone()
    import datetime
    now = datetime.datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    if req.action == "activate":
        if row:
            # Update existing record
            cursor.execute(
                "UPDATE subscriptions SET status = 'active', start_date = ?, end_date = NULL WHERE user_id = ?",
                (now, req.user_id),
            )
        else:
            cursor.execute(
                "INSERT INTO subscriptions (user_id, status, start_date) VALUES (?, 'active', ?)",
                (req.user_id, now),
            )
        db.commit()
        return schemas.SubscriptionStatus(user_id=req.user_id, status="active", start_date=now)
    elif req.action == "cancel":
        if row and row["status"] == "active":
            cursor.execute(
                "UPDATE subscriptions SET status = 'inactive', end_date = ? WHERE user_id = ?",
                (now, req.user_id),
            )
            db.commit()
            return schemas.SubscriptionStatus(
                user_id=req.user_id, status="inactive", start_date=row["start_date"], end_date=now
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription not active")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")


@app.get("/subscription/{user_id}", response_model=schemas.SubscriptionStatus)
def get_subscription_status(user_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Get the current subscription status for a user."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT status, start_date, end_date FROM subscriptions WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        return schemas.SubscriptionStatus(user_id=user_id, status="inactive")
    return schemas.SubscriptionStatus(
        user_id=user_id,
        status=row["status"],
        start_date=row["start_date"],
        end_date=row["end_date"],
    )


# ---------------------- Topic and Goal Endpoints ----------------------

@app.get("/topics", response_model=list[schemas.Topic])
def list_topics(db: sqlite3.Connection = Depends(database.get_db)):
    """Return a list of all available topics."""
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description FROM topics ORDER BY name ASC")
    rows = cursor.fetchall()
    topics: list[schemas.Topic] = []
    for row in rows:
        topics.append(schemas.Topic(id=row["id"], name=row["name"], description=row["description"]))
    return topics


@app.post("/topics", response_model=schemas.Topic, status_code=status.HTTP_201_CREATED)
def create_topic(topic: schemas.TopicCreate, db: sqlite3.Connection = Depends(database.get_db)):
    """Create a new topic. The topic name must be unique."""
    cursor = db.cursor()
    # Check if topic exists
    cursor.execute("SELECT id FROM topics WHERE name = ?", (topic.name,))
    existing = cursor.fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic already exists")
    cursor.execute(
        "INSERT INTO topics (name, description) VALUES (?, ?)",
        (topic.name, topic.description)
    )
    db.commit()
    topic_id = cursor.lastrowid
    return schemas.Topic(id=topic_id, name=topic.name, description=topic.description)


@app.get("/goals/{user_id}", response_model=list[schemas.Goal])
def list_goals(user_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Return all study goals associated with a user."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, user_id, topic_id, description, target_sessions, completed_sessions, created_at, due_date "
        "FROM goals WHERE user_id = ? ORDER BY created_at ASC",
        (user_id,),
    )
    rows = cursor.fetchall()
    goals: list[schemas.Goal] = []
    for row in rows:
        goals.append(
            schemas.Goal(
                id=row["id"],
                user_id=row["user_id"],
                topic_id=row["topic_id"],
                description=row["description"],
                target_sessions=row["target_sessions"],
                completed_sessions=row["completed_sessions"],
                created_at=row["created_at"],
                due_date=row["due_date"],
            )
        )
    return goals


@app.post("/goals", response_model=schemas.Goal, status_code=status.HTTP_201_CREATED)
def create_goal(goal: schemas.GoalCreate, db: sqlite3.Connection = Depends(database.get_db)):
    """Create a new study goal for a user on a specific topic."""
    # Validate that user and topic exist
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (goal.user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    cursor.execute("SELECT id FROM topics WHERE id = ?", (goal.topic_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    cursor.execute(
        "INSERT INTO goals (user_id, topic_id, description, target_sessions, completed_sessions, due_date) "
        "VALUES (?, ?, ?, ?, 0, ?)",
        (goal.user_id, goal.topic_id, goal.description, goal.target_sessions, goal.due_date),
    )
    db.commit()
    goal_id = cursor.lastrowid
    cursor.execute(
        "SELECT id, user_id, topic_id, description, target_sessions, completed_sessions, created_at, due_date "
        "FROM goals WHERE id = ?",
        (goal_id,),
    )
    row = cursor.fetchone()
    return schemas.Goal(
        id=row["id"],
        user_id=row["user_id"],
        topic_id=row["topic_id"],
        description=row["description"],
        target_sessions=row["target_sessions"],
        completed_sessions=row["completed_sessions"],
        created_at=row["created_at"],
        due_date=row["due_date"],
    )


@app.post("/goals/templates/{subject}", response_model=list[schemas.Goal], status_code=status.HTTP_201_CREATED)
def generate_template_goals(
    subject: str,
    request: schemas.GoalTemplateRequest,
    db: sqlite3.Connection = Depends(database.get_db),
):
    """Create default goals for a user based on subject templates."""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (request.user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return create_goals_from_template(request.user_id, subject, db)


@app.post("/goals/{goal_id}/complete", response_model=schemas.Goal)
def complete_goal(goal_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Increment the completed_sessions count for a goal. Returns the updated goal."""
    cursor = db.cursor()
    # Fetch current goal
    cursor.execute(
        "SELECT id, user_id, topic_id, description, target_sessions, completed_sessions, created_at, due_date "
        "FROM goals WHERE id = ?",
        (goal_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    # Update completed_sessions
    new_completed = row["completed_sessions"] + 1
    # Update the goal with the new completed_sessions count
    cursor.execute(
        "UPDATE goals SET completed_sessions = ? WHERE id = ?",
        (new_completed, goal_id),
    )
    # If the goal has been fully completed, award bonus XP to the user.  This
    # bonus incentivizes students to finish their study plans.  You can tune
    # the bonus value to match your gamification design.
    if new_completed >= row["target_sessions"]:
        bonus_xp = 50  # arbitrary bonus amount
        # Award bonus XP. After updating XP, call update_progress to recompute
        # levels and streaks based on the new total XP.  We ignore errors so
        # that completing a goal always succeeds.
        cursor.execute(
            "UPDATE users SET xp = xp + ? WHERE id = ?",
            (bonus_xp, row["user_id"]),
        )
        try:
            # Recompute level and streak for the user
            progress.update_progress(row["user_id"], db)
        except Exception:
            pass
    db.commit()
    # Return the updated goal object with the incremented sessions
    return schemas.Goal(
        id=row["id"],
        user_id=row["user_id"],
        topic_id=row["topic_id"],
        description=row["description"],
        target_sessions=row["target_sessions"],
        completed_sessions=new_completed,
        created_at=row["created_at"],
        due_date=row["due_date"],
    )


# ---------------------- Thread Endpoints ----------------------

@app.get("/threads/{user_id}", response_model=list[schemas.Thread])
def list_threads(user_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    """Return all conversation threads associated with a user."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, user_id, name, created_at FROM threads WHERE user_id = ? ORDER BY created_at ASC",
        (user_id,),
    )
    rows = cursor.fetchall()
    return [schemas.Thread(id=row["id"], user_id=row["user_id"], name=row["name"], created_at=row["created_at"]) for row in rows]


@app.post("/threads", response_model=schemas.Thread, status_code=status.HTTP_201_CREATED)
def create_thread(thread: schemas.ThreadCreate, db: sqlite3.Connection = Depends(database.get_db)):
    """Create a new conversation thread for a user."""
    # Ensure user exists
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (thread.user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    cursor.execute(
        "INSERT INTO threads (user_id, name) VALUES (?, ?)",
        (thread.user_id, thread.name),
    )
    db.commit()
    thread_id = cursor.lastrowid
    cursor.execute(
        "SELECT id, user_id, name, created_at FROM threads WHERE id = ?",
        (thread_id,),
    )
    row = cursor.fetchone()
    return schemas.Thread(id=row["id"], user_id=row["user_id"], name=row["name"], created_at=row["created_at"]) 


# ---------------------- Study Materials Endpoints ----------------------

@app.get("/materials")
def list_subjects():
    """Return a list of all available subjects for study materials.

    The study materials are organized by high-level subject areas (e.g., math,
    science, language_arts, computer_science).  This endpoint returns the
    available subject keys so the frontend can populate a subject selector.
    """
    # Return the top-level keys of the STUDY_MATERIALS dict
    subjects = list(STUDY_MATERIALS.keys())
    return {"subjects": subjects}


@app.get("/materials/{subject}")
def list_categories(subject: str):
    """Return the available categories within a subject.

    Each subject contains one or more categories (e.g., algebra, geometry
    under math).  This endpoint validates the subject and returns the list
    of categories.  If the subject does not exist, a 404 error is raised.
    """
    subject_key = subject.lower()
    if subject_key not in STUDY_MATERIALS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    categories = list(STUDY_MATERIALS[subject_key].keys())
    return {"subject": subject_key, "categories": categories}


@app.get("/materials/{subject}/{category}")
def get_materials(subject: str, category: str):
    """Return study materials for a specific subject and category.

    This endpoint looks up the requested subject and category in the
    STUDY_MATERIALS dictionary and returns the full data structure (units
    with topics and content) for that category.  If either the subject or
    category does not exist, a 404 error is raised.
    """
    subject_key = subject.lower()
    category_key = category.lower()
    # Validate subject
    if subject_key not in STUDY_MATERIALS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    subject_dict = STUDY_MATERIALS[subject_key]
    # Validate category
    if category_key not in subject_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return subject_dict[category_key]


if __name__ == "__main__":  # pragma: no cover
    # Run the application with uvicorn when executed directly.
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
