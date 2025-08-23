import { useEffect, useState } from 'react';
import { fetchMaterials, submitFeedback } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';
import Rating from './Rating.jsx';

export default function StudyMaterials() {
  const [subject, setSubject] = useState(() => localStorage.getItem('subject') || 'math');
  const [category, setCategory] = useState(() => localStorage.getItem('category') || '');
  const [materials, setMaterials] = useState([]);
  const { userId } = useAppContext();

  useEffect(() => {
    localStorage.setItem('subject', subject);
    localStorage.setItem('category', category);
    fetchMaterials(subject, category).then(setMaterials).catch(console.error);
  }, [subject, category]);

  return (
    <div className="materials">
      <h3>Study Materials</h3>
      <select value={subject} onChange={(e) => setSubject(e.target.value)}>
        <option value="math">Math</option>
        <option value="science">Science</option>
      </select>
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        <option value="">All</option>
        <option value="algebra">Algebra</option>
        <option value="geometry">Geometry</option>
      </select>
      <ul>
        {materials.map((m) => (
          <li key={m.id}>
            {m.title}
            <Rating onRate={(r) => submitFeedback({ user_id: userId, topic_id: m.id, rating: r, comments: '' })} />
          </li>
        ))}
      </ul>
    </div>
  );
}
