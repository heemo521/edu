// JavaScript functions for AI Tutoring MVP frontend

let currentUserId = null;
let currentUserName = '';
// Track the currently selected thread. Each thread represents a separate study
// session, allowing the user to maintain multiple conversations with the
// tutoring agent. When no thread is selected, the chat interface will be
// disabled.
let currentThreadId = null;
// Count the number of messages exchanged in the current thread. This is used
// to warn the user when the context grows large and older messages may be
// summarized by the backend. Each user or tutor message increments this
// count.
let currentMessagesCount = 0;
// Threshold after which a context summarization warning is displayed. Once
// the number of messages in a thread exceeds this value, the UI shows a
// warning that some earlier messages may be summarized. Adjust as needed.
const CONTEXT_THRESHOLD = 10;
// Voice and text-to-speech state
let voiceEnabled = false;
let ttsEnabled = false;
let recognition = null;
const apiBase = 'http://localhost:8000';
// Mapping of topic names to IDs loaded from the backend. Used when submitting
// feedback on study materials to associate ratings with a specific topic.
const topicIdMap = {};
let currentMaterialTopicId = null;

// XP thresholds used to compute progress towards the next level. The index of the
// threshold corresponds to the level number. For example, level 1 requires
// XP_THRESHOLDS[1] XP to reach, level 2 requires XP_THRESHOLDS[2], etc.
const XP_THRESHOLDS = [0, 100, 250, 500, 1000, 2000];

// Default number of sessions for each topic. These values are based on
// common tutoring curricula to help users quickly set reasonable study
// goals without having to think from scratch. Topics not listed here
// will default to 5 sessions. Due dates will be set automatically
// approximately four weeks from goal creation.
const DEFAULT_SESSIONS = {
    'Elementary Math': 5,
    'Algebra I': 10,
    'Algebra II': 10,
    'Geometry': 8,
    'Pre-Calculus': 8,
    'Calculus': 10,
    'Statistics': 7,
    'Biology': 6,
    'Chemistry': 6,
    'Physics': 6,
    'Reading & Literature': 5,
    'Grammar & Writing': 5,
    'Spanish Language': 5,
    'French Language': 5,
    'Python Programming': 5,
    'Java Programming': 6,
    'U.S. History': 5,
    'World History': 5,
    'Study Skills & Time Management': 4,
    'SAT/ACT Prep': 8
};

// -------------------------- Study Materials --------------------------

/**
 * Fetch a list of available subjects for study materials and populate the
 * subject select element. When a subject is selected, triggers loading
 * of categories and materials.
 */
async function loadSubjects() {
    const subjectSelect = document.getElementById('material-subject');
    const categorySelect = document.getElementById('material-category');
    if (!subjectSelect || !categorySelect) return;
    subjectSelect.innerHTML = '';
    categorySelect.innerHTML = '';
    try {
        const res = await fetch(`${apiBase}/materials`);
        const data = await res.json();
        if (res.ok && Array.isArray(data.subjects)) {
            // Populate subject select
            data.subjects.forEach((sub) => {
                const opt = document.createElement('option');
                opt.value = sub;
                opt.textContent = sub;
                subjectSelect.appendChild(opt);
            });
            // Attach change listener
            subjectSelect.removeEventListener('change', onSubjectChange);
            subjectSelect.addEventListener('change', onSubjectChange);
            // Initialize categories for the first subject
            if (subjectSelect.options.length > 0) {
                subjectSelect.selectedIndex = 0;
                await loadCategories();
            }
        }
    } catch (err) {
        console.error('Error loading subjects:', err);
    }
}

/**
 * Handle subject change event by loading categories for the selected subject.
 */
async function onSubjectChange() {
    await loadCategories();
}

/**
 * Fetch categories for the selected subject and populate the category select.
 * Automatically loads materials for the first category.
 */
