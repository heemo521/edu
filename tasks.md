# MVP Development Tasks

- [x] **Initialize project repository and directory structure**
 - [x] **Set up backend framework (e.g., FastAPI)**
 - [x] **Implement user registration and authentication**
 - [x] **Create chat API endpoint for tutoring**
 - [x] **Implement AI tutor stub (placeholder for LLM integration)**
 - [x] **Implement progress tracking database and models**
 - [x] **Develop parent/teacher dashboard endpoints**
 - [x] **Integrate subscription management (stub)**
 - [x] **Build simple frontend interface (HTML/CSS/JS)**
 - [x] **Write tests and perform QA**

## Post-MVP Polish Tasks

- [x] **Add user info endpoint integration and display**
  - Fetch user details (username, subscription status, message count) after login and display in the header.
- [x] **Implement sign-out functionality**
  - Reset user state, hide authenticated sections, and show a success notification.
- [x] **Improve UI/UX styling**
  - Introduce CSS variables and dark/light themes with persistence.
  - Add a header with user info, sign-out and theme toggle buttons.
  - Style chat messages with different backgrounds for user and tutor messages and include timestamps.
- [x] **Create notification system**
  - Provide unified success/error messages that appear briefly and then disappear.
- [x] **Enable Enter key to send messages**
  - Attach a keypress handler to chat input for convenience.
- [x] **Enhance dashboard layout**
  - Organize buttons and summary/history sections for better readability.
- [ ] **Further enhancements**
  - Consider adding search in chat history, improved AI responses, or more robust summary features in future iterations.

## Frontend Refinements

- [x] **Combine login and registration into a unified auth card with tabs**
  - Added an authentication section with “Login” and “Register” tabs to toggle between forms for a cleaner UI.
- [x] **Add decorative background**
  - Generated and integrated an abstract gradient image as the page background for a modern look.
- [x] **Style history and summary panels**
  - Made the history and summary sections card-like with borders, padding, and scrollable areas.
- [x] **Persist session and theme across page reloads**
    - User ID and theme preference are saved to localStorage and restored on page load so users stay logged in and their dark/light theme choice persists.

## Sprint 1: Feature Enhancements

 - [x] **Voice input for chat**
  - Added a microphone toggle button in the chat interface and implemented speech recognition using the Web Speech API.
  - Captures speech, transcribes it to text and automatically sends messages; falls back gracefully when unsupported.

 - [x] **Text-to-speech (TTS) for tutor responses**
  - Added a toggle to enable or disable speech synthesis for tutor messages using the browser’s SpeechSynthesis API.
  - AI responses can now be read aloud when TTS is enabled.

 - [x] **Enhanced dashboard and progress tracking**
  - Updated the backend dashboard endpoint to include distinct session counts and badge milestones.
  - Frontend displays these metrics and badges.

 - [x] **Persist session and theme across reloads**
  - Implemented storage of user ID and theme preference in `localStorage` and restore them on page load so users remain logged in and maintain their theme choice.

## Sprint 2: Gamification and Progress

- [x] **XP-based Level System**
  - Added `xp`, `level`, `streak_count` and `last_streak_date` columns to the `users` table via migrations in `database.py`.
  - Created a `progress.py` utility module with `update_progress` to handle XP accumulation, level computation and daily streak updates.
  - Updated the `chat` endpoint to grant XP and update user progress after each message.
  - Expanded `get_user_info` and `get_dashboard` endpoints to return XP, level and streak information.
  - Added comprehensive unit tests in `test_progress.py` to verify XP/level thresholds and streak behaviour.

- [x] **Daily Streak Counter**
  - Implemented logic in `update_progress` to increment a streak when users interact on consecutive days and reset when a day is missed.
  - Added streak metrics to dashboard and user info responses.
  - Included tests to ensure streaks increment and reset correctly across simulated dates.

- [ ] **Visual Progress Indicators**
  - [x] Added progress bar and progress info display to dashboard showing level, XP, streak and a dynamic progress bar based on XP thresholds.
  - [x] Added a toast-like banner notification that displays when a user levels up. The banner appears at the top of the page with a celebratory message and fades out after a few seconds. Further visual animations (e.g. confetti) could be added in later sprints.

## Sprint 3: Tutor Agent & Study Goals

- [x] **Topic Management Backend**
  - Created database tables and schemas for topics.
  - Added API endpoints to list all topics and create new topics.
- [x] **Study Goal Backend**
  - Created database tables and schemas for goals (user-specific targets for a given topic).
  - Added API endpoints to create goals, list goals by user, and increment completed sessions.
        - [x] **Integrate Goals with Progress System**
          - Updated the `complete_goal` endpoint to award bonus XP when a user finishes all target sessions for a goal.  The backend now increments the user's XP and recomputes their level/streak, providing additional motivation for completing study plans.
- [x] **Front‑End Topic and Goal UI**
  - Added UI components to choose a topic and set a study goal (description, target sessions, due date).
  - Displayed the list of active goals and progress (sessions completed vs. target) in the dashboard.
        - [x] **Agent Integration with Local LLM**
          - Replaced the tutor stub with a function that calls a locally running language model via the Ollama API. The integration uses the `OLLAMA_BASE_URL` and `LLAMA_MODEL` environment variables to connect to an existing Ollama server (e.g. `http://localhost:11434`) and send prompts to models such as `llama3`【797144351285286†L84-L97】.
          - Added the `requests` dependency to the backend requirements and implemented a fallback heuristic when the LLM is unavailable.
          - To use this feature, install and run Ollama on your host machine and download the desired model (e.g. run `ollama run llama3`). The backend will connect to this local server automatically.

