import { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext();

export function AppProvider({ children }) {
  const [userId, setUserId] = useState(() => localStorage.getItem('userId'));
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [currentThreadId, setCurrentThreadId] = useState(() => localStorage.getItem('currentThreadId'));
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const [xp, setXp] = useState(() => Number(localStorage.getItem('xp')) || 0);
  const [level, setLevel] = useState(() => Number(localStorage.getItem('level')) || 1);
  const [streak, setStreak] = useState(() => Number(localStorage.getItem('streak')) || 0);

  useEffect(() => {
    localStorage.setItem('userId', userId || '');
    localStorage.setItem('token', token || '');
    localStorage.setItem('currentThreadId', currentThreadId || '');
    localStorage.setItem('theme', theme);
    localStorage.setItem('xp', xp);
    localStorage.setItem('level', level);
    localStorage.setItem('streak', streak);
    document.body.className = theme;
  }, [userId, token, currentThreadId, theme, xp, level, streak]);

  const toggleTheme = () => setTheme((t) => (t === 'light' ? 'dark' : 'light'));

  return (
    <AppContext.Provider value={{
      userId, setUserId,
      token, setToken,
      currentThreadId, setCurrentThreadId,
      theme, toggleTheme,
      xp, setXp,
      level, setLevel,
      streak, setStreak,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export const useAppContext = () => useContext(AppContext);