async function loadCategories() {
    const subjectSelect = document.getElementById('material-subject');
    const categorySelect = document.getElementById('material-category');
    if (!subjectSelect || !categorySelect) return;
    const subject = subjectSelect.value;
    categorySelect.innerHTML = '';
    try {
        const res = await fetch(`${apiBase}/materials/${encodeURIComponent(subject)}`);
        const data = await res.json();
        if (res.ok && Array.isArray(data.categories)) {
            data.categories.forEach((cat) => {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                categorySelect.appendChild(opt);
            });
            // Attach change listener
            categorySelect.removeEventListener('change', onCategoryChange);
            categorySelect.addEventListener('change', onCategoryChange);
            // Load materials for the first category
            if (categorySelect.options.length > 0) {
                categorySelect.selectedIndex = 0;
                await loadMaterials();
            }
        }
    } catch (err) {
        console.error('Error loading categories:', err);
    }
}

/**
 * Handle category change event by loading materials for the selected subject
 * and category.
 */
async function onCategoryChange() {
    await loadMaterials();
}

/**
 * Fetch study materials for the selected subject and category and display them
 * in the materials content area. Displays units and topics with their
 * summaries.
 */
async function loadMaterials() {
    const subjectSelect = document.getElementById('material-subject');
    const categorySelect = document.getElementById('material-category');
    const contentEl = document.getElementById('materials-content');
    if (!subjectSelect || !categorySelect || !contentEl) return;
    const subject = subjectSelect.value;
    const category = categorySelect.value;
    contentEl.textContent = 'Loading...';
    try {
        const res = await fetch(`${apiBase}/materials/${encodeURIComponent(subject)}/${encodeURIComponent(category)}`);
        const data = await res.json();
        if (res.ok && data.units) {
            // Build HTML listing units and topics
            let html = '';
            data.units.forEach((unit) => {
                html += `<h4>${unit.name}</h4>`;
                unit.topics.forEach((topic) => {
                    html += `<p><strong>${topic.name}:</strong> ${topic.content}</p>`;
                });
            });
            contentEl.innerHTML = html;

            // Determine the topic ID based on the material title so feedback can
            // be associated with the correct topic.
            currentMaterialTopicId = null;
            if (data.title && topicIdMap[data.title]) {
                currentMaterialTopicId = topicIdMap[data.title];
            }

            // Append feedback widget if user is logged in and topic ID known
            if (currentUserId && currentMaterialTopicId) {
                const widget = document.createElement('div');
                widget.id = 'feedback-widget';
                widget.innerHTML = `\n                    <h4>Rate this material</h4>\n                    <label>Rating:\n                        <select id="feedback-rating">\n                            <option value="1">1</option>\n                            <option value="2">2</option>\n                            <option value="3">3</option>\n                            <option value="4">4</option>\n                            <option value="5" selected>5</option>\n                        </select>\n                    </label>\n                    <label>Comments:\n                        <input type="text" id="feedback-comments">\n                    </label>\n                    <button onclick="submitFeedback()">Submit Feedback</button>\n                `;
                contentEl.appendChild(widget);
            }
        } else {
            contentEl.textContent = 'No materials found.';
        }
    } catch (err) {
        contentEl.textContent = 'Error loading materials';
    }
}

/**
 * Submit user feedback for the currently viewed material.
 */
