import React, { useMemo, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import CompanyPage from './pages/CompanyPage';

export default function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });

  const isAuth = useMemo(() => Boolean(localStorage.getItem('token') && user), [user]);

  if (!isAuth) {
    return <LoginPage onLogin={setUser} />;
  }

  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/company/:id" element={<CompanyPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
