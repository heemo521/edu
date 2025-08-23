import { useEffect, useState } from 'react';
import { fetchGoals } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';

export default function GoalCard() {
  const { userId } = useAppContext();
  const [goals, setGoals] = useState([]);

  useEffect(() => {
    if (!userId) return;
    fetchGoals(userId).then(setGoals).catch(console.error);
  }, [userId]);

  return (
    <div className="card">
      <h2>Goals</h2>
      {goals.length ? (
        <ul>
          {goals.map((g) => (
            <li key={g.id}>{g.description || g.title}</li>
          ))}
        </ul>
      ) : (
        <p>No goals yet.</p>
      )}
    </div>
  );
}