async function submitFeedback() {
    if (!currentUserId || !currentMaterialTopicId) return;
    const ratingEl = document.getElementById('feedback-rating');
    const commentsEl = document.getElementById('feedback-comments');
    if (!ratingEl) return;
    const rating = parseInt(ratingEl.value, 10);
    const comments = commentsEl ? commentsEl.value : '';
    try {
        const res = await fetch(`${apiBase}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId, topic_id: currentMaterialTopicId, rating, comments })
        });
        const data = await res.json();
        if (res.ok) {
            showNotification('Feedback submitted!', 'success');
            ratingEl.value = '5';
            if (commentsEl) commentsEl.value = '';
        } else {
            showNotification(data.detail || 'Failed to submit feedback', 'error');
        }
    } catch (err) {
        showNotification('Error connecting to server', 'error');
    }
}

/**
 * Update the goal creation form with sensible defaults based on the selected
 * topic. Sets the number of sessions, description and due date (4 weeks
 * from today) automatically. This reduces friction for users and ensures
 * consistent study plans.
 */
function updateGoalDefaults() {
    const topicSelect = document.getElementById('goal-topic');
    const sessionsEl = document.getElementById('goal-sessions');
    const descriptionEl = document.getElementById('goal-description');
    const dueEl = document.getElementById('goal-due');
    if (!topicSelect || !sessionsEl || !descriptionEl || !dueEl) return;
    const selectedText = topicSelect.options[topicSelect.selectedIndex]?.textContent;
    if (!selectedText) return;
    const defaultSessions = DEFAULT_SESSIONS[selectedText] || 5;
    sessionsEl.value = defaultSessions;
    // Only update description if empty or previously auto-filled
    if (descriptionEl.value.trim() === '' || descriptionEl.dataset.autofill === 'true') {
        descriptionEl.value = `${selectedText} Study Plan`;
        descriptionEl.dataset.autofill = 'true';
    }
    // Set due date to 4 weeks from today
    const today = new Date();
    const dueDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 28);
    dueEl.value = dueDate.toISOString().split('T')[0];
}

/**
 * Display a temporary level-up notification to the user.
 * Shows a banner at the top of the page indicating the new level and
 * automatically hides it after a few seconds.
 * @param {number} newLevel The level the user has just achieved.
 */
function showLevelUp(newLevel) {
    const notifEl = document.getElementById('level-notification');
    if (!notifEl) return;
    notifEl.textContent = `Level Up! You reached Level ${newLevel}!`;
    notifEl.style.display = 'block';
    // Force reflow to ensure CSS transition runs
    void notifEl.offsetWidth;
    notifEl.style.opacity = '1';
    // Hide after 5 seconds
    setTimeout(() => {
        notifEl.style.opacity = '0';
        setTimeout(() => {
            notifEl.style.display = 'none';
        }, 500);
    }, 5000);
}

// -------------------------- Thread Management --------------------------

/**
 * Fetch all conversation threads for the current user and populate the
 * thread tabs in the chat interface. When threads are loaded, the
 * function also selects the first thread by default if none is selected.
 */
async function loadThreads() {
    if (!currentUserId) return;
    try {
        const res = await fetch(`${apiBase}/threads/${currentUserId}`);
        const data = await res.json();
        if (res.ok && Array.isArray(data) && data.length > 0) {
            const tabsEl = document.getElementById('threads-tabs');
            if (tabsEl) {
                tabsEl.innerHTML = '';
                data.forEach((thread) => {
                    const btn = document.createElement('button');
                    btn.textContent = thread.name;
                    btn.className = 'thread-tab';
                    if (thread.id === currentThreadId) {
                        btn.classList.add('active');
                    }
                    btn.onclick = () => switchThread(thread.id);
                    tabsEl.appendChild(btn);
                });
            }
            // If no thread is currently selected, pick the first one
            if (!currentThreadId) {
                currentThreadId = data[0].id;
                // Load history for the first thread
                await loadHistory();
            }
        }
    } catch (err) {
        console.error('Error loading threads:', err);
    }
}

/**
 * Create a new conversation thread for the current user. Prompts the user
 * for a thread name, sends a POST request to the backend, and then
 * reloads the thread list to display the new thread. Newly created threads
 * become the active thread automatically.
 */
async function createThread() {
    if (!currentUserId) return;
    const name = prompt('Enter a name for the new thread');
    if (!name || name.trim() === '') return;
    try {
        const res = await fetch(`${apiBase}/threads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId, name: name.trim() })
        });
        const data = await res.json();
        if (res.ok) {
            // Set the newly created thread as active
            currentThreadId = data.id;
            // Clear chat area and reset message count
            document.getElementById('chat-messages').innerHTML = '';
            currentMessagesCount = 0;
            // Reload threads to show the new thread in the tabs
            await loadThreads();
            showNotification('New thread created!', 'success');
        } else {
            showNotification(data.detail || 'Failed to create thread', 'error');
        }
    } catch (err) {
        showNotification('Error connecting to server', 'error');
    }
}

