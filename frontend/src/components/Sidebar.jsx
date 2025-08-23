import React from 'react';

const Sidebar = ({ section, setSection, threads, activeThread, setActiveThread }) => {
  return (
    <aside className="sidebar">
      <nav className="nav">
        <button
          className={section === 'threads' ? 'active' : ''}
          onClick={() => setSection('threads')}
        >
          Threads
        </button>
        <button
          className={section === 'goals' ? 'active' : ''}
          onClick={() => setSection('goals')}
        >
          Goals
        </button>
        <button
          className={section === 'materials' ? 'active' : ''}
          onClick={() => setSection('materials')}
        >
          Materials
        </button>
        <button
          className={section === 'plans' ? 'active' : ''}
          onClick={() => setSection('plans')}
        >
          Plans
        </button>
      </nav>
      {section === 'threads' && (
        <ul className="thread-list">
          {threads.map((t) => (
            <li
              key={t.id}
              className={activeThread === t.id ? 'thread active' : 'thread'}
              onClick={() => setActiveThread(t.id)}
            >
              {t.title}
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
};

export default Sidebar;
