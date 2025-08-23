import { useEffect, useState } from 'react';
import { fetchHistory, sendChatMessage } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';

export default function Chat() {
  const { userId, currentThreadId, xp, setXp } = useAppContext();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (userId && currentThreadId) {
      fetchHistory(userId, currentThreadId).then(setMessages).catch(console.error);
    }
  }, [userId, currentThreadId]);

  const send = async () => {
    if (!input) return;
    const res = await sendChatMessage(userId, currentThreadId, input);
    setMessages((m) => [...m, { sender: 'user', text: input }, { sender: 'bot', text: res.reply }]);
    setInput('');
    setXp(xp + 1);
  };

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={m.sender}>{m.text}</div>
        ))}
      </div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={send}>Send</button>
    </div>
  );
}
