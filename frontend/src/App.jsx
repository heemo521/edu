import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Chat from './pages/Chat.jsx';
import { AppProvider, useAppContext } from './context/AppContext.jsx';
import styles from './App.module.css';

function AppRoutes() {
  const { userId } = useAppContext();
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route path="/dashboard" element={userId ? <Dashboard /> : <Navigate to="/login" />} />
      <Route path="/chat" element={userId ? <Chat /> : <Navigate to="/login" />} />
      <Route path="*" element={<Navigate to={userId ? '/dashboard' : '/login'} />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Router>
        <div className={styles.app}>
          <AppRoutes />
        </div>
      </Router>
    </AppProvider>
  );
}

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