/**
 * Switch to a different conversation thread. Clears the chat messages,
 * loads the history for the selected thread, updates the active tab
 * styling, and resets the context warning state.
 * @param {number} threadId The ID of the thread to switch to.
 */
async function switchThread(threadId) {
    if (currentThreadId === threadId) return;
    currentThreadId = threadId;
    // Reset message count and hide context warning
    currentMessagesCount = 0;
    updateContextWarning();
    // Clear chat messages display
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) chatContainer.innerHTML = '';
    // Reload history for the selected thread
    await loadHistory();
    // Refresh threads to highlight active tab
    await loadThreads();
}

/**
 * Update the context warning display based on the number of messages in
 * the current thread. If the number of messages exceeds the threshold,
 * display a warning to the user that earlier messages may be summarized.
 */
function updateContextWarning() {
    const warningEl = document.getElementById('context-warning');
    if (!warningEl) return;
    if (currentMessagesCount > CONTEXT_THRESHOLD) {
        warningEl.style.display = '';
    } else {
        warningEl.style.display = 'none';
    }
}

// -------------------------- Topics & Goals ---------------------------

/**
 * Fetch all available topics from the server and populate the topic select
 * element used when creating a new study goal.
 */
async function loadTopics() {
    try {
        const res = await fetch(`${apiBase}/topics`);
        const data = await res.json();
        if (res.ok) {
            const select = document.getElementById('goal-topic');
            if (select) {
                // Clear existing options
                select.innerHTML = '';
                // Reset local topic cache and populate select options
                Object.keys(topicIdMap).forEach((key) => delete topicIdMap[key]);
                data.forEach((topic) => {
                    topicIdMap[topic.name] = topic.id;
                    const option = document.createElement('option');
                    option.value = topic.id;
                    option.textContent = topic.name;
                    select.appendChild(option);
                });
                // Attach change handler to update defaults when user selects a topic
                select.removeEventListener('change', updateGoalDefaults);
                select.addEventListener('change', updateGoalDefaults);
                // Populate default fields based on the first topic
                if (select.options.length > 0) {
                    select.selectedIndex = 0;
                    updateGoalDefaults();
                }
            }
        }
    } catch (err) {
        console.error('Error loading topics:', err);
    }
}

/**
 * Fetch and display the current user's study goals. Each goal shows its
 * description, progress (completed vs target) and includes a button to mark
 * a session as completed.
 */
async function loadGoals() {
    if (!currentUserId) return;
    const goalsList = document.getElementById('goals-list');
    if (!goalsList) return;
    goalsList.textContent = 'Loading...';
    try {
        const res = await fetch(`${apiBase}/goals/${currentUserId}`);
        const data = await res.json();
        if (res.ok) {
            goalsList.innerHTML = '';
            if (data.length === 0) {
                goalsList.innerHTML = '<p>No goals set. Create one above!</p>';
            } else {
                data.forEach((goal) => {
                    const div = document.createElement('div');
                    div.style.marginBottom = '10px';
                    const progressText = `${goal.completed_sessions} / ${goal.target_sessions}`;
                    const due = goal.due_date ? ` (due ${goal.due_date})` : '';
                    div.innerHTML = `<strong>${goal.description || 'Goal'}:</strong> ${progressText}${due}`;
                    // Button to mark a session complete
                    const btn = document.createElement('button');
                    btn.textContent = 'Complete Session';
                    btn.onclick = async () => {
                        await completeGoal(goal.id);
                        // reload goals and dashboard to update progress/XP
                        loadGoals();
                        loadDashboard();
                    };
                    // Disable button if goal already reached
                    if (goal.completed_sessions >= goal.target_sessions) {
                        btn.disabled = true;
                    }
                    div.appendChild(btn);
                    goalsList.appendChild(div);
                });
            }
        } else {
            goalsList.innerHTML = `<p>${data.detail || 'Failed to load goals'}</p>`;
        }
    } catch (err) {
        goalsList.textContent = 'Error connecting to server';
    }
}

