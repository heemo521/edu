import React, { useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import ThreadCard from './components/ThreadCard.jsx';
import GoalCard from './components/GoalCard.jsx';
import MaterialCard from './components/MaterialCard.jsx';
import PlanCard from './components/PlanCard.jsx';

const App = () => {
  const [section, setSection] = useState('threads');
  const [activeThread, setActiveThread] = useState(null);
  const threads = [
    { id: 1, title: 'Session 1' },
    { id: 2, title: 'Session 2' },
    { id: 3, title: 'Session 3' },
  ];

  return (
    <div className="app-grid">
      <Sidebar
        section={section}
        setSection={setSection}
        threads={threads}
        activeThread={activeThread}
        setActiveThread={setActiveThread}
      />
      <main className="content-area">
        {section === 'threads' && <ThreadCard activeThread={activeThread} />}
        {section === 'goals' && <GoalCard />}
        {section === 'materials' && <MaterialCard />}
        {section === 'plans' && <PlanCard />}
      </main>
    </div>
  );
};

export default App;
