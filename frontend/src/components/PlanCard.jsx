import { useEffect, useState } from 'react';
import { fetchPlans } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';

export default function PlanCard() {
  const { userId } = useAppContext();
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    if (!userId) return;
    fetchPlans(userId).then(setPlans).catch(console.error);
  }, [userId]);

  return (
    <div className="card">
      <h2>Plans</h2>
      {plans.length ? (
        <ul>
          {plans.map((p) => (
            <li key={p.id}>{p.recurrence || 'One-time'}{p.due_date ? ` - due ${p.due_date}` : ''}</li>
          ))}
        </ul>
      ) : (
        <p>No plans yet.</p>
      )}
    </div>
  );
}