/**
 * Create a new study goal based on user input from the form. Sends a POST
 * request to the server and then reloads the goals list and dashboard.
 */
async function createGoal() {
    if (!currentUserId) return;
    const topicSelect = document.getElementById('goal-topic');
    const descriptionEl = document.getElementById('goal-description');
    const sessionsEl = document.getElementById('goal-sessions');
    const dueEl = document.getElementById('goal-due');
    const topicId = parseInt(topicSelect.value);
    const description = descriptionEl.value.trim();
    const targetSessions = parseInt(sessionsEl.value);
    const dueDate = dueEl.value ? dueEl.value : null;
    try {
        const res = await fetch(`${apiBase}/goals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                topic_id: topicId,
                description,
                target_sessions: targetSessions,
                due_date: dueDate
            })
        });
        const data = await res.json();
        if (res.ok) {
            showNotification('Goal created successfully!', 'success');
            descriptionEl.value = '';
            sessionsEl.value = '5';
            dueEl.value = '';
            loadGoals();
        } else {
            showNotification(data.detail || 'Failed to create goal', 'error');
        }
    } catch (err) {
        showNotification('Error connecting to server', 'error');
    }
}

/**
 * Mark a study session as completed for a given goal ID.
 */
async function completeGoal(goalId) {
    try {
        const res = await fetch(`${apiBase}/goals/${goalId}/complete`, {
            method: 'POST'
        });
        const data = await res.json();
        if (!res.ok) {
            showNotification(data.detail || 'Failed to complete goal session', 'error');
        }
    } catch (err) {
        showNotification('Error connecting to server', 'error');
    }
}

// Show notifications (success or error) in a unified manner
function showNotification(message, type = 'success') {
    const notif = document.getElementById('notification');
    if (!notif) return;
    notif.textContent = message;
    notif.className = 'notification ' + type;
    notif.style.display = 'block';
    // hide after 4 seconds
    setTimeout(() => {
        notif.style.display = 'none';
    }, 4000);
}

// Switch between login and register forms
function showAuthForm(type) {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    if (!loginTab || !registerTab || !loginForm || !registerForm) return;
    if (type === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.style.display = '';
        registerForm.style.display = 'none';
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.style.display = '';
        loginForm.style.display = 'none';
    }
}

// Toggle dark/light theme
function toggleTheme() {
    const body = document.body;
    body.classList.toggle('dark-mode');
    // Save preference
    if (body.classList.contains('dark-mode')) {
        localStorage.setItem('theme', 'dark');
    } else {
        localStorage.setItem('theme', 'light');
    }
}

// Initialize theme from local storage
document.addEventListener('DOMContentLoaded', async () => {
    // Restore theme preference
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    // Attempt to restore user session
    const savedUserId = localStorage.getItem('userId');
    const savedUsername = localStorage.getItem('username');
    if (savedUserId) {
        currentUserId = parseInt(savedUserId);
        currentUserName = savedUsername || '';
        try {
            const res = await fetch(`${apiBase}/users/${currentUserId}`);
            const data = await res.json();
            if (res.ok) {
                updateUserInfo({
                    username: data.username,
                    subscription_status: data.subscription_status,
                    message_count: data.message_count,
                });
                document.getElementById('chat-section').style.display = '';
                document.getElementById('dashboard-section').style.display = '';
                document.getElementById('auth-section').style.display = 'none';
                // attach enter handler
                const chatInput = document.getElementById('chat-input');
                if (chatInput) {
                    chatInput.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            sendMessage();
                        }
                    });
                }
                showNotification(`Welcome back, ${data.username}`, 'success');
                // Load threads and history for the restored session
                await loadThreads();
                if (currentThreadId) {
                    await loadHistory();
                }
                // Also show materials section and load subjects
                const materialsSection = document.getElementById('materials-section');
                if (materialsSection) materialsSection.style.display = '';
                loadSubjects();
            } else {
                // If session invalid, clear local storage
                localStorage.removeItem('userId');
                localStorage.removeItem('username');
            }
        } catch (err) {
            // If fetch fails, ignore and show auth
        }
    }

    // Load available topics immediately so the topic select is populated even
    // before login. This allows the goal form to be ready when the user logs in.
    loadTopics();
});

// Update user info display
function updateUserInfo({ username, subscription_status, message_count }) {
    const info = document.getElementById('user-info');
    if (!info) return;
    document.getElementById('user-name').textContent = username;
    document.getElementById('user-subscription').textContent = `Subscription: ${subscription_status}`;
    document.getElementById('user-messages').textContent = `Messages: ${message_count}`;
    info.style.display = 'flex';
    // Also show theme toggle button in header when logged in
    const themeBtn = document.getElementById('theme-button');
    if (themeBtn) themeBtn.style.display = 'none';
}

// Reset user info on sign out
function clearUserInfo() {
    const info = document.getElementById('user-info');
    if (!info) return;
    document.getElementById('user-name').textContent = '';
    document.getElementById('user-subscription').textContent = '';
    document.getElementById('user-messages').textContent = '';
    info.style.display = 'none';
    const themeBtn = document.getElementById('theme-button');
    if (themeBtn) themeBtn.style.display = '';
}

function signOut() {
    currentUserId = null;
    currentUserName = '';
    // Clear persisted session
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    // Hide sections and clear content
    document.getElementById('chat-section').style.display = 'none';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('auth-section').style.display = '';
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('history').innerHTML = '';
    document.getElementById('summary').innerHTML = '';
    clearUserInfo();
    showNotification('Signed out successfully', 'success');
}

async function register() {
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value.trim();
    const role = document.getElementById('reg-role').value.trim() || 'student';
    const resultEl = document.getElementById('reg-result');
    resultEl.textContent = '';
    try {
        const response = await fetch(`${apiBase}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });
        const data = await response.json();
        if (response.ok) {
            resultEl.textContent = `Registered successfully as ID ${data.id}`;
            showNotification('Registration successful!', 'success');
        } else {
            resultEl.textContent = data.detail || 'Registration failed';
            showNotification(data.detail || 'Registration failed', 'error');
        }
    } catch (err) {
        resultEl.textContent = 'Error connecting to server';
        showNotification('Error connecting to server', 'error');
    }
}

