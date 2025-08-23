import React, { useState } from 'react';

const subjects = {
  Math: ['Algebra', 'Geometry'],
  Science: ['Biology', 'Chemistry'],
};

const MaterialCard = () => {
  const [subject, setSubject] = useState('Math');
  const [category, setCategory] = useState(subjects['Math'][0]);

  const handleSubject = (s) => {
    setSubject(s);
    setCategory(subjects[s][0]);
  };

  return (
    <div className="card materials-card">
      <h2>Materials</h2>
      <div className="materials-select">
        <div className="subject-list">
          {Object.keys(subjects).map((s) => (
            <div
              key={s}
              className={subject === s ? 'item active' : 'item'}
              onClick={() => handleSubject(s)}
            >
              {s}
            </div>
          ))}
        </div>
        <div className="category-list">
          {subjects[subject].map((c) => (
            <div
              key={c}
              className={category === c ? 'item active' : 'item'}
              onClick={() => setCategory(c)}
            >
              {c}
            </div>
          ))}
        </div>
      </div>
      <p>Selected: {subject} / {category}</p>
    </div>
  );
};

export default MaterialCard;
