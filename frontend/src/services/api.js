const BASE_URL = 'http://localhost:8000';

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

export const register = (data) => request('/register', { method: 'POST', body: JSON.stringify(data) });
export const login = (data) => request('/login', { method: 'POST', body: JSON.stringify(data) });
export const fetchThreads = (userId) => request(`/threads/${userId}`);
export const fetchHistory = (userId, threadId) => request(`/history/${userId}/${threadId}`);
export const sendChatMessage = (userId, threadId, message) =>
  request('/chat', { method: 'POST', body: JSON.stringify({ userId, threadId, message }) });
export const fetchDashboard = (userId) => request(`/dashboard/${userId}`);
export const fetchGoals = (userId) => request(`/goals/${userId}`);
export const fetchMaterials = (subject, category) => {
  const path = category ? `/materials/${subject}/${category}` : `/materials/${subject}`;
  return request(path);
};
