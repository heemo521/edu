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