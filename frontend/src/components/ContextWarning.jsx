import { useEffect, useState } from 'react';
import { fetchSummary } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';

export default function ContextWarning() {
  const { userId, currentThreadId } = useAppContext();
  const [hasSummary, setHasSummary] = useState(false);

  useEffect(() => {
    if (!userId || !currentThreadId) return;
    (async () => {
      try {
        const res = await fetchSummary(userId, currentThreadId);
        setHasSummary(!!res?.summary);
      } catch {
        setHasSummary(false);
      }
    })();
  }, [userId, currentThreadId]);

  if (!hasSummary) return null;

  return (
    <div className="context-warning">
      Older messages have been summarized to keep context short.
    </div>
  );
}
