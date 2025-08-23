import { useEffect, useState } from 'react';
import { fetchDashboard } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';
import ThreadsTabs from '../components/ThreadsTabs.jsx';
import StudyMaterials from '../components/StudyMaterials.jsx';
import GoalCard from '../components/GoalCard.jsx';
import PlanCard from '../components/PlanCard.jsx';

export default function Dashboard() {
  const { userId } = useAppContext();
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    if (!userId) return;
    fetchDashboard(userId).then(setSummary).catch(console.error);
  }, [userId]);

  return (
    <div className="dashboard">
      <ThreadsTabs />
      {summary && <p>Progress: {summary.progress}%</p>}
      <GoalCard />
      <PlanCard />
      <StudyMaterials />
    </div>
  );
}
