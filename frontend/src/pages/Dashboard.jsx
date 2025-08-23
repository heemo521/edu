import { useEffect, useState } from 'react';
import { fetchDashboard, fetchGoals, fetchMaterials } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';
import ThreadsTabs from '../components/ThreadsTabs.jsx';
import StudyMaterials from '../components/StudyMaterials.jsx';

export default function Dashboard() {
  const { userId } = useAppContext();
  const [goals, setGoals] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!userId) return;
    fetchDashboard(userId).then(setSummary).catch(console.error);
    fetchGoals(userId).then(setGoals).catch(console.error);
  }, [userId]);

  return (
    <div className="dashboard">
      <ThreadsTabs />
      <h2>Study Goals</h2>
      <ul>{goals.map((g) => (<li key={g.id}>{g.title}</li>))}</ul>
      {summary && <p>Progress: {summary.progress}%</p>}
      <StudyMaterials />
    </div>
  );
}
