import { useState } from 'react';
import { register, login } from '../services/api.js';
import { useAppContext } from '../context/AppContext.jsx';

export default function AuthPage() {
  const { setUserId } = useAppContext();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    try {
      const fn = isLogin ? login : register;
      const data = await fn({ username, password });
      setUserId(data.userId);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-page">
      <h1>{isLogin ? 'Login' : 'Register'}</h1>
      <form onSubmit={submit}>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
        <button type="submit">Submit</button>
      </form>
      {error && <p className="error">{error}</p>}
      <button onClick={() => setIsLogin((v) => !v)}>
        {isLogin ? 'Need an account? Register' : 'Have an account? Login'}
      </button>
    </div>
  );
}
