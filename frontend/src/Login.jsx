import { useState } from 'react';
import API from './api';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const res = await API.post('/login', { email, password });
      localStorage.setItem('token', res.data.access_token);
      onLogin();
    } catch (err) {
      alert('Invalid credentials');
    }
  };

  return (
    <div>
      <input
        placeholder='Email'
        onChange={(e) => setEmail(e.target.value)}
      />
      <br /><br />
      <input
        type='password'
        placeholder='Password'
        onChange={(e) => setPassword(e.target.value)}
      />
      <br /><br />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}