- [x] **Study Materials Backend & API**
  - Added a `data/study_materials.json` file containing structured curricula for core subjects (math, science, language arts, computer science) and their subtopics.
  - Loaded this file at application startup and exposed new API endpoints:
    - `GET /materials` returns a list of available subjects.
    - `GET /materials/{subject}` returns the categories (e.g. algebra, biology) within a subject.
    - `GET /materials/{subject}/{category}` returns detailed units and topics for the chosen category.
  - Designed the endpoints to raise a 404 when an invalid subject or category is requested.

        - [x] **Study Materials Frontend Integration**
  - Added a "Study Materials" section to the dashboard with dropdowns for subject and category selection.
  - Populated the subject and category selects by calling the new endpoints and displayed units and topics with summaries when a category is chosen.
  - This section is only visible when a user is logged in and loads automatically on login or session restore.
  - Prepopulated study goals remain separate, but the materials can inform users before setting goals.

- [ ] **Self‑Improving Study Materials (Future)**
  - TODO: Implement a feedback mechanism allowing students to rate the helpfulness of a topic or suggest improvements.
  - TODO: Aggregate feedback to adjust content difficulty or prioritize topics based on common struggles.
  - TODO: Integrate user feedback into the AI tutor’s responses via prompt adjustments or data-driven updates.

        - [ ] **Study Plan & Goal Setting**
          - TODO: Allow users to set learning goals (e.g., topics, number of sessions) and generate personalized study plans.
          - TODO: Track progress against these plans and display completion statistics.

## Sprint 4: Context & Threads

- [x] **Threaded Conversations & Context Summarization**
  - Added a `threads` table and updated the `messages` table in the database to associate messages with a specific thread.
  - Created API endpoints to list threads for a user and create new threads.
  - Added context building in the backend that summarizes active goals and the last five messages in a thread when sending a prompt to the tutor.
  - Modified the `chat` endpoint to accept a `thread_id` and include context in LLM prompts.
  - Added logic to insert a default "General" thread upon user registration.
  - Implemented frontend support for multiple threads, including thread tabs and a “New Thread” button.
  - Chat messages are now counted per thread and a context warning is displayed when the number of messages exceeds a threshold, informing users that older messages may be summarized.
  - Added `thread_id` parameter to chat requests and thread-aware history loading.

## Final Touches and Launch Checklist

- [ ] **Context Memory Injection & Summaries**
  - Enhance `build_context` to include a summary line when conversations exceed the context window.  This is partially implemented by noting omitted messages, but future versions should automatically summarise older messages into a compact representation and store these summaries for reuse.  The front‑end should warn users when summarisation occurs and provide a link to view the full history.
  - Introduce a `summaries` table to persist conversation summaries for each thread and update it when summarisation happens.

- [ ] **Goal-Based XP Bonuses**
  - Modify `progress.update_progress` or the `complete_goal` endpoint to award bonus XP when a user completes a goal session.  This encourages students to follow through on their study plans and provides an additional gamification loop.

- [ ] **Study Plan & Intelligent Scheduling**
  - Allow users to set comprehensive study plans (topics, number of sessions, desired completion dates) and display these plans alongside goals.  Provide reminders and calendar integration to keep students on track.
  - Generate suggested session cadences based on user availability and target completion dates.

- [ ] **Feedback & Self‑Improving Materials**
  - Implement a feedback endpoint and UI so students can rate the usefulness of each topic or lesson.  Store feedback in a new table and periodically aggregate it to identify topics that need refinement or expansion.
  - Adjust the AI tutor’s prompt based on common feedback (e.g., “students often struggle with factoring quadratics; provide extra hints”).

- [ ] **Agent Prompt Finalisation**
  - Finalise the system prompt for the local LLM.  It should include the user’s goals, the current thread’s context summary, and guidelines such as using the Socratic method, encouraging independent thinking, and never revealing sensitive information.
  - Parameterise the prompt so it can be easily updated without code changes.

- [ ] **UI/UX Polish**
  - Improve visual hierarchy and responsiveness on mobile.  Use card layouts, consistent spacing and subtle animations for message sending/receiving and level‑up events.
  - Highlight the active thread tab and clearly differentiate between study plan tasks, chat messages, and materials.
  - Add confirmation dialogs for destructive actions (e.g. deleting a thread or goal).

- [ ] **Deployment & Documentation**
  - Provide a comprehensive `README.md` with setup instructions (requirements, running the server locally, connecting to an Ollama model, using Docker) and troubleshooting tips.
  - Supply a sample `.env.example` file specifying environment variables such as `OLLAMA_BASE_URL` and `LLAMA_MODEL`.
  - Optionally create a `docker-compose.yml` file to orchestrate the API, front‑end and model server for easier deployment.

- [ ] **Testing & Quality Assurance**
  - Write additional unit tests to cover new functionality (threads, goals, materials).  Aim for >60 % code coverage on the backend.
  - Create basic end‑to‑end tests (e.g. using Playwright or Selenium) to simulate user flows: registration, login, thread creation, chatting, setting goals, browsing materials, and receiving AI responses.
  - Conduct manual QA to ensure cross-browser compatibility and responsive design.


## Deployment and Containerization

- [x] **Create a Dockerfile for containerized deployment**
  - Added a `Dockerfile` that uses a Python slim base image, installs the backend requirements and `uvicorn`, copies the backend and frontend code, exposes ports 8000 and 3000, and runs both the FastAPI backend and a simple static file server for the frontend in a single container.
- [ ] **Provide docker-compose.yml (optional)**
  - Consider adding a docker-compose file to orchestrate services if scaling beyond a single container is required.