async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const resultEl = document.getElementById('login-result');
    resultEl.textContent = '';
    try {
        const response = await fetch(`${apiBase}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            currentUserId = data.user_id;
            currentUserName = username;
            // Persist session
            localStorage.setItem('userId', currentUserId);
            localStorage.setItem('username', currentUserName);
            resultEl.textContent = `Welcome, ${username}!`;
            // Fetch and display user info
            try {
                const infoRes = await fetch(`${apiBase}/users/${currentUserId}`);
                const infoData = await infoRes.json();
                if (infoRes.ok) {
                    updateUserInfo({
                        username: infoData.username,
                        subscription_status: infoData.subscription_status,
                        message_count: infoData.message_count
                    });
                    // Immediately load the dashboard to show progress info after login
                    loadDashboard();
                }
            } catch (err) {
                // ignore if user info fails
            }
            document.getElementById('chat-section').style.display = '';
            document.getElementById('dashboard-section').style.display = '';
            document.getElementById('auth-section').style.display = 'none';
            // Attach keypress event to chat input for Enter key
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        sendMessage();
                    }
                });
            }
            // Load threads for the user after login
            await loadThreads();
            // After loading threads, currentThreadId should be set; load history and dashboard.
            // Load history only if a thread was loaded
            if (currentThreadId) {
                await loadHistory();
            }
            // Load topics and goals for the user after login
            loadTopics();
            loadGoals();
            // Load study materials subjects and show the materials section
            const materialsSection = document.getElementById('materials-section');
            if (materialsSection) {
                materialsSection.style.display = '';
            }
            loadSubjects();
            showNotification(`Logged in as ${username}`, 'success');
        } else {
            resultEl.textContent = data.detail || 'Login failed';
            showNotification(data.detail || 'Login failed', 'error');
        }
    } catch (err) {
        resultEl.textContent = 'Error connecting to server';
        showNotification('Error connecting to server', 'error');
    }
}

async function sendMessage() {
    if (!currentUserId) {
        alert('Please log in first');
        return;
    }
    const inputEl = document.getElementById('chat-input');
    const message = inputEl.value.trim();
    if (!message) return;
    // Append user message to chat
    appendMessage('You', message, 'user');
    inputEl.value = '';
    try {
        const response = await fetch(`${apiBase}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId, message, thread_id: currentThreadId })
        });
        const data = await response.json();
        if (response.ok) {
            appendMessage('Tutor', data.response, 'tutor');
            // Increment message count by 1 for tutor reply
            currentMessagesCount++;
            updateContextWarning();
            // Reload dashboard to update progress metrics after sending a message
            loadDashboard();
        } else {
            appendMessage('System', data.detail || 'Error', 'system');
            showNotification(data.detail || 'Error', 'error');
        }
    } catch (err) {
        appendMessage('System', 'Error connecting to server', 'system');
        showNotification('Error connecting to server', 'error');
    }
}

