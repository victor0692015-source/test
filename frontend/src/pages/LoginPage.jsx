import React, { useState } from 'react';
import { request } from '../services/api';

export default function LoginPage({ onLogin }) {
  const [login, setLogin] = useState('admin');
  const [password, setPassword] = useState('admin');
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    try {
      const data = await request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ login, password })
      });
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="center-page">
      <form className="card login-card" onSubmit={submit}>
        <h1>Watch CRM</h1>
        <p>Вход в систему</p>
        <input value={login} onChange={(e) => setLogin(e.target.value)} placeholder="Логин" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Пароль" />
        {error && <span className="error">{error}</span>}
        <button className="primary-btn" type="submit">Войти</button>
      </form>
    </div>
  );
}
