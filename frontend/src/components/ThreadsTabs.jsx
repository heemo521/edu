import { useEffect, useState } from 'react';
import { fetchThreads } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';

export default function ThreadsTabs() {
  const { userId, currentThreadId, setCurrentThreadId } = useAppContext();
  const [threads, setThreads] = useState([]);

  useEffect(() => {
    if (userId) fetchThreads(userId).then(setThreads).catch(console.error);
  }, [userId]);

  return (
    <div className="threads-tabs">
      {threads.map((t) => (
        <button
          key={t.id}
          className={t.id === currentThreadId ? 'active' : ''}
          onClick={() => setCurrentThreadId(t.id)}
        >
          {t.name}
        </button>
      ))}
    </div>
  );
}