function appendMessage(sender, text, type = 'system') {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message';
    // Determine class for styling
    if (type === 'user') div.classList.add('user');
    else if (type === 'tutor') div.classList.add('tutor');
    else div.classList.add('system');
    // Generate timestamp
    const timestamp = new Date().toLocaleTimeString();
    div.innerHTML = `<small>[${timestamp}]</small> <strong>${sender}:</strong> ${text}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    // If the message is from the tutor and TTS is enabled, speak it aloud
    if (type === 'tutor' && ttsEnabled && 'speechSynthesis' in window) {
        try {
            const utterance = new SpeechSynthesisUtterance(text);
            speechSynthesis.speak(utterance);
        } catch (err) {
            console.error('TTS error:', err);
        }
    }
    // Increment message count based on sender type. We treat each
    // user or tutor message as one unit for context sizing. System
    // messages do not count toward the context limit.
    if (type === 'user' || type === 'tutor') {
        currentMessagesCount++;
        updateContextWarning();
    }
}

// Toggle voice input on/off
function toggleVoice() {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert('Voice recognition is not supported in this browser');
        return;
    }
    voiceEnabled = !voiceEnabled;
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) voiceBtn.textContent = voiceEnabled ? 'Voice On' : 'Voice Off';
    if (voiceEnabled) {
        startVoiceRecognition();
    } else {
        stopVoiceRecognition();
    }
}

// Start speech recognition and handle results
function startVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.continuous = true;
    recognition.onresult = (event) => {
        if (!voiceEnabled) return;
        const transcript = event.results[event.results.length - 1][0].transcript.trim();
        // Populate chat input and send message
        const inputEl = document.getElementById('chat-input');
        if (inputEl) {
            inputEl.value = transcript;
            sendMessage();
        }
    };
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
    };
    recognition.onend = () => {
        // Restart if still enabled
        if (voiceEnabled) {
            recognition.start();
        }
    };
    recognition.start();
}

// Stop speech recognition
function stopVoiceRecognition() {
    if (recognition) {
        try {
            recognition.onend = null;
            recognition.stop();
        } catch (err) {
            console.error('Error stopping recognition:', err);
        }
    }
}

// Toggle text-to-speech on/off
function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    const ttsBtn = document.getElementById('tts-btn');
    if (ttsBtn) ttsBtn.textContent = ttsEnabled ? 'TTS On' : 'TTS Off';
}

async function loadHistory() {
    if (!currentUserId) return;
    const historyEl = document.getElementById('history');
    // If no thread is selected, don't attempt to load history
    if (!currentThreadId) {
        historyEl.textContent = 'No active thread';
        return;
    }
    historyEl.textContent = 'Loading...';
    try {
        const res = await fetch(`${apiBase}/history/${currentUserId}/${currentThreadId}`);
        const data = await res.json();
        if (res.ok) {
            historyEl.textContent = '';
            // Each history item contains a user message and a tutor response. We
            // compute the message count accordingly when loading history to
            // reflect the total number of messages in the thread.
            currentMessagesCount = data.length * 2;
            updateContextWarning();
            data.forEach(item => {
                const p = document.createElement('p');
                p.textContent = `${item.timestamp}: Q: ${item.message} | A: ${item.response}`;
                historyEl.appendChild(p);
            });
        } else {
            historyEl.textContent = data.detail || 'Failed to load history';
        }
    } catch (err) {
        historyEl.textContent = 'Error connecting to server';
    }
}

async function loadDashboard() {
    if (!currentUserId) return;
    const summaryEl = document.getElementById('summary');
    summaryEl.textContent = 'Loading...';
    try {
        const res = await fetch(`${apiBase}/dashboard/${currentUserId}`);
        const data = await res.json();
        if (res.ok) {
            let html = `<p>Total messages: ${data.total_messages}</p>`;
            html += `<p>Last activity: ${data.last_activity || 'N/A'}</p>`;
            if (data.sessions_count !== undefined) {
                html += `<p>Sessions: ${data.sessions_count}</p>`;
            }
            if (Array.isArray(data.badges) && data.badges.length > 0) {
                html += `<p>Badges:</p><ul>`;
                data.badges.forEach((b) => {
                    html += `<li>${b}</li>`;
                });
                html += `</ul>`;
            }
            summaryEl.innerHTML = html;

            // Update the progress info section for XP, level and streak.
            const progressEl = document.getElementById('progress-info');
            if (progressEl) {
                const xp = data.xp || 0;
                const level = data.level || 0;
                const streak = data.streak_count || 0;
                // Determine the current threshold and next threshold for the progress bar
                const currentThreshold = XP_THRESHOLDS[level] !== undefined ? XP_THRESHOLDS[level] : 0;
                const nextThreshold = XP_THRESHOLDS[level + 1] !== undefined ? XP_THRESHOLDS[level + 1] : XP_THRESHOLDS[XP_THRESHOLDS.length - 1];
                // Calculate progress percentage within the current level
                let progress = 0;
                if (nextThreshold > currentThreshold) {
                    progress = ((xp - currentThreshold) / (nextThreshold - currentThreshold)) * 100;
                    progress = Math.max(0, Math.min(progress, 100));
                }
                // Build HTML for progress display
                let progressHtml = `<p>Level: ${level}</p>`;
                progressHtml += `<p>XP: ${xp} / ${nextThreshold}</p>`;
                progressHtml += `<p>Daily Streak: ${streak}</p>`;
                progressHtml += `<div class="progress-container"><div class="progress-bar" style="width: ${progress}%;"></div></div>`;
                progressEl.innerHTML = progressHtml;

                // Check for level-up events. If the user's level has increased compared
                // to the last stored level in localStorage, display a level-up notification.
                const lastStored = localStorage.getItem('lastLevel');
                const lastLevel = lastStored ? parseInt(lastStored, 10) : 0;
                if (level > lastLevel) {
                    showLevelUp(level);
                }
                // Persist the current level for future comparisons
                localStorage.setItem('lastLevel', level.toString());
            }
        } else {
            summaryEl.textContent = data.detail || 'Failed to load dashboard';
        }
    } catch (err) {
        summaryEl.textContent = 'Error connecting to server';
    }
}

async function subscribe() {
    if (!currentUserId) return;
    await changeSubscription('activate');
}

async function cancelSubscription() {
    if (!currentUserId) return;
    await changeSubscription('cancel');
}

async function changeSubscription(action) {
    const summaryEl = document.getElementById('summary');
    summaryEl.textContent = '';
    try {
        const res = await fetch(`${apiBase}/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId, action })
        });
        const data = await res.json();
        if (res.ok) {
            summaryEl.innerHTML = `<p>Subscription status: ${data.status}</p><p>Start: ${data.start_date || 'N/A'}</p><p>End: ${data.end_date || 'N/A'}</p>`;
        } else {
            summaryEl.textContent = data.detail || 'Subscription change failed';
        }
    } catch (err) {
        summaryEl.textContent = 'Error connecting to server';
    }
}