import { useEffect, useState } from 'react';
import { fetchHistory, sendChatMessage } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';
import ThreadsTabs from '../components/ThreadsTabs.jsx';
import ContextWarning from '../components/ContextWarning.jsx';

export default function Chat() {
  const { userId, currentThreadId, xp, setXp } = useAppContext();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (userId && currentThreadId) {
      fetchHistory(userId, currentThreadId)
        .then((history) => {
          // History items come back as pairs of user message and bot response.
          // Flatten them into the shape used by the chat UI.
          const formatted = history.flatMap((h) => [
            { sender: 'user', text: h.message },
            { sender: 'bot', text: h.response },
          ]);
          setMessages(formatted);
        })
        .catch(console.error);
    }
  }, [userId, currentThreadId]);

  const send = async () => {
    if (!input) return;
    const res = await sendChatMessage(userId, currentThreadId, input);
    // The backend returns the tutor reply under the `response` key. Fall back to
    // `reply` for backward compatibility in tests/mocks.
    const reply = res.response ?? res.reply ?? '';
    setMessages((m) => [...m, { sender: 'user', text: input }, { sender: 'bot', text: reply }]);
    setInput('');
    setXp(xp + 1);
  };

  return (
    <div className="chat">
      <ThreadsTabs />
      <ContextWarning />
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
