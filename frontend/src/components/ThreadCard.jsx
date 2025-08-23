import React from 'react';

const ThreadCard = ({ activeThread }) => {
  return (
    <div className="card">
      <h2>{activeThread ? `Thread ${activeThread}` : 'Select a thread'}</h2>
      {activeThread && <p>Chat content goes here.</p>}
    </div>
  );
};

export default ThreadCard;
