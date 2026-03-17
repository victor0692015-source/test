import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { request } from '../services/api';
import CompanyBubble from '../components/CompanyBubble';
import QuickViewModal from '../components/QuickViewModal';

const statuses = ['all', 'new', 'negotiation', 'won', 'lost'];

export default function DashboardPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [form, setForm] = useState({ name: '', contactPerson: '', email: '', phone: '', dealStatus: 'new' });

  const loadCompanies = async () => {
    const query = new URLSearchParams({ search, status }).toString();
    const data = await request(`/companies?${query}`);
    setCompanies(data);
  };

  useEffect(() => {
    loadCompanies();
  }, [search, status]);

  const createCompany = async (e) => {
    e.preventDefault();
    await request('/companies', { method: 'POST', body: JSON.stringify(form) });
    setForm({ name: '', contactPerson: '', email: '', phone: '', dealStatus: 'new' });
    loadCompanies();
  };

  return (
    <div className="dashboard">
      <header className="toolbar card">
        <input placeholder="Поиск компании" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </header>

      <section className="watch-grid card">
        {companies.map((company, i) => (
          <CompanyBubble key={company.id} company={company} index={i} onClick={setSelected} />
        ))}
      </section>

      <form className="card create-form" onSubmit={createCompany}>
        <h3>Новая компания</h3>
        <input required placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input required placeholder="Контактное лицо" value={form.contactPerson} onChange={(e) => setForm({ ...form, contactPerson: e.target.value })} />
        <input required placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input required placeholder="Телефон" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <button className="primary-btn" type="submit">Создать</button>
      </form>

      <QuickViewModal company={selected} onClose={() => setSelected(null)} onOpen={(id) => navigate(`/company/${id}`)} />
    </div>
  );
}
