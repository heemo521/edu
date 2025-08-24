import { NavLink } from 'react-router-dom';
import { useAppContext } from '../context/AppContext.jsx';
import './PageTabs.css';

export default function PageTabs() {
  const { userId } = useAppContext();
  if (!userId) return null;

  return (
    <nav className="page-tabs">
      <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
      <NavLink to="/chat" className={({ isActive }) => isActive ? 'active' : ''}>Chat</NavLink>
    </nav>
  );
}
